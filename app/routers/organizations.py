"""
Organizations Router
FastAPI router for organization CRUD operations.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
import math

from app.database import get_async_db
from app.models.organization import Organization
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationListResponse
)

router = APIRouter(prefix="/api/v1/organizations", tags=["organizations"])


@router.get("/", response_model=OrganizationListResponse)
async def list_organizations(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_async_db)
):
    """List organizations with pagination"""
    # Get total count
    count_result = await db.execute(select(func.count(Organization.id)))
    total = count_result.scalar()
    
    # Calculate pagination
    offset = (page - 1) * size
    pages = math.ceil(total / size) if total > 0 else 1
    
    # Get organizations
    result = await db.execute(
        select(Organization)
        .offset(offset)
        .limit(size)
        .order_by(Organization.created_at.desc())
    )
    organizations = result.scalars().all()
    
    return OrganizationListResponse(
        items=[OrganizationResponse.model_validate(org) for org in organizations],
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.post("/", response_model=OrganizationResponse, status_code=201)
async def create_organization(
    organization_data: OrganizationCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new organization"""
    organization = Organization(**organization_data.model_dump())
    db.add(organization)
    await db.commit()
    await db.refresh(organization)
    
    return OrganizationResponse.model_validate(organization)


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """Get organization by ID"""
    result = await db.execute(
        select(Organization).where(Organization.id == organization_id)
    )
    organization = result.scalar_one_or_none()
    
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    return OrganizationResponse.model_validate(organization)


@router.put("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: str,
    organization_data: OrganizationUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """Update organization by ID"""
    result = await db.execute(
        select(Organization).where(Organization.id == organization_id)
    )
    organization = result.scalar_one_or_none()
    
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Update fields
    update_data = organization_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(organization, field, value)
    
    await db.commit()
    await db.refresh(organization)
    
    return OrganizationResponse.model_validate(organization)


@router.delete("/{organization_id}", status_code=204)
async def delete_organization(
    organization_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """Delete organization by ID"""
    result = await db.execute(
        select(Organization).where(Organization.id == organization_id)
    )
    organization = result.scalar_one_or_none()
    
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    await db.delete(organization)
    await db.commit()
