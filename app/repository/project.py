from typing import List, Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Session, select
from sqlalchemy.orm import joinedload
from app.database import get_db
from app.models.project import Project
from app.models.project_data_matrix import PDMStatus, ProjectDataMatrix
from app.schemas.project import ProjectDetailsResponse
from app.schemas.section import SectionResponse


def _create_project_details_response(project: Project) -> ProjectDetailsResponse:
    """Helper function to create a ProjectDetailsResponse from a Project object."""
    total_sections = len(project.project_data_matrices)
    completed_sections = sum(1 for pdm in project.project_data_matrices if pdm.status == PDMStatus.COMPLETED)

    # Convert ProjectDataMatrix objects to SectionResponse objects
    sections_response = [
        SectionResponse(
            id=str(pdm.id),
            project_id=str(pdm.project_id),
            form_section_number=pdm.data_matrix.number if pdm.data_matrix else "",
            status=pdm.status,
            final_output=pdm.output,
            created_at=pdm.created_at,
            updated_at=pdm.updated_at
        ) for pdm in project.project_data_matrices
    ]

    return ProjectDetailsResponse(
        id=str(project.id),
        organization_id=str(project.organization_id),
        user_id=str(project.user_id),
        name=project.name,
        description=project.description,
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at,
        due_date=project.due_date,
        total_sections=total_sections,
        completed_sections=completed_sections,
        sections=sections_response
    )


async def create_project(project: Project, session: AsyncSession = Depends(get_db)) -> Project:
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project

async def get_project_by_id(project_id: str, session: AsyncSession = Depends(get_db)) -> Project:
    statement = select(Project).options(
        joinedload(Project.project_data_matrices).joinedload(ProjectDataMatrix.data_matrix)
    ).where(Project.id == project_id)
    result = await session.execute(statement)
    project = result.unique().scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    return project

async def get_project_details_by_id(project_id: str, session: AsyncSession = Depends(get_db)) -> ProjectDetailsResponse:
    project = await get_project_by_id(project_id, session)
    return _create_project_details_response(project)


async def list_projects(session: AsyncSession = Depends(get_db), organization_id: Optional[str] = None, user_id: Optional[str] = None, offset: int = 0, limit: int = 100) -> List[ProjectDetailsResponse]:
    statement = select(Project).options(joinedload(Project.project_data_matrices).joinedload(ProjectDataMatrix.data_matrix))
    if organization_id:
        statement = statement.where(Project.organization_id == organization_id)
    if user_id:
        statement = statement.where(Project.user_id == user_id)
    statement = statement.offset(offset).limit(limit)
    result = await session.execute(statement)
    projects_from_db = list(result.scalars().unique().all())

    return [_create_project_details_response(project) for project in projects_from_db]

async def update_project(project_id: str, project_data: dict, session: AsyncSession = Depends(get_db)) -> Optional[Project]:
    project = await get_project_by_id(project_id, session)
    if project:
        for key, value in project_data.items():
            setattr(project, key, value)
        session.add(project)
        await session.commit()
        await session.refresh(project)
        return project
    return None

async def delete_project(project_id: str, session: AsyncSession = Depends(get_db)) -> bool:
    project = await get_project_by_id(project_id, session)
    if project:
        await session.delete(project)
        await session.commit()
        return True
    return False