"""
Users Router
FastAPI router for user CRUD operations.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
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
from app.repository.user import get_user_by_id, get_user_by_email, list_users as list_users_repo, create_user as create_user_repo, update_user as update_user_repo, delete_user as delete_user_repo
from app.repository.organization import get_organization_by_id

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    session: AsyncSession = Depends(get_db)
):
    """List users with pagination and optional organization filtering"""
    # Get users using functional repository
    users = await list_users_repo(session=session, offset=(page - 1) * size, limit=size)

    # Get total count (still direct query for now, can be moved to repo if needed)
    count_query = select(func.count(User.id))
    # if org_id:
    #     count_query = count_query.where(User.organization_id == org_id)
    count_result = await session.execute(count_query)
    total = count_result.scalar()

    # Calculate pagination
    pages = math.ceil(total / size) if total > 0 else 1

    return UserListResponse(
        items=[UserResponse.model_validate(user) for user in users],
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_db)
):
    """Create a new user"""
    # Verify organization exists
    organization = await get_organization_by_id(user_data.organization_id, session)
    if not organization:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization not found")

    # Check if email already exists
    existing_user = await get_user_by_email(user_data.email, session)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = User(**user_data.model_dump())
    user = await create_user_repo(user, session)

    return UserResponse.model_validate(user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    user: User = Depends(get_user_by_id),
):
    """Get user by ID"""
    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    user: User = Depends(get_user_by_id),
    session: AsyncSession = Depends(get_db)
):
    """Update user by ID"""
    update_data = user_data.model_dump(exclude_unset=True)

    # Verify organization exists if org_id is being updated
    if "organization_id" in update_data:
        organization = await get_organization_by_id(update_data["organization_id"], session)
        if not organization:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization not found")

    # Check if email already exists (excluding current user)
    if "email" in update_data:
        existing_user = await get_user_by_email(update_data["email"], session)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = await update_user_repo(user_id, update_data, session)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found during update")

    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    user: User = Depends(get_user_by_id),
    session: AsyncSession = Depends(get_db)
):
    """Delete user by ID"""
    success = await delete_user_repo(user_id, session)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found during delete")


@router.get("/organizations/{org_id}/users", response_model=UserListResponse)
async def list_users_by_organization(
    org_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    session: AsyncSession = Depends(get_db)
):
    """List users by organization ID"""
    # Verify organization exists
    organization = await get_organization_by_id(org_id, session)
    if not organization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    return await list_users_repo(page=page, size=size, organization_id=org_id, session=session)
