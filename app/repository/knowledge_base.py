
from typing import List, Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Session, select
from app.database import get_db
from app.models.knowledge_base import KnowledgeBase

async def create_knowledge_base(knowledge_base: KnowledgeBase, session: AsyncSession = Depends(get_db)) -> KnowledgeBase:
    session.add(knowledge_base)
    await session.commit()
    await session.refresh(knowledge_base)
    return knowledge_base

async def get_knowledge_base_by_id(kb_id: str, session: AsyncSession = Depends(get_db)) -> KnowledgeBase:
    statement = select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
    result = await session.execute(statement)
    knowledge_base = result.scalar_one_or_none()
    if not knowledge_base:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge Base entry not found")
    return knowledge_base

async def list_knowledge_bases(session: AsyncSession = Depends(get_db), offset: int = 0, limit: int = 100) -> List[KnowledgeBase]:
    statement = select(KnowledgeBase).offset(offset).limit(limit)
    result = await session.execute(statement)
    return list(result.scalars().all())

async def update_knowledge_base(kb_id: str, knowledge_base_data: dict, session: AsyncSession = Depends(get_db)) -> Optional[KnowledgeBase]:
    knowledge_base = await get_knowledge_base_by_id(kb_id, session)
    if knowledge_base:
        for key, value in knowledge_base_data.items():
            setattr(knowledge_base, key, value)
        session.add(knowledge_base)
        await session.commit()
        await session.refresh(knowledge_base)
        return knowledge_base
    return None

async def delete_knowledge_base(kb_id: str, session: AsyncSession = Depends(get_db)) -> bool:
    knowledge_base = await get_knowledge_base_by_id(kb_id, session)
    if knowledge_base:
        await session.delete(knowledge_base)
        await session.commit()
        return True
    return False
