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


@router.get("/", response_model=SectionListResponse)
async def list_sections(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    project_id: str = Query(..., description="Project ID to filter sections"),
    db: AsyncSession = Depends(get_async_db)
):
    """List sections with pagination filtered by project ID"""
    # Build query
    query = select(Section)
    count_query = select(func.count(Section.id))

    if project_id:
        query = query.where(Section.project_id == project_id)
        count_query = count_query.where(Section.project_id == project_id)

    # Get total count
    count_result = await db.execute(count_query)
    total = count_result.scalar()

    # Calculate pagination
    offset = (page - 1) * size
    pages = math.ceil(total / size) if total > 0 else 1

    # Get sections
    result = await db.execute(
        query
        .offset(offset)
        .limit(size)
        .order_by(Section.form_section_number.asc())
    )
    sections = result.scalars().all()

    return SectionListResponse(
        items=[SectionResponse.model_validate(section) for section in sections],
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.post("/", response_model=SectionResponse, status_code=201)
async def create_section(
    section_data: SectionCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new section"""
    # Verify project exists
    project_result = await db.execute(
        select(Project).where(Project.id == section_data.project_id)
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Project not found")

    # Check if section number already exists for this project
    existing_section = await db.execute(
        select(Section).where(
            Section.project_id == section_data.project_id,
            Section.section_number == section_data.section_number
        )
    )
    if existing_section.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Section number already exists for this project")

    section = Section(**section_data.model_dump())
    db.add(section)
    await db.commit()
    await db.refresh(section)

    return SectionResponse.model_validate(section)


@router.get("/{section_id}", response_model=SectionResponse)
async def get_section(
    section_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """Get section by ID"""
    result = await db.execute(
        select(Section).where(Section.id == section_id)
    )
    section = result.scalar_one_or_none()

    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    return SectionResponse.model_validate(section)


@router.put("/{section_id}", response_model=SectionResponse)
async def update_section(
    section_id: str,
    section_data: SectionUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """Update section by ID"""
    result = await db.execute(
        select(Section).where(Section.id == section_id)
    )
    section = result.scalar_one_or_none()

    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    update_data = section_data.model_dump(exclude_unset=True)

    # Verify project exists if project_id is being updated
    if "project_id" in update_data:
        project_result = await db.execute(
            select(Project).where(Project.id == update_data["project_id"])
        )
        if not project_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Project not found")

    # Check if section number already exists for the project (excluding current section)
    if "section_number" in update_data:
        project_id = update_data.get("project_id", section.project_id)
        existing_result = await db.execute(
            select(Section).where(
                Section.project_id == project_id,
                Section.form_section_number == update_data["form_section_number"],
                Section.id != section_id
            )
        )
        if existing_section.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Section number already exists for this project")

    # Update fields
    for field, value in update_data.items():
        setattr(section, field, value)

    await db.commit()
    await db.refresh(section)

    return SectionResponse.model_validate(section)


@router.delete("/{section_id}", status_code=204)
async def delete_section(
    section_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """Delete section by ID"""
    result = await db.execute(
        select(Section).where(Section.id == section_id)
    )
    section = result.scalar_one_or_none()

    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    await db.delete(section)
    await db.commit()


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


@router.get("/projects/{project_id}/sections", response_model=SectionListResponse)
async def list_sections_by_project(
    project_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_async_db)
):
    """List sections by project ID"""
    # Verify project exists
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")

    return await list_sections(page=page, size=size, project_id=project_id, db=db)


@router.post("/projects/{project_id}/sections/{section_number}/answer", response_model=SectionAnswerResponse)
async def submit_section_answer(
    project_id: str,
    section_number: int,
    answer_data: AnswerCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Submit an answer for a section question.

    This endpoint:
    1. Accepts question_text and answer_text
    2. Saves both in answers table
    3. Retrieves all previous answers and relevant guideline chunks
    4. Calls LangChain with prompt template to generate next question or draft section
    5. Returns JSON with next_question or draft_output
    """
    try:
        section_service = SectionService()
        result = await section_service.process_section_answer(
            project_id=project_id,
            section_number=section_number,
            question_text=answer_data.question_text,
            answer_text=answer_data.answer_text,
            db=db
        )

        return SectionAnswerResponse(**result)

    except ValueError as e:
        # Business logic validation errors
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Unexpected errors
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/projects/{project_id}/sections/{section_number}/confirm", response_model=SectionConfirmResponse)
async def confirm_section(
    project_id: str,
    section_number: int,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Confirm a section by finalizing its output and updating project progress.

    This endpoint:
    1. Validates that the section is in_progress and matches current_section
    2. Saves draft_output as final_output
    3. Marks section as completed
    4. Increments project's completed_sections and advances current_section
    5. If all sections completed, marks project as completed
    """
    try:
        section_service = SectionService()
        result = await section_service.confirm_section(project_id, section_number, db)

        return SectionConfirmResponse(**result)

    except ValueError as e:
        # Business logic validation errors
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Unexpected errors
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


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
