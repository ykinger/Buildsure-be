"""
Project Repository
Data access layer for project operations using Pydantic models.
"""
from typing import List, Optional
from app import db
from app.models.project import Project, ProjectCreate, ProjectResponse
from sqlalchemy.orm import Session

class ProjectRepository:
    """Repository class for project database operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_project(self, project_data: ProjectCreate) -> Project:
        """
        Create a new project in the database.
        
        Args:
            project_data: Pydantic model containing project data
            
        Returns:
            The created Project ORM object
        """
        project = Project(
            name=project_data.name,
            description=project_data.description,
            due_date=project_data.due_date,
            organization_id=project_data.organization_id,
            status=project_data.status
        )
        
        self.session.add(project)
        self.session.commit()
        self.session.refresh(project)
        return project
    
    def get_projects_by_organization(self, organization_id: str) -> List[Project]:
        """
        Get all projects for a specific organization.
        
        Args:
            organization_id: The organization ID to filter by
            
        Returns:
            List of Project ORM objects
        """
        return self.session.query(Project).filter(
            Project.organization_id == organization_id
        ).all()
    
    def get_project_by_id(self, project_id: str) -> Optional[Project]:
        """
        Get a project by its ID.
        
        Args:
            project_id: The project ID to search for
            
        Returns:
            Project ORM object if found, None otherwise
        """
        return self.session.query(Project).filter(
            Project.id == project_id
        ).first()
    
    def update_project(self, project_id: str, project_data: ProjectCreate) -> Optional[Project]:
        """
        Update an existing project.
        
        Args:
            project_id: The project ID to update
            project_data: Pydantic model containing updated project data
            
        Returns:
            Updated Project ORM object if found, None otherwise
        """
        project = self.get_project_by_id(project_id)
        if project:
            project.name = project_data.name
            project.description = project_data.description
            project.due_date = project_data.due_date
            project.status = project_data.status
            
            self.session.commit()
            self.session.refresh(project)
            return project
        return None
    
    def delete_project(self, project_id: str) -> bool:
        """
        Delete a project by its ID.
        
        Args:
            project_id: The project ID to delete
            
        Returns:
            True if project was deleted, False if not found
        """
        project = self.get_project_by_id(project_id)
        if project:
            self.session.delete(project)
            self.session.commit()
            return True
        return False
