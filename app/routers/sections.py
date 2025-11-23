"""
Sections Router
FastAPI router for section CRUD operations.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
import math
import json

from pydantic import BaseModel
from sqlmodel import SQLModel

from app.auth.cognito import get_current_user
from app.database import get_db
from app.models.project import Project
from app.models.section import Section, SectionStatus
from app.models.project_data_matrix import ProjectDataMatrix
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
from app.repository.section import get_section_by_id, list_sections as list_sections_repo, create_section as create_section_repo, update_section as update_section_repo, delete_section as delete_section_repo
from app.repository.project import get_project_by_id
from app.repository.message import delete_messages
from app.repository.project_data_matrix import list_project_data_matrices, get_project_data_matrix_by_id
from app.services.ai_service import AIService

import logging

class RequestAnswer(BaseModel):
    answer: str

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

router = APIRouter(prefix="/api/v1/sections", tags=["sections"])


@router.get("/")
async def list_sections(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """List sections with pagination and optional filtering by project ID"""
    # Get sections using functional repository
    sections = await list_project_data_matrices(session=session, offset=(page - 1) * size, limit=size)

    # Get total count (still direct query for now, can be moved to repo if needed)
    count_query = select(func.count(ProjectDataMatrix.id))
    # if project_id:
    #     count_query = count_query.where(Section.project_id == project_id)
    count_result = await session.execute(count_query)
    total = count_result.scalar()

    # Calculate pagination
    pages = math.ceil(total / size) if total > 0 else 1

    return sections
    # return SectionListResponse(
    #     items=[section for section in sections],
    #     total=total,
    #     page=page,
    #     size=size,
    #     pages=pages
    # )


@router.post("/", response_model=SectionResponse, status_code=status.HTTP_201_CREATED)
async def create_section(
    section_data: SectionCreate,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Create a new section"""
    if not section_data.project_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="project_id is required")

    # Verify project exists
    project = await get_project_by_id(section_data.project_id, session)
    if not project:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project not found")

    section = Section(**section_data.model_dump())
    section = await create_section_repo(section, session)

    return SectionResponse.model_validate(section)


@router.get("/{id}")
async def get_section(
    current_user: dict = Depends(get_current_user),
    section: ProjectDataMatrix = Depends(get_project_data_matrix_by_id),
):
    """Get section by ID"""
    return section


@router.put("/{section_id}", response_model=SectionResponse)
async def update_section(
    section_id: str,
    section_data: SectionUpdate,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Update section by ID"""
    update_data = section_data.model_dump(exclude_unset=True)

    # Verify project exists if project_id is being updated
    if "project_id" in update_data:
        project = await get_project_by_id(update_data["project_id"], session)
        if not project:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project not found")

    section = await update_section_repo(section_id, update_data, session)
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found during update")

    return SectionResponse.model_validate(section)


@router.delete("/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_section(
    section_id: str,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Delete section by ID"""
    success = await delete_section_repo(section_id, session)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found during delete")


@router.get("/{id}/clear")
async def clear_section_history(
    current_user: dict = Depends(get_current_user),
    pdm: ProjectDataMatrix = Depends(get_project_data_matrix_by_id),
    ai: AIService = Depends(AIService),
    session: AsyncSession = Depends(get_db)
):
    """Clear chat history (answers) for a section"""
    await delete_messages(pdm.messages, session)
    return await ai.what_next(pdm, session)


@router.post("/{section_id}/next")
async def start_section_next(
    answer: Optional[RequestAnswer] = None,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    pdm: ProjectDataMatrix = Depends(get_project_data_matrix_by_id),
    ai: AIService = Depends(AIService)
):
    """
    Start a section conversation or continue with an answer.
    """
    return await ai.what_next(pdm, session, answer.answer)

@router.post("/{section_id}/start")
async def start_section_status_update(
    section_id: str,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    pdm: ProjectDataMatrix = Depends(get_project_data_matrix_by_id),
    ai: AIService = Depends(AIService)
):
    """
    Start a section and changes the state to In progress
    """

    return await ai.what_next(pdm, session)

@router.post("/{section_id}/confirm", response_model=SectionConfirmSimpleResponse)
async def confirm_section_simple(
    section_id: str,
    confirm_data: SectionConfirmRequest,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Confirm a section by saving answer and progressing to next section."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Section functionality is currently disabled.")
