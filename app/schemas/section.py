"""
Section Pydantic Schemas
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from app.models.section import SectionStatus


class SectionBase(BaseModel):
    """Base section schema with common fields"""
    form_section_number: str
    status: SectionStatus = SectionStatus.PENDING
    draft_output: Optional[Dict[str, Any]] = None
    final_output: Optional[Dict[str, Any]] = None


class SectionCreate(SectionBase):
    """Schema for creating a section"""
    project_id: str


class SectionUpdate(BaseModel):
    """Schema for updating a section"""
    form_section_number: Optional[str] = None
    status: Optional[SectionStatus] = None
    draft_output: Optional[Dict[str, Any]] = None
    final_output: Optional[Dict[str, Any]] = None
    project_id: Optional[str] = None


class SectionResponse(SectionBase):
    """Schema for section response"""
    id: str
    project_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SectionListResponse(BaseModel):
    """Schema for paginated section list response"""
    items: List[SectionResponse]
    total: int
    page: int
    size: int
    pages: int

    model_config = ConfigDict(from_attributes=True)


class SectionStartResponse(BaseModel):
    """Schema for section start response with generated question"""
    section_id: str
    form_section_number: str
    status: SectionStatus
    question: str
    question_type: str = "initial"

    model_config = ConfigDict(from_attributes=True)


class SectionConfirmResponse(BaseModel):
    """Schema for section confirmation response"""
    section_id: str
    form_section_number: str
    status: SectionStatus
    final_output: Optional[Dict[str, Any]] = None
    project_id: str
    project_status: str
    completed_sections: int
    total_sections: int
    current_section: str
    message: str

    model_config = ConfigDict(from_attributes=True)


class SectionConfirmRequest(BaseModel):
    """Schema for section confirmation request with answer"""
    answer: str


class SectionConfirmSimpleResponse(BaseModel):
    """Schema for simple section confirmation response"""
    section_id: str
    next_section_id: str
    message: str
    status: str

    model_config = ConfigDict(from_attributes=True)
