from typing import Optional
from datetime import datetime
from app.database import CustomBase
from sqlmodel import Field, Relationship
from sqlalchemy import Column, DateTime, func, Text
from typing import List

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

    project_data_matrices: List["ProjectDataMatrix"] = Relationship(back_populates="data_matrix")
    data_matrix_knowledge_bases: List["DataMatrixKnowledgeBase"] = Relationship(back_populates="data_matrix")
