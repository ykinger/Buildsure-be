"""
Form Section Template Model
Defines the database model for form section templates.
"""
from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import Column, String, Text, DateTime, func, JSON
from sqlalchemy.orm import relationship, Mapped
from app.database import Base

if TYPE_CHECKING:
    from .section import Section


class FormSectionTemplate(Base):
    __tablename__ = "form_section_template"

    question_number = Column(
        String(10),
        primary_key=True,
        nullable=False
    )
    form_title = Column(String(255), nullable=False)
    question_to_answer = Column(Text, nullable=True)
    obc_reference = Column(JSON, nullable=True)
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
    sections: Mapped[List["Section"]] = relationship(
        "Section",
        back_populates="form_template"
    )

    def __repr__(self) -> str:
        return f"<FormSectionTemplate(question_number='{self.question_number}', form_title='{self.form_title}')>"
