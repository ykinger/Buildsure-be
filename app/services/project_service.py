"""
Project Service Module
Handles project-related business logic and orchestration.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.project import Project, ProjectStatus
from app.schemas.project import ProjectReportResponse, SectionReportData, ProjectStartResponse
from app.models.data_matrix import DataMatrix
from app.models.project_data_matrix import ProjectDataMatrix, PDMStatus
from app.repository.data_matrix import list_data_matrices
from app.repository.project import get_project_details_by_id
from app.repository.project_data_matrix import (
    create_project_data_matrix,
    find_next_pending_pdm,
    update_pdm_status
)

logger = logging.getLogger(__name__)


class ProjectService:
    """Service for managing project operations and business logic."""

    async def start_project(
        self,
        project_id: str,
        db: AsyncSession
    ) -> ProjectStartResponse:
        """
        Start a project by updating project status and creating project_data_matrix rows.

        Args:
            project_id: The project ID
            db: Database session

        Returns:
            ProjectStartResponse containing basic project details

        Raises:
            ValueError: If project not found
            RuntimeError: If database operations fail
        """
        try:
            # Get project
            project = await self._get_project_by_id(project_id, db)

            # Update project status to IN_PROGRESS
            project.status = ProjectStatus.IN_PROGRESS

            await db.commit()
            await db.refresh(project)

            # Pre-populate project data matrix
            await self._pre_populate_data_matrix(project.id, db)

            # Set the first section to ready to start
            next_pdm = await find_next_pending_pdm(project.id, db)
            if next_pdm:
                await update_pdm_status(next_pdm, PDMStatus.READY_TO_START, db)

            # Fetch the fully detailed project response
            project = await get_project_details_by_id(project_id, db)

            # Build response
            response_data = {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "status": project.status,
                "organization_id": project.organization_id,
                "user_id": project.user_id,
                "created_at": project.created_at,
                "updated_at": project.updated_at,
            }

            logger.info(f"Successfully started project {project_id}")
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
            # Using 27 as the default total sections (3.01 to 3.27)
            sections_data = await self._format_report_sections(
                27, completed_sections
            )

            # Step 4: Create report response
            report = ProjectReportResponse(
                project_id=project_id,
                project_name=project.name,
                project_status=project.status,
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
    ) -> List[Any]: # Changed to Any as Section is removed
        """
        Get all completed sections for a project.

        Args:
            project_id: The project ID
            db: Database session

        Returns:
            List of completed Section objects
        """
        logger.debug(f"Sections are no longer managed directly by ProjectService. Returning empty list for project {project_id}")
        return []

    async def _format_report_sections(
        self,
        total_sections: int,
        completed_sections: List[Any] # Changed to Any as Section is removed
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

        # Generate data for all sections (3.01 to 3.27)
        for section_num in range(1, total_sections + 1):
            form_section_num = f"3.{section_num:02d}"
            section_key = f"section_{section_num}"

            sections_data[section_key] = SectionReportData(
                form_section_number=form_section_num,
                final_output=None,
                completed=False
            )

        return sections_data

    async def _pre_populate_data_matrix(
        self,
        project_id: str,
        db: AsyncSession
    ) -> None:
        """
        Copies all records from the `data_matrix` table to the `project_data_matrix` table
        for a given project, filling the project_id and other fields accordingly.
        - Checks for existing rows to avoid duplicates
        - Sets status=PENDING for all rows except number "3.00" which is IN_PROGRESS

        Args:
            project_id: The ID of the project to pre-populate data for.
            db: The database session.
        """
        # Check if already populated to avoid duplicates
        existing = await db.execute(
            select(ProjectDataMatrix).where(ProjectDataMatrix.project_id == project_id)
        )
        if existing.scalars().first():
            logger.info(f"Project {project_id} already has project_data_matrix rows, skipping")
            return

        # Get all data matrices
        data_matrices = await list_data_matrices(session=db)

        # Create project_data_matrix rows
        for dm in data_matrices:
            # Set READY_TO_START for number "3.00", PENDING for others
            status = PDMStatus.READY_TO_START if dm.number == "3.00" else PDMStatus.PENDING

            pdm = ProjectDataMatrix(
                project_id=project_id,
                data_matrix_id=dm.id,
                status=status,
                output=None
            )
            db.add(pdm)

        await db.commit()
        logger.info(f"Successfully pre-populated {len(data_matrices)} project_data_matrix rows for project {project_id}")

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
