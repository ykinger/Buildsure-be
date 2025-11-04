from typing import Optional
from app.database import CustomBase
from sqlmodel import Field, Relationship
from sqlalchemy import Column, Text
from typing import List

class KnowledgeBase(CustomBase, table=True):
    __tablename__ = 'knowledge_base'
    id: Optional[str] = Field(default=None, primary_key=True)
    source: str
    reference: str
    alternate_reference: Optional[str]
    content: str = Field(sa_column=Column(Text))

    data_matrix_knowledge_bases: List["DataMatrixKnowledgeBase"] = Relationship(back_populates="knowledge_base")
