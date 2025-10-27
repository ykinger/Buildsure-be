from typing import Optional
from datetime import datetime
from app.database import CustomBase
from sqlmodel import Field, Relationship
from sqlalchemy import Column, DateTime, func, Text

class DataMatrix(CustomBase, table=True):
    __tablename__ = 'data_matrix'
    id: Optional[str] = Field(default=None, primary_key=True)
    number: str
    alternate_number: Optional[str]
    title: str
    guide: str = Field(sa_column=Column(Text))
    question: str = Field(sa_column=Column(Text))
    created_at: Optional[datetime] = Field(
        sa_column=Column(DateTime, server_default=func.now(), nullable=False)
    )
