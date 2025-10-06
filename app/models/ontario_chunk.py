"""
OntarioChunk Model
Defines the database model for storing Ontario Building Code chunks.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, func
from app.database import Base


class OntarioChunk(Base):

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    reference = Column(
        String(30),
        nullable=False,
        index=True
    )
    division = Column(
        String(50),
        nullable=True,
        index=True
    )
    part = Column(
        String(10),
        nullable=True,
        index=True
    )
    section = Column(
        String(10),
        nullable=True,
        index=True
    )
    subsection = Column(
        String(10),
        nullable=True,
        index=True
    )
    article = Column(
        String(10),
        nullable=True,
        index=True
    )
    chunk_type = Column(
        String(20),
        nullable=False,
        index=True
    )
    title = Column(
        String(200),
        nullable=True
    )
    content = Column(
        Text,
        nullable=False
    )
    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<OntarioChunk(id={self.id}, reference='{self.reference}', type='{self.chunk_type}', content='{self.content[:50]}...')>"
