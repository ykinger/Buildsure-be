"""
DataMatrix Model
Defines the database model for storing data matrix questions.
"""
import uuid
from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import Column, String, Text, DateTime, func
from sqlalchemy.orm import relationship, Mapped
from app.database import Base

if TYPE_CHECKING:
    from .ontario_chunk import OntarioChunk
    from .section import Section


class DataMatrix(Base):
    __tablename__ = "data_matrix"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    guide = Column(
        Text,
        nullable=False
    )
    number = Column(
        String(10),
        nullable=False,
        index=True
    )
    alternate_number = Column(
        String(10),
        nullable=True,
        index=True
    )
    title = Column(
        String(200),
        nullable=False
    )
    question = Column(
        Text,
        nullable=False
    )
    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    ontario_chunks: Mapped[List["OntarioChunk"]] = relationship(
        "OntarioChunk",
        secondary="data_matrix_ontario_chunk",
        back_populates="data_matrices"
    )
    sections: Mapped[List["Section"]] = relationship(
        "Section",
        back_populates="data_matrix"
    )

    def __repr__(self) -> str:
        return f"<DataMatrix(id={self.id}, number='{self.number}', title='{self.title}')>"
