from typing import Optional, Dict, Any
from datetime import datetime
from app.database import CustomBase
from sqlmodel import Field, Relationship
from sqlalchemy import Column, DateTime, func, JSON, Text
from enum import Enum

class SectionStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class Section(CustomBase, table=True):
    __tablename__ = 'section'
    id: Optional[str] = Field(default=None, primary_key=True)
    project_id: str = Field(foreign_key="project.id")
    form_section_number: str
    form_title: Optional[str] = Field(sa_column=Column(Text))
    status: SectionStatus = Field(default=SectionStatus.PENDING)
    draft_output: Optional[Dict[str, Any]] = Field(sa_column=Column(JSON))
    final_output: Optional[Dict[str, Any]] = Field(sa_column=Column(JSON))
    created_at: Optional[datetime] = Field(
        sa_column=Column(DateTime, server_default=func.now(), nullable=False)
    )
    updated_at: Optional[datetime] = Field(
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    )

    project: Optional["Project"] = Relationship(back_populates="sections")
from enum import Enum

class SectionStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class Section(CustomBase, table=True):
    __tablename__ = 'section'
    id: Optional[str] = Field(default=None, primary_key=True)
    project_id: str = Field(foreign_key="project.id")
    form_section_number: str
    form_title: Optional[str] = Field(sa_column=Column(Text))
    status: SectionStatus = Field(default=SectionStatus.PENDING)
    draft_output: Optional[Dict[str, Any]] = Field(sa_column=Column(JSON))
    final_output: Optional[Dict[str, Any]] = Field(sa_column=Column(JSON))
    created_at: Optional[datetime] = Field(
        sa_column=Column(DateTime, server_default=func.now(), nullable=False)
    )
    updated_at: Optional[datetime] = Field(
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    )
