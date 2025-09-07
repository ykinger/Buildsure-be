"""
CodeMatrix Repository
Data access layer for code_matrix_status operations using Pydantic models.
"""
from typing import List, Optional
from app import db
from app.models.code_matrix_status import CodeMatrixStatus, CodeMatrixStatusCreate
from sqlalchemy.orm import Session

class CodeMatrixRepository:
    """Repository class for code_matrix_status database operations."""
    
    def __init__(self, session: Session) -> None:
        self.session: Session = session
    
    def create_code_matrix_status(self, code_matrix_data: CodeMatrixStatusCreate) -> CodeMatrixStatus:
        """
        Create a new code matrix status record in the database.
        
        Args:
            code_matrix_data: Pydantic model containing code matrix status data
            
        Returns:
            The created CodeMatrixStatus ORM object
        """
        code_matrix_status = CodeMatrixStatus(
            org_id=code_matrix_data.org_id,
            project_id=code_matrix_data.project_id,
            code_matrix_questions=code_matrix_data.code_matrix_questions,
            clarifying_questions=code_matrix_data.clarifying_questions,
            curr_section=code_matrix_data.curr_section
        )
        
        self.session.add(code_matrix_status)
        self.session.commit()
        self.session.refresh(code_matrix_status)
        return code_matrix_status
    
    def get_code_matrix_status(self, org_id: str, project_id: str) -> Optional[CodeMatrixStatus]:
        """
        Get code matrix status for a specific organization and project.
        
        Args:
            org_id: The organization ID
            project_id: The project ID
            
        Returns:
            CodeMatrixStatus ORM object if found, None otherwise
        """
        return self.session.query(CodeMatrixStatus).filter(
            CodeMatrixStatus.org_id == org_id,
            CodeMatrixStatus.project_id == project_id
        ).first()
    
    def update_code_matrix_status(self, org_id: str, project_id: str, 
                                code_matrix_data: CodeMatrixStatusCreate) -> Optional[CodeMatrixStatus]:
        """
        Update an existing code matrix status record.
        
        Args:
            org_id: The organization ID
            project_id: The project ID
            code_matrix_data: Pydantic model containing updated code matrix status data
            
        Returns:
            Updated CodeMatrixStatus ORM object if found, None otherwise
        """
        code_matrix_status = self.get_code_matrix_status(org_id, project_id)
        if code_matrix_status:
            code_matrix_status.code_matrix_questions = code_matrix_data.code_matrix_questions
            code_matrix_status.clarifying_questions = code_matrix_data.clarifying_questions
            code_matrix_status.curr_section = code_matrix_data.curr_section
            
            self.session.commit()
            self.session.refresh(code_matrix_status)
            return code_matrix_status
        return None
    
    def delete_code_matrix_status(self, org_id: str, project_id: str) -> bool:
        """
        Delete a code matrix status record by organization and project ID.
        
        Args:
            org_id: The organization ID
            project_id: The project ID
            
        Returns:
            True if record was deleted, False if not found
        """
        code_matrix_status = self.get_code_matrix_status(org_id, project_id)
        if code_matrix_status:
            self.session.delete(code_matrix_status)
            self.session.commit()
            return True
        return False
    
    def get_all_for_project(self, project_id: str) -> List[CodeMatrixStatus]:
        """
        Get all code matrix status records for a specific project.
        
        Args:
            project_id: The project ID
            
        Returns:
            List of CodeMatrixStatus ORM objects
        """
        return self.session.query(CodeMatrixStatus).filter(
            CodeMatrixStatus.project_id == project_id
        ).all()
