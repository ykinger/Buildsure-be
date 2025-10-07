"""
DataMatrixOntarioChunk Model
Defines the pivot table for many-to-many relationship between DataMatrix and OntarioChunk.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class DataMatrixOntarioChunk(Base):

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    data_matrix_id = Column(
        String(36),
        ForeignKey("data_matrix.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    ontario_chunk_id = Column(
        String(36),
        ForeignKey("ontario_chunk.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<DataMatrixOntarioChunk(data_matrix_id={self.data_matrix_id}, ontario_chunk_id={self.ontario_chunk_id})>"
