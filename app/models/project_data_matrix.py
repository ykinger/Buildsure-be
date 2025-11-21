from typing import Optional, List
from datetime import datetime
from enum import Enum
from uuid import uuid4
from app.database import CustomBase
from sqlmodel import Field, Relationship
from sqlalchemy import Column, DateTime, func, JSON, String

class PDMStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class ProjectDataMatrix(CustomBase, table=True):
    __tablename__ = 'project_data_matrix'
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    project_id: str = Field(foreign_key="project.id")
    data_matrix_id: str = Field(foreign_key="data_matrix.id")
    status: PDMStatus = Field(default=PDMStatus.PENDING, sa_type=String)
    output: Optional[dict] = Field(sa_column=Column(JSON))
    created_at: Optional[datetime] = Field(
        sa_column=Column(DateTime, server_default=func.now(), nullable=False)
    )
    updated_at: Optional[datetime] = Field(
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    )

    project: Optional["Project"] = Relationship(back_populates="project_data_matrices")
    data_matrix: Optional["DataMatrix"] = Relationship(back_populates="project_data_matrices")
    messages: Optional[List["Message"]] = Relationship(back_populates="project_data_matrix")
