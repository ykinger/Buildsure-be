"""
User Pydantic Schemas
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    """Base user schema with common fields"""
    name: str
    email: EmailStr


class UserCreate(UserBase):
    """Schema for creating a user"""
    org_id: str


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    org_id: Optional[str] = None


class UserResponse(UserBase):
    """Schema for user response"""
    id: str
    org_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    """Schema for paginated user list response"""
    items: List[UserResponse]
    total: int
    page: int
    size: int
    pages: int

    model_config = ConfigDict(from_attributes=True)
