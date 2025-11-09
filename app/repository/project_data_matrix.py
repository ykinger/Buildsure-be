
from typing import List, Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select
from app.database import get_db
from app.models.project_data_matrix import ProjectDataMatrix
from app.models.data_matrix import DataMatrix

async def create_project_data_matrix(project_data_matrix: ProjectDataMatrix, session: AsyncSession = Depends(get_db)) -> ProjectDataMatrix:
    session.add(project_data_matrix)
    await session.commit()
    await session.refresh(project_data_matrix)
    return project_data_matrix

async def get_project_data_matrix_by_id(id: str, session: AsyncSession = Depends(get_db)) -> ProjectDataMatrix:
    statement = select(ProjectDataMatrix).where(ProjectDataMatrix.id == id).options(
        selectinload(ProjectDataMatrix.messages),
        selectinload(ProjectDataMatrix.data_matrix).selectinload(DataMatrix.knowledge_bases),
        )
    result = await session.execute(statement)
    project_data_matrix = result.scalar_one_or_none()
    if not project_data_matrix:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project Data Matrix entry not found")
    return project_data_matrix

async def list_project_data_matrices(session: AsyncSession = Depends(get_db), offset: int = 0, limit: int = 100) -> List[ProjectDataMatrix]:
    statement = select(ProjectDataMatrix).options(selectinload(ProjectDataMatrix.messages)).offset(offset).limit(limit)
    result = await session.execute(statement)
    return list(result.scalars().all())

async def update_project_data_matrix(pdm_id: str, project_data_matrix_data: dict, session: AsyncSession = Depends(get_db)) -> Optional[ProjectDataMatrix]:
    project_data_matrix = await get_project_data_matrix_by_id(pdm_id, session)
    if project_data_matrix:
        for key, value in project_data_matrix_data.items():
            setattr(project_data_matrix, key, value)
        session.add(project_data_matrix)
        await session.commit()
        await session.refresh(project_data_matrix)
        return project_data_matrix
    return None

async def delete_project_data_matrix(pdm_id: str, session: AsyncSession = Depends(get_db)) -> bool:
    project_data_matrix = await get_project_data_matrix_by_id(pdm_id, session)
    if project_data_matrix:
        await session.delete(project_data_matrix)
        await session.commit()
        return True
    return False
