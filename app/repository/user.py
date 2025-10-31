
from typing import List, Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Session, select
from app.database import get_db
from app.models.user import User

async def create_user(user: User, session: AsyncSession = Depends(get_db)) -> User:
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def get_user_by_id(user_id: str, session: AsyncSession = Depends(get_db)) -> User:
    statement = select(User).where(User.id == user_id)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

async def get_user_by_email(email: str, session: AsyncSession = Depends(get_db)) -> Optional[User]:
    statement = select(User).where(User.email == email)
    result = await session.execute(statement)
    return result.scalar_one_or_none()

async def list_users(session: AsyncSession = Depends(get_db), offset: int = 0, limit: int = 100) -> List[User]:
    statement = select(User).offset(offset).limit(limit)
    result = await session.execute(statement)
    return list(result.scalars().all())

async def update_user(user_id: str, user_data: dict, session: AsyncSession = Depends(get_db)) -> Optional[User]:
    user = await get_user_by_id(user_id, session)
    if user:
        for key, value in user_data.items():
            setattr(user, key, value)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
    return None

async def delete_user(user_id: str, session: AsyncSession = Depends(get_db)) -> bool:
    user = await get_user_by_id(user_id, session)
    if user:
        await session.delete(user)
        await session.commit()
        return True
    return False
