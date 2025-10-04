from typing import Optional
from uuid import UUID

from sqlmodel import Field, SQLModel


class ConversationBase(SQLModel):
    history: str = Field(index=False)


class ConversationCreate(ConversationBase):
    pass


class ConversationRead(ConversationBase):
    id: UUID
