from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class Conversation(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)
    history: str = Field(index=False)
