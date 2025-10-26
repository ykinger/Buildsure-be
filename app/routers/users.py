"""
Users Router
FastAPI router for user CRUD operations.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
import math

from app.database import get_db
from app.models.user import User
from app.models.organization import Organization
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse
)

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    org_id: Optional[str] = Query(None, description="Filter by organization ID"),
    db: AsyncSession = Depends(get_db)
):
    """List users with pagination and optional organization filtering"""
    # Build query
    query = select(User)
    count_query = select(func.count(User.id))

    if org_id:
        query = query.where(User.org_id == org_id)
        count_query = count_query.where(User.org_id == org_id)

    # Get total count
    count_result = await db.execute(count_query)
    total = count_result.scalar()

    # Calculate pagination
    offset = (page - 1) * size
    pages = math.ceil(total / size) if total > 0 else 1

    # Get users
    result = await db.execute(
        query
        .offset(offset)
        .limit(size)
        .order_by(User.created_at.desc())
    )
    users = result.scalars().all()

    return UserListResponse(
        items=[UserResponse.model_validate(user) for user in users],
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new user"""
    # Verify organization exists
    org_result = await db.execute(
        select(Organization).where(Organization.id == user_data.org_id)
    )
    if not org_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Organization not found")

    # Check if email already exists
    email_result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if email_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(**user_data.model_dump())
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return UserResponse.model_validate(user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get user by ID"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update user by ID"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = user_data.model_dump(exclude_unset=True)

    # Verify organization exists if org_id is being updated
    if "org_id" in update_data:
        org_result = await db.execute(
            select(Organization).where(Organization.id == update_data["org_id"])
        )
        if not org_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Organization not found")

    # Check if email already exists (excluding current user)
    if "email" in update_data:
        email_result = await db.execute(
            select(User).where(User.email == update_data["email"], User.id != user_id)
        )
        if email_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already registered")

    # Update fields
    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete user by ID"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(user)
    await db.commit()


@router.get("/organizations/{org_id}/users", response_model=UserListResponse)
async def list_users_by_organization(
    org_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db)
):
    """List users by organization ID"""
    # Verify organization exists
    org_result = await db.execute(
        select(Organization).where(Organization.id == org_id)
    )
    if not org_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Organization not found")

    return await list_users(page=page, size=size, org_id=org_id, db=db)
