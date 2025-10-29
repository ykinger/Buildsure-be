"""
Sections Router
FastAPI router for section CRUD operations.
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
import math
import json

from pydantic import BaseModel
from sqlmodel import SQLModel

from app.database import get_db
from app.models.project import Project
from app.schemas.section import (
    SectionCreate,
    SectionUpdate,
    SectionResponse,
    SectionListResponse,
    SectionStartResponse,
    SectionConfirmResponse,
    SectionConfirmRequest,
    SectionConfirmSimpleResponse
)
from app.schemas.answer import AnswerCreate, SectionAnswerResponse
from app.services.section_service import SectionService
from app.services.ai_service import AIService

import logging

class RequestAnswer(BaseModel):
    answer: str

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

router = APIRouter(prefix="/api/v1/sections", tags=["sections"])


@router.get("/{section_id}/clear")
async def clear_section_history(section_id: str, db: AsyncSession = Depends(get_db)):
    """Clear chat history (answers) for a section"""
    raise HTTPException(status_code=501, detail="Section functionality is currently disabled.")


@router.post("/{section_id}/next")
async def start_section(
    section_id: str,
    answer: Optional[RequestAnswer] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Start a section conversation or continue with an answer.
    """
    raise HTTPException(status_code=501, detail="Section functionality is currently disabled.")


@router.post("/{section_id}/start")
async def start_section(
    section_id: str,
    answer: Optional[RequestAnswer] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Start a section and changes the state to In progress
    """
    raise HTTPException(status_code=501, detail="Section functionality is currently disabled.")


@router.post("/{section_id}/confirm", response_model=SectionConfirmSimpleResponse)
async def confirm_section_simple(
    section_id: str,
    confirm_data: SectionConfirmRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Confirm a section by saving answer and progressing to next section.
    """
    raise HTTPException(status_code=501, detail="Section functionality is currently disabled.")
