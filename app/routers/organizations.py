"""
Organizations Router
FastAPI router for organization CRUD operations.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
import math

from app.auth.cognito import get_current_user
from app.database import get_db
from app.models.organization import Organization
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationListResponse
)
from app.repository.organization import get_organization_by_id, list_organizations as list_organizations_repo, create_organization as create_organization_repo, update_organization as update_organization_repo, delete_organization as delete_organization_repo

router = APIRouter(prefix="/api/v1/organizations", tags=["organizations"])


@router.get("/", response_model=OrganizationListResponse)
async def list_organizations(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """List organizations with pagination"""
    # Get organizations using functional repository
    organizations = await list_organizations_repo(session=session, offset=(page - 1) * size, limit=size)

    # Get total count (still direct query for now, can be moved to repo if needed)
    count_result = await session.execute(select(func.count(Organization.id)))
    total = count_result.scalar()

    # Calculate pagination
    pages = math.ceil(total / size) if total > 0 else 1

    return OrganizationListResponse(
        items=[OrganizationResponse.model_validate(org) for org in organizations],
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.post("/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    organization_data: OrganizationCreate,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Create a new organization"""
    organization = Organization(**organization_data.model_dump())
    organization = await create_organization_repo(organization, session)

    return OrganizationResponse.model_validate(organization)


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: str,
    current_user: dict = Depends(get_current_user),
    organization: Organization = Depends(get_organization_by_id),
):
    """Get organization by ID"""
    return OrganizationResponse.model_validate(organization)


@router.put("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: str,
    organization_data: OrganizationUpdate,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Update organization by ID"""
    update_data = organization_data.model_dump(exclude_unset=True)
    organization = await update_organization_repo(organization_id, update_data, session)

    if not organization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found during update")

    return OrganizationResponse.model_validate(organization)


@router.delete("/{organization_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    organization_id: str,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Delete organization by ID"""
    success = await delete_organization_repo(organization_id, session)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found during delete")
