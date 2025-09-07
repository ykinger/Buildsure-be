"""
Project Service
Business logic for project creation and management.
"""
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from app.models.project import Project, ProjectCreate, ProjectResponse
from app.repositories.project_repository import ProjectRepository
from app.repositories.code_matrix_repository import CodeMatrixRepository
from app.models.ai_response import create_error_response
import logging

logger = logging.getLogger(__name__)

class ProjectService:
    """Service class for project business logic."""
    
    def __init__(self, project_repository: ProjectRepository, code_matrix_repository: CodeMatrixRepository, ai_service: Optional[Any] = None) -> None:
        """
        Initialize ProjectService with repositories and optional AI service.
        
        Args:
            project_repository: ProjectRepository instance for project data access
            code_matrix_repository: CodeMatrixRepository instance for code matrix data access
            ai_service: Optional AIService instance for AI functionality
        """
        self.project_repository: ProjectRepository = project_repository
        self.code_matrix_repository: CodeMatrixRepository = code_matrix_repository
        self.ai_service: Optional[Any] = ai_service
    
    def create_project(self, org_id: str, payload: Dict[str, Any]) -> Project:
        """
        Create a new project using repository pattern.
        
        Args:
            org_id: Organization ID
            payload: Project data dictionary with string keys
            
        Returns:
            Created Project ORM object
        """
        # Convert payload to Pydantic model
        project_data = ProjectCreate(
            name=payload.get('name'),
            description=payload.get('description'),
            due_date=payload.get('dueDate'),
            organization_id=org_id,
            status=payload.get('status', 'not_started'),
            curr_task=payload.get('currTask', 'code_matrix')
        )
        
        # Use repository for database operations
        return self.project_repository.create_project(project_data)

    def get_projects_by_org(self, org_id: str) -> List[Project]:
        """
        Get projects by organization ID using repository pattern.
        
        Args:
            org_id: Organization ID
            
        Returns:
            List of Project ORM objects
        """
        return self.project_repository.get_projects_by_organization(org_id)

    def get_project(self, org_id: str, project_id: str) -> Project:
        """
        Get a single project by organization ID and project ID.
        
        Args:
            org_id: Organization ID
            project_id: Project ID
            
        Returns:
            Project ORM object
            
        Raises:
            ValueError: If project is not found or doesn't belong to the organization
        """
        project = self.project_repository.get_project_by_id(project_id)
        
        if not project:
            raise ValueError(f"Project with ID {project_id} not found")
            
        if project.organization_id != org_id:
            raise ValueError(f"Project {project_id} does not belong to organization {org_id}")
            
        return project
