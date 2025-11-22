
from typing import List, Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Session, select
from app.database import get_db
from app.models.message import Message

async def create_message(message: Message, session: AsyncSession = Depends(get_db)) -> Message:
    session.add(message)
    await session.commit()
    await session.refresh(message)
    return message

async def get_message_by_id(message_id: str, session: AsyncSession = Depends(get_db)) -> Message:
    statement = select(Message).where(Message.id == message_id)
    result = await session.execute(statement)
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    return message

async def list_messages(session: AsyncSession = Depends(get_db), offset: int = 0, limit: int = 100) -> List[Message]:
    statement = select(Message).offset(offset).limit(limit)
    result = await session.execute(statement)
    return list(result.scalars().all())

async def update_message(message_id: str, message_data: dict, session: AsyncSession = Depends(get_db)) -> Optional[Message]:
    message = await get_message_by_id(message_id, session)
    if message:
        for key, value in message_data.items():
            setattr(message, key, value)
        session.add(message)
        await session.commit()
        await session.refresh(message)
        return message
    return None

async def delete_messages(messages: List[Message], session: AsyncSession):
    if not messages:
        return

    message_ids = [message.id for message in messages]
    print ("Deleting", message_ids)

    from sqlalchemy import delete as sqlalchemy_delete
    statement = sqlalchemy_delete(Message).where(Message.id.in_(message_ids))

    await session.execute(statement)
    await session.commit()
