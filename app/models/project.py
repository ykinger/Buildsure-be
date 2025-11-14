from typing import Optional, List
from datetime import datetime
from uuid import uuid4
from app.database import CustomBase
from sqlmodel import Field, Relationship
from sqlalchemy import Column, DateTime, func, Text, Integer
from enum import Enum

class ProjectStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class Project(CustomBase, table=True):
    __tablename__ = 'project'
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    organization_id: str = Field(foreign_key="organization.id")
    user_id: str = Field(foreign_key="user.id")
    name: str
    description: Optional[str] = Field(sa_column=Column(Text))
    status: str = Field(default=ProjectStatus.NOT_STARTED)

    created_at: Optional[datetime] = Field(
        sa_column=Column(DateTime, server_default=func.now(), nullable=False)
    )
    updated_at: Optional[datetime] = Field(
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    )
    due_date: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))
    # total_sections: int = Field(default=0, sa_column=Column(Integer, default=0, nullable=False))
    # completed_sections: int = Field(default=0, sa_column=Column(Integer, default=0, nullable=False))

    organization: Optional["Organization"] = Relationship(back_populates="projects")
    user: Optional["User"] = Relationship(back_populates="projects")
    project_data_matrices: List["ProjectDataMatrix"] = Relationship(back_populates="project")
    sections: List["Section"] = Relationship(back_populates="project")
