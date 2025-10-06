from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class Conversation(SQLModel, table=True):
    id: str = Field(primary_key=True, nullable=False)
    history: str = Field(index=False)
