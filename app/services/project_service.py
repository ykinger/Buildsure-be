"""
Project Service
Business logic for project creation and management.
"""
from typing import List, Dict
from sqlalchemy.orm import Session
from app.models.project import Project, ProjectCreate, ProjectResponse
from app.repositories.project_repository import ProjectRepository

class ProjectService:
    """Service class for project business logic."""
    
    def __init__(self, project_repository: ProjectRepository):
        """
        Initialize ProjectService with a project repository.
        
        Args:
            project_repository: ProjectRepository instance for data access
        """
        self.project_repository = project_repository
    
    def create_project(self, org_id: str, payload: Dict) -> Project:
        """
        Create a new project using repository pattern.
        
        Args:
            org_id: Organization ID
            payload: Project data dictionary
            
        Returns:
            Created Project ORM object
        """
        # Convert payload to Pydantic model
        project_data = ProjectCreate(
            name=payload.get('name'),
            description=payload.get('description'),
            due_date=payload.get('dueDate'),
            organization_id=org_id,
            status=payload.get('status', 'not_started')
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
