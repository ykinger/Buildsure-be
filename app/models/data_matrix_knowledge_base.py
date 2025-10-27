from typing import Optional
from app.database import CustomBase
from sqlmodel import Field

class DataMatrixKnowledgeBase(CustomBase, table=True):
    __tablename__ = 'data_matrix_knowledge_base'
    id: Optional[str] = Field(default=None, primary_key=True)
    data_matrix_id: str = Field(foreign_key="data_matrix.id")
    knowledge_base_id: str = Field(foreign_key="knowledge_base.id")
