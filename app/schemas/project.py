"""
Project Pydantic Schemas
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.models.project import ProjectStatus


class ProjectBase(BaseModel):
    """Base project schema with common fields"""
    name: str
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.NOT_STARTED
    current_section: int = 0
    total_sections: int = 0
    completed_sections: int = 0


class ProjectCreate(ProjectBase):
    """Schema for creating a project"""
    org_id: str
    user_id: str


class ProjectUpdate(BaseModel):
    """Schema for updating a project"""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    current_section: Optional[int] = None
    total_sections: Optional[int] = None
    completed_sections: Optional[int] = None
    org_id: Optional[str] = None
    user_id: Optional[str] = None


class ProjectResponse(ProjectBase):
    """Schema for project response"""
    id: str
    org_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectListResponse(BaseModel):
    """Schema for paginated project list response"""
    items: List[ProjectResponse]
    total: int
    page: int
    size: int
    pages: int

    model_config = ConfigDict(from_attributes=True)
