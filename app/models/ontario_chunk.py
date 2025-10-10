"""
OntarioChunk Model
Defines the database model for storing Ontario Building Code chunks.
"""
import uuid
from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import Column, String, Text, DateTime, func
from sqlalchemy.orm import relationship, Mapped
from app.database import Base

if TYPE_CHECKING:
    from .data_matrix import DataMatrix


class OntarioChunk(Base):
    __tablename__ = "ontario_chunk"

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

    # Relationships
    data_matrices: Mapped[List["DataMatrix"]] = relationship(
        "DataMatrix",
        secondary="data_matrix_ontario_chunk",
        back_populates="ontario_chunks"
    )

    def __repr__(self) -> str:
        return f"<OntarioChunk(id={self.id}, reference='{self.reference}', type='{self.chunk_type}', content='{self.content[:50]}...')>"
