"""
Projects Router
FastAPI router for project CRUD operations.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import math
from datetime import datetime

from app.auth.cognito import get_current_user, get_current_user_and_org
from app.database import get_db
from app.models.project import Project, ProjectStatus
from app.models.organization import Organization
from app.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectCreateResponse,
    ProjectUpdate,
    ProjectDetailsResponse,
    ProjectListResponse,
    ProjectDetailResponse,
    ProjectReportResponse,
    ProjectStartResponse
)
from app.services.project_service import ProjectService
from app.services.report_export_service import ReportExportService
from app.repository.project import get_project_by_id, list_projects as list_projects_repo, create_project as create_project_repo, update_project as update_project_repo, delete_project as delete_project_repo
from app.repository.organization import get_organization_by_id
from app.repository.user import get_user_by_id

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    # org_id: Optional[str] = Query(None, description="Filter by organization ID"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    user_and_org: dict = Depends(get_current_user_and_org),
    session: AsyncSession = Depends(get_db)
):
    """List projects with pagination and optional filtering"""
    # TODO: Implement proper authentication to get current user's organization
    # For now, require org_id filter for security
    # if not org_id:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="organization_id filter is required for security"
    #     )

    # # Verify organization exists
    # organization = await get_organization_by_id(org_id, session) # Use functional repo for verification
    # if not organization:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization not found")

    user_sub = user_and_org["user_claims"]["sub"]
    # Get projects using functional repository
    projects = await list_projects_repo(session=session, user_id=user_sub, offset=(page - 1) * size, limit=size)

    # Get total count (still direct query for now, can be moved to repo if needed)
    count_query = select(func.count(Project.id))
    # .where(Project.organization_id == org_id)
    if user_id:
        count_query = count_query.where(Project.user_id == user_id)
    count_result = await session.execute(count_query)
    total = count_result.scalar()

    # Calculate pagination
    pages = math.ceil(total / size) if total > 0 else 1

    return ProjectListResponse(
        items=projects,
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.post("/", response_model=ProjectCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    user_and_org: dict = Depends(get_current_user_and_org),
    session: AsyncSession = Depends(get_db)
):
    """Create a new project"""
    # Extract user ID and organization ID from authentication
    user_sub = user_and_org["user_claims"]["sub"]
    organization_id = user_and_org["organization_id"]

    # Create project with authenticated user's data (override any provided values)
    project_dict = project_data.model_dump()
    project_dict.update({
        'user_id': user_sub,  # Force to authenticated user
        'organization_id': organization_id,  # Force to user's organization
        'status': ProjectStatus.NOT_STARTED
    })
    
    project = Project(**project_dict)
    project = await create_project_repo(project, session)

    return ProjectCreateResponse.model_validate(project)


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    project: Project = Depends(get_project_by_id),
):
    """Get project by ID"""
    # # Optional organization validation for security
    # if org_id and project.organization_id != org_id:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Project does not belong to the specified organization")

    return project


@router.post("/{project_id}/start", response_model=ProjectStartResponse, status_code=status.HTTP_200_OK)
async def start_project(
    project_id: str,
    user_and_org: dict = Depends(get_current_user_and_org),
    project: Project = Depends(get_project_by_id),
    session: AsyncSession = Depends(get_db)
):
    """Start a project by updating project status to IN_PROGRESS"""
    try:
        project_service = ProjectService()
        project = await project_service.start_project(project_id, session) # Pass project_id and session
        return project
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to start project: {str(e)}")


@router.put("/{project_id}", response_model=ProjectDetailsResponse)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    current_user: dict = Depends(get_current_user),
    project: Project = Depends(get_project_by_id),
    session: AsyncSession = Depends(get_db)
):
    """Update project by ID"""
    update_data = project_data.model_dump(exclude_unset=True)

    # Verify organization exists if organization_id is being updated
    if "organization_id" in update_data:
        organization = await get_organization_by_id(update_data["organization_id"], session)
        if not organization:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization not found")

    # Verify user exists and belongs to the organization if user_id is being updated
    if "user_id" in update_data:
        organization_id = update_data.get("organization_id", project.organization_id)
        user = await get_user_by_id(update_data["user_id"], session)
        if not user or user.organization_id != organization_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found or doesn't belong to the specified organization")

    project = await update_project_repo(project_id, update_data, session) # Use functional repo to update
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found during update")

    return ProjectDetailsResponse.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    project: Project = Depends(get_project_by_id),
    session: AsyncSession = Depends(get_db)
):
    """Delete project by ID"""
    success = await delete_project_repo(project_id, session) # Use functional repo to delete
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found during delete")

@router.get("/{project_id}/report")
async def get_project_report(
    project_id: str,
    format: Optional[str] = Query("json", description="Report format: json, pdf, or excel"),
    current_user: dict = Depends(get_current_user),
    project: Project = Depends(get_project_by_id),
    session: AsyncSession = Depends(get_db)
):
    """Generate and return a comprehensive report for the project in various formats"""
    try:
        project_service = ProjectService()
        report = await project_service.generate_project_report(project_id, session) # Pass project_id and session

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
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid format. Supported formats: json, pdf, excel")

    except ValueError as e:
        # Project not found or validation error
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        # Internal server error
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate report: {str(e)}")
