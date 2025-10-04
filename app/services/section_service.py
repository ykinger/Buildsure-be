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
from app.models.ontario_chunk import OntarioChunk
from app.models.answer import Answer
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)

class SectionService:
    """Service for managing section operations and business logic."""
    
    def __init__(self):
        pass  # No longer instantiate AIService here
    
    async def start_section(
        self,
        section_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Start a section by validating, updating status, and generating the first question.
        
        Args:
            section_id: The section ID to start
            db: Database session
            
        Returns:
            Dict containing the generated question and section info
            
        Raises:
            ValueError: If validation fails
            RuntimeError: If database operations fail
        """
        try:
            # Step 1: Validate the section can be started
            section = await self._validate_section_start(section_id, db)
            
            # Step 2: Update section status to 'in_progress'
            await self._update_section_status(section, SectionStatus.IN_PROGRESS, db)
            
            # Step 3: Retrieve relevant ontario chunks
            ontario_chunks = await self._get_relevant_guidelines(
                section.section_number, db
            )
            
            # Step 4: Generate the first question using AI
            ai_service = AIService(db)
            question_data = await ai_service.generate_question(
                section_number=section.section_number,
                ontario_chunks=ontario_chunks,
                form_questions_and_answers=[],  # Empty for first question
                clarifying_questions_and_answers=[]  # Empty for first question
            )
            
            # Step 5: Prepare the response
            response = {
                "section_id": section.id,
                "form_section_number": section.form_section_number,
                "status": SectionStatus.IN_PROGRESS.value,
                "question": question_data,
                "guidelines_found": len(ontario_chunks),
                "message": f"Section {section.form_section_number} started successfully"
            }
            
            logger.info(f"Successfully started section {section.form_section_number} (ID: {section.id})")
            return response
            
        except Exception as e:
            logger.error(f"Error starting section {section_id}: {str(e)}")
            # Rollback any changes if needed
            await db.rollback()
            raise
    
    async def _validate_section_start(
        self,
        section_id: str,
        db: AsyncSession
    ) -> Section:
        """
        Validate that the section can be started.
        
        Args:
            section_id: The section ID
            db: Database session
            
        Returns:
            The section object
            
        Raises:
            ValueError: If validation fails
        """
        # Check if section exists
        section_result = await db.execute(
            select(Section).where(Section.id == section_id)
        )
        section = section_result.scalar_one_or_none()
        
        if not section:
            raise ValueError(f"Section with ID {section_id} not found")
        
        # Check if section is in the correct state to be started
        if section.status != SectionStatus.READY_TO_START:
            if section.status == SectionStatus.PENDING:
                raise ValueError(
                    f"Section {section.form_section_number} is not ready to start. "
                    f"Complete the previous section first."
                )
            elif section.status == SectionStatus.IN_PROGRESS:
                raise ValueError(
                    f"Section {section.form_section_number} is already in progress"
                )
            elif section.status == SectionStatus.COMPLETED:
                raise ValueError(
                    f"Section {section.form_section_number} is already completed"
                )
            else:
                raise ValueError(
                    f"Section {section.form_section_number} cannot be started. "
                    f"Current status: {section.status.value}"
                )
        
        return section
    
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
            
            logger.debug(f"Updated section {section.form_section_number} status to {new_status.value}")
            
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
        Retrieve relevant OBC chunks for the given section.
        
        Args:
            section_number: The section number
            db: Database session
            limit: Maximum number of chunks to retrieve
            
        Returns:
            List of OBC chunk dictionaries
        """
        try:
            # Query for OBC chunks that might be relevant to this section
            # Get articles from Division B (Acceptable Solutions) as they contain the most detailed guidance
            
            result = await db.execute(
                select(OntarioChunk)
                .where(OntarioChunk.division == "Division B")
                .where(OntarioChunk.chunk_type == "article")
                .order_by(OntarioChunk.reference)
                .limit(limit)
            )
            chunks = result.scalars().all()
            
            # Convert to dictionaries for AI service (matching expected format)
            guideline_data = []
            for chunk in chunks:
                guideline_data.append({
                    "section_reference": chunk.reference,
                    "section_title": chunk.title,
                    "section_level": 4,  # Articles are level 4 in hierarchy
                    "chunk_text": chunk.content
                })
            
            logger.debug(f"Retrieved {len(guideline_data)} OBC chunks for section {section_number}")
            return guideline_data
            
        except Exception as e:
            logger.error(f"Error retrieving OBC chunks for section {section_number}: {str(e)}")
            # Return empty list if retrieval fails
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
                "draft_output": section.draft_output,
                "final_output": section.final_output,
                "created_at": section.created_at.isoformat() if section.created_at else None,
                "updated_at": section.updated_at.isoformat() if section.updated_at else None
            }
            
        except Exception as e:
            logger.error(f"Error getting section status: {str(e)}")
            raise
    
    async def process_section_answer(
        self,
        project_id: str,
        section_number: int,
        question_text: str,
        answer_text: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Process a section answer and determine next step.
        
        Args:
            project_id: The project ID
            section_number: The section number
            question_text: The question that was answered
            answer_text: The user's answer
            db: Database session
            
        Returns:
            Dict containing next_question or draft_output
            
        Raises:
            ValueError: If validation fails
            RuntimeError: If processing fails
        """
        try:
            # Step 1: Validate section exists and is in progress
            section = await self._validate_section_answer(
                project_id, section_number, db
            )
            
            # Step 2: Save the answer to the answers table
            answer = await self._save_answer(
                section.id, question_text, answer_text, db
            )
            
            # Step 3: Retrieve all previous answers for this section
            previous_answers = await self._get_section_answers(section.id, db)
            
            # Step 4: Get relevant ontario chunks
            ontario_chunks = await self._get_relevant_guidelines(
                section_number, db
            )
            
            # Step 5: Call AI service to determine next step
            ai_service = AIService(db)
            ai_result = await ai_service.process_answer_and_generate_next(
                section_number=section_number,
                current_question=question_text,
                current_answer=answer_text,
                previous_answers=previous_answers,
                ontario_chunks=ontario_chunks
            )
            
            # Step 6: Handle the AI result
            response = await self._handle_ai_result(
                section, ai_result, len(previous_answers), db
            )
            
            logger.info(f"Successfully processed answer for section {section_number}")
            return response
            
        except Exception as e:
            logger.error(f"Error processing answer for section {section_number}: {str(e)}")
            await db.rollback()
            raise
    
    async def _validate_section_answer(
        self,
        project_id: str,
        section_number: int,
        db: AsyncSession
    ) -> Section:
        """
        Validate that the section exists and is in progress.
        
        Args:
            project_id: The project ID
            section_number: The section number
            db: Database session
            
        Returns:
            The section object
            
        Raises:
            ValueError: If validation fails
        """
        # Check if section exists and is in progress
        result = await db.execute(
            select(Section).where(
                Section.project_id == project_id,
                Section.section_number == section_number
            )
        )
        section = result.scalar_one_or_none()
        
        if not section:
            raise ValueError(
                f"Section {section_number} not found for project {project_id}"
            )
        
        if section.status != SectionStatus.IN_PROGRESS:
            raise ValueError(
                f"Section {section_number} is not in progress. Current status: {section.status.value}"
            )
        
        return section
    
    async def _save_answer(
        self,
        section_id: str,
        question_text: str,
        answer_text: str,
        db: AsyncSession
    ) -> Answer:
        """
        Save an answer to the database.
        
        Args:
            section_id: The section ID
            question_text: The question text
            answer_text: The answer text
            db: Database session
            
        Returns:
            The created answer object
        """
        try:
            answer = Answer(
                section_id=section_id,
                question_text=question_text,
                answer_text=answer_text,
                question_type="clarifying"
            )
            
            db.add(answer)
            await db.commit()
            await db.refresh(answer)
            
            logger.debug(f"Saved answer for section {section_id}")
            return answer
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to save answer: {str(e)}")
            raise RuntimeError(f"Failed to save answer: {str(e)}")
    
    async def _get_section_answers(
        self,
        section_id: str,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all answers for a section.
        
        Args:
            section_id: The section ID
            db: Database session
            
        Returns:
            List of answer dictionaries
        """
        try:
            result = await db.execute(
                select(Answer)
                .where(Answer.section_id == section_id)
                .order_by(Answer.created_at)
            )
            answers = result.scalars().all()
            
            # Convert to dictionaries
            answer_data = []
            for answer in answers:
                answer_data.append({
                    "id": answer.id,
                    "question_text": answer.question_text,
                    "answer_text": answer.answer_text,
                    "question_type": answer.question_type,
                    "created_at": answer.created_at.isoformat() if answer.created_at else None
                })
            
            return answer_data
            
        except Exception as e:
            logger.error(f"Error retrieving answers for section {section_id}: {str(e)}")
            return []
    
    async def _handle_ai_result(
        self,
        section: Section,
        ai_result: Dict[str, Any],
        answers_count: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Handle the AI service result and update section if needed.
        
        Args:
            section: The section object
            ai_result: Result from AI service
            answers_count: Number of answers for this section
            db: Database session
            
        Returns:
            Response dictionary
        """
        try:
            action = ai_result.get("action", "question")
            
            if action == "draft":
                # Update section with draft output
                draft_output = ai_result.get("draft_output")
                section.draft_output = draft_output
                db.add(section)
                await db.commit()
                await db.refresh(section)
                
                return {
                    "section_id": section.id,
                    "section_number": section.section_number,
                    "status": section.status.value,
                    "next_question": None,
                    "draft_output": draft_output,
                    "message": f"Draft generated for section {section.section_number}",
                    "answers_count": answers_count
                }
            else:
                # Return next question
                next_question = ai_result.get("next_question")
                
                return {
                    "section_id": section.id,
                    "section_number": section.section_number,
                    "status": section.status.value,
                    "next_question": next_question,
                    "draft_output": None,
                    "message": f"Next question generated for section {section.section_number}",
                    "answers_count": answers_count
                }
                
        except Exception as e:
            logger.error(f"Error handling AI result: {str(e)}")
            raise RuntimeError(f"Error handling AI result: {str(e)}")
    
    async def confirm_section(
        self,
        project_id: str,
        section_number: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Confirm a section by saving draft as final output and updating project progress.
        
        Args:
            project_id: The project ID
            section_number: The section number to confirm
            db: Database session
            
        Returns:
            Dict containing confirmation details and updated project status
            
        Raises:
            ValueError: If validation fails
            RuntimeError: If database operations fail
        """
        try:
            # Step 1: Validate the section can be confirmed
            project, section = await self._validate_section_confirm(
                project_id, section_number, db
            )
            
            # Step 2: Save draft_output as final_output and mark section as completed
            await self._finalize_section(section, db)
            
            # Step 3: Update project progress
            updated_project = await self._update_project_progress(project, db)
            
            # Step 4: Prepare the response
            response = {
                "section_id": section.id,
                "section_number": section.section_number,
                "status": SectionStatus.COMPLETED.value,
                "final_output": section.final_output,
                "project_id": project_id,
                "project_status": updated_project.status.value,
                "completed_sections": updated_project.completed_sections,
                "total_sections": updated_project.total_sections,
                "current_section": updated_project.current_section,
                "message": f"Section {section_number} confirmed successfully"
            }
            
            logger.info(f"Successfully confirmed section {section_number} for project {project_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error confirming section {section_number} for project {project_id}: {str(e)}")
            # Rollback any changes if needed
            await db.rollback()
            raise
    
    async def _validate_section_confirm(
        self,
        project_id: str,
        section_number: int,
        db: AsyncSession
    ) -> tuple[Project, Section]:
        """
        Validate that the section can be confirmed.
        
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
                f"Cannot confirm section {section_number}. "
                f"Current section is {project.current_section}"
            )
        
        # Check if section is in progress
        if section.status != SectionStatus.IN_PROGRESS:
            raise ValueError(
                f"Section {section_number} is not in progress. "
                f"Current status: {section.status.value}"
            )
        
        # Check if section has draft_output to confirm
        if not section.draft_output:
            raise ValueError(
                f"Section {section_number} has no draft output to confirm"
            )
        
        return project, section
    
    async def _finalize_section(
        self,
        section: Section,
        db: AsyncSession
    ) -> None:
        """
        Finalize the section by copying draft to final output and marking as completed.
        
        Args:
            section: The section to finalize
            db: Database session
        """
        try:
            # Copy draft_output to final_output
            section.final_output = section.draft_output
            
            # Mark section as completed
            section.status = SectionStatus.COMPLETED
            
            db.add(section)
            await db.commit()
            await db.refresh(section)
            
            logger.debug(f"Finalized section {section.section_number}")
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to finalize section: {str(e)}")
            raise RuntimeError(f"Failed to finalize section: {str(e)}")
    
    async def _update_project_progress(
        self,
        project: Project,
        db: AsyncSession
    ) -> Project:
        """
        Update project progress after section confirmation.
        
        Args:
            project: The project to update
            db: Database session
            
        Returns:
            Updated project object
        """
        try:
            # Import here to avoid circular imports
            from app.models.project import ProjectStatus
            
            # Increment completed sections
            project.completed_sections += 1
            
            # Advance current section
            project.current_section += 1
            
            # Set the next section to READY_TO_START if it exists and is currently PENDING
            if project.current_section <= project.total_sections:
                next_section_result = await db.execute(
                    select(Section).where(
                        Section.project_id == project.id,
                        Section.section_number == project.current_section
                    )
                )
                next_section = next_section_result.scalar_one_or_none()
                
                if next_section and next_section.status == SectionStatus.PENDING:
                    next_section.status = SectionStatus.READY_TO_START
                    db.add(next_section)
                    logger.debug(f"Set section {project.current_section} to READY_TO_START")
            
            # Check if all sections are completed
            if project.completed_sections >= project.total_sections:
                project.status = ProjectStatus.COMPLETED
                logger.info(f"Project {project.id} completed - all sections finished")
            elif project.status == ProjectStatus.NOT_STARTED:
                # If project was not started, mark it as in progress
                project.status = ProjectStatus.IN_PROGRESS
            
            db.add(project)
            await db.commit()
            await db.refresh(project)
            
            logger.debug(f"Updated project progress: {project.completed_sections}/{project.total_sections}")
            return project
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to update project progress: {str(e)}")
            raise RuntimeError(f"Failed to update project progress: {str(e)}")

    async def health_check(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Check the health of the section service and its dependencies.
        
        Args:
            db: Database session
            
        Returns:
            Dict containing health status information
        """
        try:
            # Check AI service health
            ai_service = AIService(db)
            ai_health = ai_service.health_check()
            
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
