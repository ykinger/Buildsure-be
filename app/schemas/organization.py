"""
Organization Pydantic Schemas
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class OrganizationBase(BaseModel):
    """Base organization schema with common fields"""
    name: str
    description: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    """Schema for creating an organization"""
    pass


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization"""
    name: Optional[str] = None
    description: Optional[str] = None


class OrganizationResponse(OrganizationBase):
    """Schema for organization response"""
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrganizationListResponse(BaseModel):
    """Schema for paginated organization list response"""
    items: List[OrganizationResponse]
    total: int
    page: int
    size: int
    pages: int

    model_config = ConfigDict(from_attributes=True)
