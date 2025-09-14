"""
User Model
Defines the database model for users.
"""
import uuid
from datetime import datetime
from typing import List, TYPE_CHECKING, Optional
from sqlalchemy import Column, String, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship, Mapped
from app.database import Base

if TYPE_CHECKING:
    from .organization import Organization
    from .project import Project


class User(Base):
    __tablename__ = "users"

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
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
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
        back_populates="users"
    )
    projects: Mapped[List["Project"]] = relationship(
        "Project", 
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}')>"
