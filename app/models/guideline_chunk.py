"""
GuidelineChunk Model
Defines the database model for storing Ontario Building Code chunks.
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Text, DateTime, func, JSON, Integer
from app.database import Base


class GuidelineChunk(Base):
    __tablename__ = "guideline_chunks"

    id = Column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    section_reference = Column(
        String(20), 
        nullable=False,
        index=True
    )
    section_title = Column(
        String(500),
        nullable=True
    )
    section_level = Column(
        Integer,
        nullable=False,
        default=1
    )
    chunk_text = Column(
        Text, 
        nullable=False
    )
    embedding = Column(
        JSON, 
        nullable=True
    )
    created_at = Column(
        DateTime, 
        server_default=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<GuidelineChunk(id={self.id}, section_reference='{self.section_reference}', section_title='{self.section_title[:50]}...')>"
