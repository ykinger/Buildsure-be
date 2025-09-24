"""
Section Model
Defines the database model for sections.
"""
import uuid
from datetime import datetime
from typing import Dict, Any, TYPE_CHECKING, List
from sqlalchemy import Column, String, DateTime, func, ForeignKey, Integer, Enum, JSON
from sqlalchemy.orm import relationship, Mapped
from app.database import Base
import enum

if TYPE_CHECKING:
    from .project import Project
    from .answer import Answer


class SectionStatus(enum.Enum):
    PENDING = "pending"
    READY_TO_START = "ready_to_start"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Section(Base):
    __tablename__ = "sections"

    id = Column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    project_id = Column(
        String(36), 
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    section_number = Column(Integer, nullable=False)
    status = Column(
        Enum(SectionStatus), 
        nullable=False, 
        default=SectionStatus.PENDING
    )
    draft_output = Column(JSON, nullable=True)
    final_output = Column(JSON, nullable=True)
    created_at = Column(
        DateTime, 
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime, 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project", 
        back_populates="sections"
    )
    answers: Mapped[List["Answer"]] = relationship(
        "Answer",
        back_populates="section",
        cascade="all, delete-orphan",
        order_by="Answer.created_at"
    )

    def __repr__(self) -> str:
        return f"<Section(id={self.id}, project_id={self.project_id}, section_number={self.section_number}, status='{self.status.value}')>"
