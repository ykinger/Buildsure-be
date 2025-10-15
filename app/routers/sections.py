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

from app.database import get_async_db
from app.models.section import Section, SectionStatus
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
async def clear_section_history(section_id: str, db: AsyncSession = Depends(get_async_db)):
    """Clear chat history (answers) for a section"""
    # Get section and use section_id for history clearing
    select_stmt = select(Section).where(Section.id == section_id)
    result = await db.execute(select_stmt)
    section = result.scalar_one_or_none()

    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    ai_service = AIService(db)
    await ai_service.clear_chat_history(section.id)
    response = await ai_service.what_to_pass_to_user(section.form_section_number)
    return response


@router.post("/{section_id}/next")
async def start_section(
    section_id: str,
    answer: Optional[RequestAnswer] = None,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Start a section conversation or continue with an answer.

    This endpoint replaces the POC functionality and:
    1. Gets the section and extracts form_section_number
    2. Uses AIService.what_to_pass_to_user method for conversational flow
    3. Handles both initial calls (no answer) and follow-up calls (with answer)
    4. Returns structured AI responses for questions or final answers
    """
    # Get section and extract form_section_number (like POC does)
    select_stmt = select(Section).where(Section.id == section_id)
    result = await db.execute(select_stmt)
    section = result.scalar_one_or_none()

    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    section_number = section.form_section_number
    ai_service = AIService(db)

    # Handle the answer parameter properly
    human_answer = answer.answer if answer else None
    ai_response = await ai_service.what_to_pass_to_user(section_number, human_answer)

    # Handle final_answer type to log completion (like POC)
    if ai_response.get("type") == "final_answer":
        logging.info("AI Found the final answer, now we need to move to next section")
        #TODO: update section status to completed here if needed

    return ai_response

@router.post("/{section_id}/confirm", response_model=SectionConfirmSimpleResponse)
async def confirm_section_simple(
    section_id: str,
    confirm_data: SectionConfirmRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Confirm a section by saving answer and progressing to next section.

    This endpoint:
    1. Accepts a string "answer" in the payload
    2. Saves that answer in final_output column as JSON
    3. Marks current section as READY_TO_START
    4. Finds next section in lexicographical order that is PENDING and marks it as READY_TO_START
    5. Returns response with next section ID
    """
    try:
        # Step 1: Get the current section
        section_result = await db.execute(
            select(Section).where(Section.id == section_id)
        )
        current_section = section_result.scalar_one_or_none()

        if not current_section:
            raise HTTPException(status_code=404, detail="Section not found")

        # Step 2: Save the answer to final_output as JSON
        current_section.final_output = {"answer": confirm_data.answer}
        current_section.status = SectionStatus.COMPLETED
        db.add(current_section)

        # Step 3: Find next section in lexicographical order that is PENDING
        next_section_result = await db.execute(
            select(Section)
            .where(
                Section.project_id == current_section.project_id,
                Section.form_section_number > current_section.form_section_number,
                Section.status != SectionStatus.COMPLETED
            )
            .order_by(Section.form_section_number.asc())
            .limit(1)
        )
        next_section = next_section_result.scalar_one_or_none()

        # Step 4: Mark next section as READY_TO_START if found
        if next_section:
            next_section.status = SectionStatus.READY_TO_START
            db.add(next_section)

        # Step 5: Commit all changes
        await db.commit()

        # Step 6: Prepare response
        if next_section:
            return SectionConfirmSimpleResponse(
                section_id=section_id,
                next_section_id=next_section.id,
                message=f"Section confirmed successfully. Next section: {next_section.form_section_number}",
                status=SectionStatus.READY_TO_START.value
            )
        else:
            return SectionConfirmSimpleResponse(
                section_id=section_id,
                next_section_id="",
                message="Section confirmed successfully. This is the final section.",
                status=SectionStatus.READY_TO_START.value
            )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Rollback on error
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
