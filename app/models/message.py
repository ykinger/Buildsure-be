from typing import Optional
from datetime import datetime
from app.database import CustomBase
from sqlmodel import Field, Relationship
from sqlalchemy import Column, DateTime, func, Text

class Message(CustomBase, table=True):
    __tablename__ = 'message'
    id: Optional[str] = Field(default=None, primary_key=True)
    project_data_matrix_id: str = Field(foreign_key="project_data_matrix.id")
    user_id: Optional[str] = Field(foreign_key="user.id")
    role: str
    content: str = Field(sa_column=Column(Text))
    created_at: Optional[datetime] = Field(
        sa_column=Column(DateTime, server_default=func.now(), nullable=False)
    )

    project_data_matrix: Optional["ProjectDataMatrix"] = Relationship(back_populates="messages")
    # user: Optional["User"] = Relationship(back_populates="messages")
