
from typing import List, Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Session, select
from app.database import get_db
from app.models.data_matrix import DataMatrix

async def create_data_matrix(data_matrix: DataMatrix, session: AsyncSession = Depends(get_db)) -> DataMatrix:
    session.add(data_matrix)
    await session.commit()
    await session.refresh(data_matrix)
    return data_matrix

async def get_data_matrix_by_id(data_matrix_id: str, session: AsyncSession = Depends(get_db)) -> DataMatrix:
    statement = select(DataMatrix).where(DataMatrix.id == data_matrix_id)
    result = await session.execute(statement)
    data_matrix = result.scalar_one_or_none()
    if not data_matrix:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data Matrix entry not found")
    return data_matrix

async def list_data_matrices(session: AsyncSession = Depends(get_db), offset: int = 0, limit: int = 100) -> List[DataMatrix]:
    statement = select(DataMatrix).offset(offset).limit(limit)
    result = await session.execute(statement)
    return list(result.scalars().all())

async def update_data_matrix(data_matrix_id: str, data_matrix_data: dict, session: AsyncSession = Depends(get_db)) -> Optional[DataMatrix]:
    data_matrix = await get_data_matrix_by_id(data_matrix_id, session)
    if data_matrix:
        for key, value in data_matrix_data.items():
            setattr(data_matrix, key, value)
        session.add(data_matrix)
        await session.commit()
        await session.refresh(data_matrix)
        return data_matrix
    return None

async def delete_data_matrix(data_matrix_id: str, session: AsyncSession = Depends(get_db)) -> bool:
    data_matrix = await get_data_matrix_by_id(data_matrix_id, session)
    if data_matrix:
        await session.delete(data_matrix)
        await session.commit()
        return True
    return False
