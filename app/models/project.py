"""
Project Model
Defines the database model for projects.
"""
import uuid
from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import Column, String, Text, DateTime, func, ForeignKey, Integer, Enum
from sqlalchemy.orm import relationship, Mapped
from app.database import Base
import enum

if TYPE_CHECKING:
    from .organization import Organization
    from .user import User
    from .section import Section


class ProjectStatus(enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"


class Project(Base):
    __tablename__ = "projects"

    id = Column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    org_id = Column(
        String(36), 
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id = Column(
        String(36), 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(
        Enum(ProjectStatus), 
        nullable=False, 
        default=ProjectStatus.NOT_STARTED
    )
    current_section = Column(String, nullable=False, default="3.01")
    total_sections = Column(Integer, nullable=False, default=0)
    completed_sections = Column(Integer, nullable=False, default=0)
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
    organization: Mapped["Organization"] = relationship(
        "Organization", 
        back_populates="projects"
    )
    user: Mapped["User"] = relationship(
        "User", 
        back_populates="projects"
    )
    sections: Mapped[List["Section"]] = relationship(
        "Section", 
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="Section.form_section_number"
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}', status='{self.status.value}')>"
