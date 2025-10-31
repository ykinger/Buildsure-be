
from typing import List, Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Session, select
from app.database import get_db
from app.models.section import Section

async def create_section(section: Section, session: AsyncSession = Depends(get_db)) -> Section:
    session.add(section)
    await session.commit()
    await session.refresh(section)
    return section

async def get_section_by_id(section_id: str, session: AsyncSession = Depends(get_db)) -> Section:
    statement = select(Section).where(Section.id == section_id)
    result = await session.execute(statement)
    section = result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")
    return section

async def list_sections(session: AsyncSession = Depends(get_db), project_id: Optional[str] = None, offset: int = 0, limit: int = 100) -> List[Section]:
    statement = select(Section)
    if project_id:
        statement = statement.where(Section.project_id == project_id)
    statement = statement.offset(offset).limit(limit)
    result = await session.execute(statement)
    return list(result.scalars().all())

async def update_section(section_id: str, section_data: dict, session: AsyncSession = Depends(get_db)) -> Optional[Section]:
    section = await get_section_by_id(section_id, session)
    if section:
        for key, value in section_data.items():
            setattr(section, key, value)
        session.add(section)
        await session.commit()
        await session.refresh(section)
        return section
    return None

async def delete_section(section_id: str, session: AsyncSession = Depends(get_db)) -> bool:
    section = await get_section_by_id(section_id, session)
    if section:
        await session.delete(section)
        await session.commit()
        return True
    return False
