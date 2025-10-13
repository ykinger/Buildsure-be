"""
Projects Router
FastAPI router for project CRUD operations.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
import math

from app.database import get_async_db
from app.models.project import Project, ProjectStatus
from app.models.organization import Organization
from app.models.user import User
from app.models.section import Section, SectionStatus
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
    project_data.org_id = "17c93869-01ae-4cf8-8fac-17feb289e994"
    project_data.user_id = "e22aad92-d56a-4198-a35b-631863e53463"
    print("TODO change this : We are hardcoding org_id and user_id till we add auth", project_data)

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
    
    # Create project with hardcoded total_sections=27
    project_dict = project_data.model_dump()
    project_dict.update({
        'total_sections': 27,
        'current_section': '3.01',
        'completed_sections': 0,
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
    db: AsyncSession = Depends(get_async_db)
):
    """Get project by ID with all sections"""
    from app.models.form_section_template import FormSectionTemplate
    
    result = await db.execute(
        select(Project)
        .options(
            selectinload(Project.sections).selectinload(Section.form_template)
        )
        .where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Build response with sections including form_title
    from app.schemas.section import SectionResponse
    sections_data = []
    for section in project.sections:
        section_dict = {
            "id": section.id,
            "project_id": section.project_id,
            "form_section_number": section.form_section_number,
            "status": section.status,
            "draft_output": section.draft_output,
            "final_output": section.final_output,
            "form_title": section.form_template.form_title if section.form_template else None,
            "created_at": section.created_at,
            "updated_at": section.updated_at
        }
        sections_data.append(SectionResponse(**section_dict))
    
    response_data = {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "status": project.status,
        "current_section": project.current_section,
        "total_sections": project.total_sections,
        "completed_sections": project.completed_sections,
        "org_id": project.org_id,
        "user_id": project.user_id,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "sections": sections_data
    }
    
    return ProjectDetailResponse(**response_data)


@router.post("/{project_id}/start", response_model=ProjectDetailResponse, status_code=201)
async def start_project(
    project_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """Start a project by creating 27 sections and updating project status"""
    # Get project
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Create 27 sections using bulk insert
    sections = []
    for section_number in range(1, 28):  # 1 to 27
        # Set section 1 as READY_TO_START, others as PENDING
        status = SectionStatus.READY_TO_START if section_number == 1 else SectionStatus.PENDING
        form_section_number = f"3.{section_number:02d}"
        sections.append(Section(
            project_id=project.id,
            form_section_number=form_section_number,
            status=status
        ))
    
    db.add_all(sections)
    
    # Update project status to IN_PROGRESS
    project.status = ProjectStatus.IN_PROGRESS
    
    await db.commit()
    await db.refresh(project)
    
    # Get all sections for response with form_template
    from app.models.form_section_template import FormSectionTemplate
    sections_result = await db.execute(
        select(Section)
        .options(selectinload(Section.form_template))
        .where(Section.project_id == project_id)
        .order_by(Section.form_section_number)
    )
    all_sections = sections_result.scalars().all()
    
    # Build response with sections including form_title
    from app.schemas.section import SectionResponse
    sections_data = []
    for section in all_sections:
        section_dict = {
            "id": section.id,
            "project_id": section.project_id,
            "form_section_number": section.form_section_number,
            "status": section.status,
            "draft_output": section.draft_output,
            "final_output": section.final_output,
            "form_title": section.form_template.form_title if section.form_template else None,
            "created_at": section.created_at,
            "updated_at": section.updated_at
        }
        sections_data.append(SectionResponse(**section_dict))
    
    response_data = {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "status": project.status,
        "current_section": project.current_section,
        "total_sections": project.total_sections,
        "completed_sections": project.completed_sections,
        "org_id": project.org_id,
        "user_id": project.user_id,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "sections": sections_data
    }
    
    return ProjectDetailResponse(**response_data)


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
