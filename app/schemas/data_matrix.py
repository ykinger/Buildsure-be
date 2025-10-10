"""
DataMatrix Schemas
Pydantic schemas for data matrix API serialization.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class DataMatrixBase(BaseModel):
    guide: str
    number: str
    alternate_number: Optional[str] = None
    title: str
    question: str


class DataMatrixCreate(DataMatrixBase):
    pass


class DataMatrixUpdate(BaseModel):
    guide: Optional[str] = None
    number: Optional[str] = None
    alternate_number: Optional[str] = None
    title: Optional[str] = None
    question: Optional[str] = None


class DataMatrix(DataMatrixBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class DataMatrixOntarioChunkBase(BaseModel):
    data_matrix_id: str
    ontario_chunk_id: str


class DataMatrixOntarioChunkCreate(DataMatrixOntarioChunkBase):
    pass


class DataMatrixOntarioChunk(DataMatrixOntarioChunkBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True
