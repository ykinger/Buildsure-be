"""
Project Service Module
Handles project-related business logic and orchestration.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.project import Project, ProjectStatus
from app.models.section import Section, SectionStatus
from app.schemas.project import ProjectReportResponse, SectionReportData, ProjectStartResponse
from app.schemas.section import SectionResponse

logger = logging.getLogger(__name__)


class ProjectService:
    """Service for managing project operations and business logic."""
    
    async def start_project(
        self,
        project_id: str,
        db: AsyncSession
    ) -> ProjectStartResponse:
        """
        Start a project by creating 27 sections and updating project status.
        
        Args:
            project_id: The project ID
            db: Database session
            
        Returns:
            ProjectStartResponse containing project details with all 27 sections
            
        Raises:
            ValueError: If project not found
            RuntimeError: If database operations fail
        """
        try:
            # Get project
            project = await self._get_project_by_id(project_id, db)
            
            # Create 27 sections
            sections = []
            for section_number in range(1, 28):  # 1 to 27
                # Set section 1 as READY_TO_START, others as PENDING
                status = SectionStatus.READY_TO_START if section_number == 1 else SectionStatus.PENDING
                form_section_number = f"3.{section_number:02d}"
                sections.append(Section(
                    project_id=project.id,
                    form_section_number=form_section_number,
                    status=status
                ))
            
            db.add_all(sections)
            
            # Update project status to IN_PROGRESS
            project.status = ProjectStatus.IN_PROGRESS
            
            await db.commit()
            await db.refresh(project)
            
            # Get all sections for response
            sections_result = await db.execute(
                select(Section)
                .where(Section.project_id == project_id)
                .order_by(Section.form_section_number)
            )
            all_sections = sections_result.scalars().all()
            
            # Build response
            response_data = {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "status": project.status,
                "current_section": project.current_section,
                "total_sections": project.total_sections,
                "completed_sections": project.completed_sections,
                "org_id": project.org_id,
                "user_id": project.user_id,
                "created_at": project.created_at,
                "updated_at": project.updated_at,
                "sections": [SectionResponse.model_validate(section) for section in all_sections]
            }
            
            logger.info(f"Successfully started project {project_id} with 27 sections")
            return ProjectStartResponse(**response_data)
            
        except Exception as e:
            logger.error(f"Error starting project {project_id}: {str(e)}")
            raise
    
    async def generate_project_report(
        self,
        project_id: str,
        db: AsyncSession
    ) -> ProjectReportResponse:
        """
        Generate a comprehensive report for a project.
        
        Args:
            project_id: The project ID
            db: Database session
            
        Returns:
            ProjectReportResponse containing the complete report
            
        Raises:
            ValueError: If project not found
            RuntimeError: If database operations fail
        """
        try:
            # Step 1: Get project details
            project = await self._get_project_by_id(project_id, db)
            
            # Step 2: Get all completed sections
            completed_sections = await self._get_completed_sections(project_id, db)
            
            # Step 3: Format report data
            sections_data = await self._format_report_sections(
                project.total_sections, completed_sections
            )
            
            # Step 4: Create report response
            report = ProjectReportResponse(
                project_id=project_id,
                project_name=project.name,
                project_status=project.status,
                total_sections=project.total_sections,
                completed_sections=project.completed_sections,
                generated_at=datetime.utcnow(),
                sections=sections_data
            )
            
            logger.info(f"Successfully generated report for project {project_id}")
            return report
            
        except Exception as e:
            logger.error(f"Error generating report for project {project_id}: {str(e)}")
            raise
    
    async def _get_project_by_id(
        self,
        project_id: str,
        db: AsyncSession
    ) -> Project:
        """
        Get project by ID.
        
        Args:
            project_id: The project ID
            db: Database session
            
        Returns:
            Project object
            
        Raises:
            ValueError: If project not found
        """
        result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        
        if not project:
            raise ValueError(f"Project with ID {project_id} not found")
        
        return project
    
    async def _get_completed_sections(
        self,
        project_id: str,
        db: AsyncSession
    ) -> List[Section]:
        """
        Get all completed sections for a project.
        
        Args:
            project_id: The project ID
            db: Database session
            
        Returns:
            List of completed Section objects
        """
        try:
            result = await db.execute(
                select(Section)
                .where(
                    Section.project_id == project_id,
                    Section.status == SectionStatus.COMPLETED
                )
                .order_by(Section.form_section_number)
            )
            sections = result.scalars().all()
            
            logger.debug(f"Found {len(sections)} completed sections for project {project_id}")
            return sections
            
        except Exception as e:
            logger.error(f"Error retrieving completed sections for project {project_id}: {str(e)}")
            return []
    
    async def _format_report_sections(
        self,
        total_sections: int,
        completed_sections: List[Section]
    ) -> Dict[str, SectionReportData]:
        """
        Format sections data for the report response.
        
        Args:
            total_sections: Total number of sections in the project
            completed_sections: List of completed sections
            
        Returns:
            Dictionary with section keys and SectionReportData values
        """
        sections_data = {}
        
        # Create a mapping of form section numbers to completed sections
        completed_map = {section.form_section_number: section for section in completed_sections}
        
        # Generate data for all sections (3.01 to 3.27)
        for section_num in range(1, total_sections + 1):
            form_section_num = f"3.{section_num:02d}"
            section_key = f"section_{section_num}"
            
            if form_section_num in completed_map:
                # Section is completed
                completed_section = completed_map[form_section_num]
                sections_data[section_key] = SectionReportData(
                    form_section_number=form_section_num,
                    final_output=completed_section.final_output,
                    completed=True
                )
            else:
                # Section is not completed
                sections_data[section_key] = SectionReportData(
                    form_section_number=form_section_num,
                    final_output=None,
                    completed=False
                )
        
        return sections_data
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the project service.
        
        Returns:
            Dict containing health status information
        """
        try:
            return {
                "status": "healthy",
                "service": "project_service"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "service": "project_service"
            }
