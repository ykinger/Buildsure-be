"""
Answer Model
Defines the database model for storing question-answer pairs for sections.
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Column, String, DateTime, func, ForeignKey, Text
from sqlalchemy.orm import relationship, Mapped
from app.database import Base

if TYPE_CHECKING:
    from .section import Section


class Answer(Base):
    __tablename__ = "answers"

    id = Column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    section_id = Column(
        String(36), 
        ForeignKey("sections.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    question_text = Column(Text, nullable=False)
    answer_text = Column(Text, nullable=False)
    question_type = Column(
        String(50), 
        nullable=False, 
        default="clarifying"
    )  # "initial", "clarifying", "followup"
    created_at = Column(
        DateTime, 
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    section: Mapped["Section"] = relationship(
        "Section", 
        back_populates="answers"
    )

    def __repr__(self) -> str:
        return f"<Answer(id={self.id}, section_id={self.section_id}, question_type='{self.question_type}')>"
