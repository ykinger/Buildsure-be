"""
Projects Router
FastAPI router for project CRUD operations.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
import math
from io import BytesIO

from app.database import get_async_db
from app.models.project import Project
from app.models.organization import Organization
from app.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
    ProjectReportResponse
)
from app.services.project_service import ProjectService
from app.services.report_export_service import ReportExportService

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    org_id: Optional[str] = Query(None, description="Filter by organization ID"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    db: AsyncSession = Depends(get_async_db)
):
    """List projects with pagination and optional filtering"""
    # Build query
    query = select(Project)
    count_query = select(func.count(Project.id))
    
    if org_id:
        query = query.where(Project.org_id == org_id)
        count_query = count_query.where(Project.org_id == org_id)
    
    if user_id:
        query = query.where(Project.user_id == user_id)
        count_query = count_query.where(Project.user_id == user_id)
    
    # Get total count
    count_result = await db.execute(count_query)
    total = count_result.scalar()
    
    # Calculate pagination
    offset = (page - 1) * size
    pages = math.ceil(total / size) if total > 0 else 1
    
    # Get projects
    result = await db.execute(
        query
        .offset(offset)
        .limit(size)
        .order_by(Project.created_at.desc())
    )
    projects = result.scalars().all()
    
    return ProjectListResponse(
        items=[ProjectResponse.model_validate(project) for project in projects],
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new project"""
    # Verify organization exists
    org_result = await db.execute(
        select(Organization).where(Organization.id == project_data.org_id)
    )
    if not org_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Organization not found")
    
    # Verify user exists and belongs to the organization
    user_result = await db.execute(
        select(User).where(
            User.id == project_data.user_id,
            User.org_id == project_data.org_id
        )
    )
    if not user_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User not found or doesn't belong to the organization")
    
    project = Project(**project_data.model_dump())
    db.add(project)
    await db.commit()
    await db.refresh(project)
    
    return ProjectResponse.model_validate(project)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """Get project by ID"""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return ProjectResponse.model_validate(project)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """Update project by ID"""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    update_data = project_data.model_dump(exclude_unset=True)
    
    # Verify organization exists if org_id is being updated
    if "org_id" in update_data:
        org_result = await db.execute(
            select(Organization).where(Organization.id == update_data["org_id"])
        )
        if not org_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Organization not found")
    
    # Verify user exists and belongs to the organization if user_id is being updated
    if "user_id" in update_data:
        org_id = update_data.get("org_id", project.org_id)
        user_result = await db.execute(
            select(User).where(
                User.id == update_data["user_id"],
                User.org_id == org_id
            )
        )
        if not user_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="User not found or doesn't belong to the organization")
    
    # Update fields
    for field, value in update_data.items():
        setattr(project, field, value)
    
    await db.commit()
    await db.refresh(project)
    
    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """Delete project by ID"""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    await db.delete(project)
    await db.commit()


@router.get("/organizations/{org_id}/projects", response_model=ProjectListResponse)
async def list_projects_by_organization(
    org_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_async_db)
):
    """List projects by organization ID"""
    # Verify organization exists
    org_result = await db.execute(
        select(Organization).where(Organization.id == org_id)
    )
    if not org_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Organization not found")
    
    return await list_projects(page=page, size=size, org_id=org_id, db=db)


@router.get("/users/{user_id}/projects", response_model=ProjectListResponse)
async def list_projects_by_user(
    user_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_async_db)
):
    """List projects by user ID"""
    # Verify user exists
    user_result = await db.execute(
        select(User).where(User.id == user_id)
    )
    if not user_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="User not found")
    
    return await list_projects(page=page, size=size, user_id=user_id, db=db)


@router.get("/{project_id}/report")
async def get_project_report(
    project_id: str,
    format: Optional[str] = Query("json", description="Report format: json, pdf, or excel"),
    db: AsyncSession = Depends(get_async_db)
):
    """Generate and return a comprehensive report for the project in various formats"""
    try:
        project_service = ProjectService()
        report = await project_service.generate_project_report(project_id, db)
        
        # Return JSON format by default
        if format.lower() == "json":
            return report
        
        # Handle export formats
        export_service = ReportExportService()
        
        if format.lower() == "pdf":
            pdf_buffer = await export_service.export_to_pdf(report)
            
            def iter_pdf():
                yield pdf_buffer.read()
            
            return StreamingResponse(
                iter_pdf(),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=project_{project_id}_report.pdf"
                }
            )
        
        elif format.lower() == "excel":
            excel_buffer = await export_service.export_to_excel(report)
            
            def iter_excel():
                yield excel_buffer.read()
            
            return StreamingResponse(
                iter_excel(),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename=project_{project_id}_report.xlsx"
                }
            )
        
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Supported formats: json, pdf, excel")
            
    except ValueError as e:
        # Project not found or validation error
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # Internal server error
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")
