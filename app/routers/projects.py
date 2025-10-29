"""
Projects Router
FastAPI router for project CRUD operations.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import math

from app.database import get_db
from app.models.project import Project, ProjectStatus
from app.models.organization import Organization
from app.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
    ProjectDetailResponse,
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
    db: AsyncSession = Depends(get_db)
):
    """List projects with pagination and optional filtering"""
    # TODO: Implement proper authentication to get current user's organization
    # For now, require org_id filter for security
    if not org_id:
        raise HTTPException(
            status_code=400,
            detail="organization_id filter is required for security"
        )

    # Verify organization exists
    org_result = await db.execute(
        select(Organization).where(Organization.id == org_id)
    )
    if not org_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Organization not found")

    # Build query
    query = select(Project).where(Project.organization_id == org_id)
    count_query = select(func.count(Project.id)).where(Project.organization_id == org_id)

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
    db: AsyncSession = Depends(get_db)
):
    """Create a new project"""
    # TODO: Implement proper authentication to get current user and organization
    # For now, require organization_id and user_id to be provided
    if not project_data.organization_id:
        raise HTTPException(status_code=400, detail="organization_id is required")
    if not project_data.user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    # Verify organization exists
    org_result = await db.execute(
        select(Organization).where(Organization.id == project_data.organization_id)
    )
    if not org_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Organization not found")

    # Verify user exists and belongs to the organization
    user_result = await db.execute(
        select(User).where(
            User.id == project_data.user_id,
            User.organization_id == project_data.organization_id
        )
    )
    if not user_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User not found or doesn't belong to the organization")

    # Create project with default values
    project_dict = project_data.model_dump()
    project_dict.update({
        'status': ProjectStatus.NOT_STARTED
    })
    project = Project(**project_dict)
    db.add(project)
    await db.commit()
    await db.refresh(project)

    return ProjectResponse.model_validate(project)


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(
    project_id: str,
    org_id: Optional[str] = Query(None, description="Organization ID for validation"),
    db: AsyncSession = Depends(get_db)
):
    """Get project by ID"""
    try:
        result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Optional organization validation for security
        if org_id and project.organization_id != org_id:
            raise HTTPException(status_code=403, detail="Project does not belong to the specified organization")

        response_data = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "current_section": project.current_section,

            "organization_id": project.organization_id,
            "user_id": project.user_id,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
        }

        return ProjectDetailResponse(**response_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve project: {str(e)}")


@router.post("/{project_id}/start", response_model=ProjectDetailResponse, status_code=201)
async def start_project(
    project_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Start a project by updating project status to IN_PROGRESS"""
    try:
        project_service = ProjectService()
        project = await project_service.start_project(project_id, db)
        return project
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start project: {str(e)}")


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update project by ID"""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = project_data.model_dump(exclude_unset=True)

    # Verify organization exists if organization_id is being updated
    if "organization_id" in update_data:
        org_result = await db.execute(
            select(Organization).where(Organization.id == update_data["organization_id"])
        )
        if not org_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Organization not found")

    # Verify user exists and belongs to the organization if user_id is being updated
    if "user_id" in update_data:
        organization_id = update_data.get("organization_id", project.organization_id)
        user_result = await db.execute(
            select(User).where(
                User.id == update_data["user_id"],
                User.organization_id == organization_id
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
    db: AsyncSession = Depends(get_db)
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

@router.get("/{project_id}/report")
async def get_project_report(
    project_id: str,
    format: Optional[str] = Query("json", description="Report format: json, pdf, or excel"),
    db: AsyncSession = Depends(get_db)
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
