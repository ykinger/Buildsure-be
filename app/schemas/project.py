"""
Project Pydantic Schemas
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from app.models.project import ProjectStatus
from app.schemas.section import SectionResponse


class ProjectBase(BaseModel):
    """Base project schema with common fields"""
    name: str
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.NOT_STARTED
    current_section: str = "3.01"
    due_date: Optional[datetime] = None


class ProjectCreate(BaseModel):
    """Schema for creating a project"""
    name: str
    description: Optional[str] = None
    organization_id: str = ""
    user_id: str = ""
    due_date: Optional[datetime] = None


class ProjectUpdate(BaseModel):
    """Schema for updating a project"""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    current_section: Optional[str] = None
    due_date: Optional[datetime] = None

    organization_id: Optional[str] = None
    user_id: Optional[str] = None


class ProjectResponse(ProjectBase):
    """Schema for project response"""
    id: str
    organization_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    total_sections: int
    completed_sections: int
    sections: List[SectionResponse]

    model_config = ConfigDict(from_attributes=True)


class ProjectListResponse(BaseModel):
    """Schema for paginated project list response"""
    items: List[ProjectResponse]
    total: int
    page: int
    size: int
    pages: int

    model_config = ConfigDict(from_attributes=True)


class SectionReportData(BaseModel):
    """Schema for individual section data in project report"""
    form_section_number: str
    final_output: Optional[Dict[str, Any]] = None
    completed: bool = False

    model_config = ConfigDict(from_attributes=True)


class ProjectDetailResponse(BaseModel):
    """Schema for detailed project response with all sections"""
    # Project fields
    id: str
    name: str
    description: Optional[str]
    status: ProjectStatus
    current_section: str
    due_date: Optional[datetime]

    organization_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    total_sections: int
    completed_sections: int
    sections: List[SectionResponse]
    model_config = ConfigDict(from_attributes=True)


class ProjectReportResponse(BaseModel):
    """Schema for project report response with dynamic sections"""
    project_id: str
    project_name: str
    project_status: ProjectStatus
    generated_at: datetime
    sections: Dict[str, SectionReportData]  # Dynamic keys like "section_1", "section_2", etc.

    @property
    def total_sections(self) -> int:
        """Calculate total sections from sections dict"""
        return len(self.sections)

    @property
    def completed_sections(self) -> int:
        """Calculate completed sections from sections dict"""
        return sum(1 for section in self.sections.values() if section.completed)

    model_config = ConfigDict(from_attributes=True)
