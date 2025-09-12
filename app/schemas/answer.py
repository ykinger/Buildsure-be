"""
Answer Pydantic Schemas
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class AnswerBase(BaseModel):
    """Base answer schema with common fields"""
    question_text: str
    answer_text: str
    question_type: str = "clarifying"


class AnswerCreate(BaseModel):
    """Schema for creating an answer (request body)"""
    question_text: str
    answer_text: str


class AnswerResponse(AnswerBase):
    """Schema for answer response"""
    id: str
    section_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SectionAnswerResponse(BaseModel):
    """Schema for section answer submission response"""
    section_id: str
    section_number: int
    status: str
    next_question: Optional[str] = None
    draft_output: Optional[Dict[str, Any]] = None
    message: str
    answers_count: int

    model_config = ConfigDict(from_attributes=True)
