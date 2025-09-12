"""
Section Service Module
Handles section-related business logic and orchestration.
"""
import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.project import Project
from app.models.section import Section, SectionStatus
from app.models.guideline_chunk import GuidelineChunk
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)

class SectionService:
    """Service for managing section operations and business logic."""
    
    def __init__(self):
        self.ai_service = AIService()
    
    async def start_section(
        self,
        project_id: str,
        section_number: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Start a section by validating, updating status, and generating the first question.
        
        Args:
            project_id: The project ID
            section_number: The section number to start
            db: Database session
            
        Returns:
            Dict containing the generated question and section info
            
        Raises:
            ValueError: If validation fails
            RuntimeError: If database operations fail
        """
        try:
            # Step 1: Validate the section can be started
            project, section = await self._validate_section_start(
                project_id, section_number, db
            )
            
            # Step 2: Update section status to 'in_progress'
            await self._update_section_status(section, SectionStatus.IN_PROGRESS, db)
            
            # Step 3: Retrieve relevant guideline chunks
            guideline_chunks = await self._get_relevant_guidelines(
                section_number, db
            )
            
            # Step 4: Generate the first question using AI
            question_data = await self.ai_service.generate_question(
                section_number=section_number,
                guideline_chunks=guideline_chunks,
                form_questions_and_answers=[],  # Empty for first question
                clarifying_questions_and_answers=[]  # Empty for first question
            )
            
            # Step 5: Prepare the response
            response = {
                "project_id": project_id,
                "section_number": section_number,
                "section_status": SectionStatus.IN_PROGRESS.value,
                "question": question_data,
                "guidelines_found": len(guideline_chunks),
                "message": f"Section {section_number} started successfully"
            }
            
            logger.info(f"Successfully started section {section_number} for project {project_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error starting section {section_number} for project {project_id}: {str(e)}")
            # Rollback any changes if needed
            await db.rollback()
            raise
    
    async def _validate_section_start(
        self,
        project_id: str,
        section_number: int,
        db: AsyncSession
    ) -> tuple[Project, Section]:
        """
        Validate that the section can be started.
        
        Args:
            project_id: The project ID
            section_number: The section number
            db: Database session
            
        Returns:
            Tuple of (project, section)
            
        Raises:
            ValueError: If validation fails
        """
        # Check if project exists
        project_result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = project_result.scalar_one_or_none()
        
        if not project:
            raise ValueError(f"Project with ID {project_id} not found")
        
        # Check if section exists for this project
        section_result = await db.execute(
            select(Section).where(
                Section.project_id == project_id,
                Section.section_number == section_number
            )
        )
        section = section_result.scalar_one_or_none()
        
        if not section:
            raise ValueError(
                f"Section {section_number} not found for project {project_id}"
            )
        
        # Validate that this section matches the project's current section
        if project.current_section != section_number:
            raise ValueError(
                f"Cannot start section {section_number}. "
                f"Current section is {project.current_section}"
            )
        
        # Check if section is already in progress or completed
        if section.status == SectionStatus.IN_PROGRESS:
            raise ValueError(
                f"Section {section_number} is already in progress"
            )
        elif section.status == SectionStatus.COMPLETED:
            raise ValueError(
                f"Section {section_number} is already completed"
            )
        
        return project, section
    
    async def _update_section_status(
        self,
        section: Section,
        new_status: SectionStatus,
        db: AsyncSession
    ) -> None:
        """
        Update the section status in the database.
        
        Args:
            section: The section to update
            new_status: The new status
            db: Database session
        """
        try:
            section.status = new_status
            db.add(section)
            await db.commit()
            await db.refresh(section)
            
            logger.debug(f"Updated section {section.section_number} status to {new_status.value}")
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to update section status: {str(e)}")
            raise RuntimeError(f"Failed to update section status: {str(e)}")
    
    async def _get_relevant_guidelines(
        self,
        section_number: int,
        db: AsyncSession,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant guideline chunks for the given section.
        
        Args:
            section_number: The section number
            db: Database session
            limit: Maximum number of chunks to retrieve
            
        Returns:
            List of guideline chunk dictionaries
        """
        try:
            # Query for guideline chunks that might be relevant to this section
            # For now, we'll get a general set of chunks
            # In the future, this could be enhanced with semantic search or section mapping
            
            result = await db.execute(
                select(GuidelineChunk)
                .order_by(GuidelineChunk.section_reference)
                .limit(limit)
            )
            chunks = result.scalars().all()
            
            # Convert to dictionaries for AI service
            guideline_data = []
            for chunk in chunks:
                guideline_data.append({
                    "section_reference": chunk.section_reference,
                    "section_title": chunk.section_title,
                    "section_level": chunk.section_level,
                    "chunk_text": chunk.chunk_text
                })
            
            logger.debug(f"Retrieved {len(guideline_data)} guideline chunks for section {section_number}")
            return guideline_data
            
        except Exception as e:
            logger.error(f"Error retrieving guidelines for section {section_number}: {str(e)}")
            # Return empty list if guideline retrieval fails
            return []
    
    async def get_section_status(
        self,
        project_id: str,
        section_number: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Get the current status of a section.
        
        Args:
            project_id: The project ID
            section_number: The section number
            db: Database session
            
        Returns:
            Dict containing section status information
        """
        try:
            result = await db.execute(
                select(Section).where(
                    Section.project_id == project_id,
                    Section.section_number == section_number
                )
            )
            section = result.scalar_one_or_none()
            
            if not section:
                raise ValueError(f"Section {section_number} not found for project {project_id}")
            
            return {
                "project_id": project_id,
                "section_number": section_number,
                "status": section.status.value,
                "user_input": section.user_input,
                "draft_output": section.draft_output,
                "final_output": section.final_output,
                "created_at": section.created_at.isoformat() if section.created_at else None,
                "updated_at": section.updated_at.isoformat() if section.updated_at else None
            }
            
        except Exception as e:
            logger.error(f"Error getting section status: {str(e)}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the section service and its dependencies.
        
        Returns:
            Dict containing health status information
        """
        try:
            # Check AI service health
            ai_health = self.ai_service.health_check()
            
            return {
                "status": "healthy" if ai_health["status"] == "healthy" else "degraded",
                "ai_service": ai_health,
                "service": "section_service"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "service": "section_service"
            }
