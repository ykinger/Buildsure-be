
from typing import List, Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Session, select
from app.database import get_db
from app.models.project import Project

async def create_project(project: Project, session: AsyncSession = Depends(get_db)) -> Project:
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project

async def get_project_by_id(project_id: str, session: AsyncSession = Depends(get_db)) -> Project:
    statement = select(Project).where(Project.id == project_id)
    result = await session.execute(statement)
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project

async def list_projects(session: AsyncSession = Depends(get_db), organization_id: Optional[str] = None, user_id: Optional[str] = None, offset: int = 0, limit: int = 100) -> List[Project]:
    statement = select(Project)
    if organization_id:
        statement = statement.where(Project.organization_id == organization_id)
    if user_id:
        statement = statement.where(Project.user_id == user_id)
    statement = statement.offset(offset).limit(limit)
    result = await session.execute(statement)
    return list(result.scalars().all())

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
