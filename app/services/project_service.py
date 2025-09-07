"""
Project Service
Business logic for project creation and management.
"""
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from app.models.project import Project, ProjectCreate, ProjectResponse
from app.repositories.project_repository import ProjectRepository
import logging

logger = logging.getLogger(__name__)

class ProjectService:
    """Service class for project business logic."""
    
    def __init__(self, project_repository: ProjectRepository, ai_service: Optional[Any] = None) -> None:
        """
        Initialize ProjectService with a project repository and optional AI service.
        
        Args:
            project_repository: ProjectRepository instance for data access
            ai_service: Optional AIService instance for AI functionality
        """
        self.project_repository: ProjectRepository = project_repository
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

    def start_project_analysis(self, org_id: str, project_id: str) -> Dict[str, Any]:
        """
        Start AI analysis for a project.
        
        Args:
            org_id: Organization ID
            project_id: Project ID
            
        Returns:
            Dictionary with AI analysis response (question or decision)
        """
        try:
            if not self.ai_service:
                logger.warning("AI service not available - returning fallback response")
                # Return fallback response when AI service is unavailable
                import datetime
                return {
                    "id": "fallback-response",
                    "type": "decision",
                    "decision": {
                        "text": "AI analysis service is currently unavailable. Please try again later.",
                        "confidence": 0.0,
                        "follow_up_required": False
                    },
                    "metadata": {
                        "session_id": "fallback-session",
                        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                        "next_step": "complete"
                    }
                }
            
            # Call AI service for project analysis
            return self.ai_service.start_project_analysis(org_id, project_id)
            
        except Exception as e:
            logger.error(f"Error starting project analysis: {e}")
            # Return error response
            import datetime
            return {
                "id": "error-response",
                "type": "decision",
                "decision": {
                    "text": "An error occurred while starting project analysis. Please try again.",
                    "confidence": 0.0,
                    "follow_up_required": False
                },
                "metadata": {
                    "session_id": "error-session",
                    "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                    "next_step": "complete",
                    "error": str(e)
                }
            }

    def query_code_matrix(self, org_id: str, project_id: str) -> Dict[str, Any]:
        """
        Query AI service with code matrix data.
        
        Args:
            org_id: Organization ID
            project_id: Project ID
            
        Returns:
            Dictionary with AI response
        """
        try:
            # Get code matrix status from repository
            code_matrix_status = self.project_repository.get_code_matrix_status(org_id, project_id)
            
            # Use empty values if no code matrix status is found
            current_section = ""
            code_matrix_questions = []
            clarifying_questions = []
            
            if code_matrix_status:
                current_section = code_matrix_status.curr_section or ""
                code_matrix_questions = code_matrix_status.code_matrix_questions or []
                clarifying_questions = code_matrix_status.clarifying_questions or []
            
            if not self.ai_service:
                logger.warning("AI service not available - returning fallback response")
                # Return fallback response when AI service is unavailable
                import datetime
                return {
                    "id": "fallback-response",
                    "type": "decision",
                    "decision": {
                        "text": "AI analysis service is currently unavailable. Please try again later.",
                        "confidence": 0.0,
                        "follow_up_required": False
                    },
                    "metadata": {
                        "session_id": "fallback-session",
                        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                        "next_step": "complete"
                    }
                }
            
            # Call AI service query with code matrix data (empty values if no record found)
            return self.ai_service.query(
                current_question_number=current_section,
                form_questions_and_answers=code_matrix_questions,
                clarifying_questions_and_answers=clarifying_questions
            )
            
        except Exception as e:
            logger.error(f"Error querying code matrix: {e}")
            # Return error response
            import datetime
            return {
                "id": "error-response",
                "type": "decision",
                "decision": {
                    "text": "An error occurred while querying code matrix. Please try again.",
                    "confidence": 0.0,
                    "follow_up_required": False
                },
                "metadata": {
                    "session_id": "error-session",
                    "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                    "next_step": "complete",
                    "error": str(e)
                }
            }
