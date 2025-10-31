from typing import Optional
from datetime import datetime
from app.database import CustomBase
from sqlmodel import Field, Relationship
from sqlalchemy import Column, DateTime, func, JSON

class ProjectDataMatrix(CustomBase, table=True):
    __tablename__ = 'project_data_matrix'
    id: Optional[str] = Field(default=None, primary_key=True)
    project_id: str = Field(foreign_key="project.id")
    data_matrix_id: str = Field(foreign_key="data_matrix.id")
    status: str
    output: Optional[dict] = Field(sa_column=Column(JSON))
    created_at: Optional[datetime] = Field(
        sa_column=Column(DateTime, server_default=func.now(), nullable=False)
    )
    updated_at: Optional[datetime] = Field(
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    )

    project: Optional["Project"] = Relationship(back_populates="project_data_matrices")
    data_matrix: Optional["DataMatrix"] = Relationship(back_populates="project_data_matrices")

class ProjectDataMatrix(CustomBase, table=True):
    __tablename__ = 'project_data_matrix'
    id: Optional[str] = Field(default=None, primary_key=True)
    project_id: str = Field(foreign_key="project.id")
    data_matrix_id: str = Field(foreign_key="data_matrix.id")
    status: str
    output: Optional[dict] = Field(sa_column=Column(JSON))
    created_at: Optional[datetime] = Field(
        sa_column=Column(DateTime, server_default=func.now(), nullable=False)
    )
    updated_at: Optional[datetime] = Field(
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    )
