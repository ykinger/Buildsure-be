"""
Section Service Module
Handles section-related business logic and orchestration for the new schema.
"""
import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from enum import Enum

from app.models.project import Project
from app.models.project_data_matrix import ProjectDataMatrix
from app.models.data_matrix import DataMatrix
from app.models.knowledge_base import KnowledgeBase
from app.models.data_matrix_knowledge_base import DataMatrixKnowledgeBase
from app.models.message import Message
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)

class ProjectDataMatrixStatus(str, Enum):
    """Status enum for ProjectDataMatrix sections"""
    PENDING = "pending"
    READY_TO_START = "ready_to_start"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class SectionService:
    """Service for managing section operations and business logic."""

    def __init__(self):
        pass  # No longer instantiate AIService here

    async def start_section(
        self,
        project_data_matrix_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Start a section by validating, updating status, and generating the first question.

        Args:
            project_data_matrix_id: The ProjectDataMatrix ID to start
            db: Database session

        Returns:
            Dict containing the generated question and section info

        Raises:
            ValueError: If validation fails
            RuntimeError: If database operations fail
        """
        try:
            # Step 1: Validate the section can be started
            project_data_matrix = await self._validate_section_start(project_data_matrix_id, db)

            # Step 2: Update section status to 'in_progress'
            await self._update_section_status(project_data_matrix, ProjectDataMatrixStatus.IN_PROGRESS, db)

            # Step 3: Retrieve relevant knowledge base content
            knowledge_base_content = await self._get_relevant_guidelines(project_data_matrix.data_matrix_id, db)

            # Step 4: Generate the first question using AI
            ai_service = AIService(db)
            question_data = await ai_service.generate_question(
                section_number=project_data_matrix.data_matrix_id,
                ontario_chunks=knowledge_base_content,
                form_questions_and_answers=[],  # Empty for first question
                clarifying_questions_and_answers=[]  # Empty for first question
            )

            # Step 5: Prepare the response
            response = {
                "project_data_matrix_id": project_data_matrix.id,
                "status": ProjectDataMatrixStatus.IN_PROGRESS.value,
                "question": question_data,
                "guidelines_found": len(knowledge_base_content),
                "message": f"Section started successfully"
            }

            logger.info(f"Successfully started section (ID: {project_data_matrix.id})")
            return response

        except Exception as e:
            logger.error(f"Error starting section {project_data_matrix_id}: {str(e)}")
            # Rollback any changes if needed
            await db.rollback()
            raise

    async def _validate_section_start(
        self,
        project_data_matrix_id: str,
        db: AsyncSession
    ) -> ProjectDataMatrix:
        """
        Validate that the section can be started.

        Args:
            project_data_matrix_id: The ProjectDataMatrix ID
            db: Database session

        Returns:
            The ProjectDataMatrix object

        Raises:
            ValueError: If validation fails
        """
        # Check if section exists
        result = await db.execute(
            select(ProjectDataMatrix).where(ProjectDataMatrix.id == project_data_matrix_id)
        )
        project_data_matrix = result.scalar_one_or_none()

        if not project_data_matrix:
            raise ValueError(f"Section with ID {project_data_matrix_id} not found")

        # Check if section is in the correct state to be started
        if project_data_matrix.status != ProjectDataMatrixStatus.READY_TO_START:
            if project_data_matrix.status == ProjectDataMatrixStatus.PENDING:
                raise ValueError(
                    f"Section is not ready to start. Complete the previous section first."
                )
            elif project_data_matrix.status == ProjectDataMatrixStatus.IN_PROGRESS:
                raise ValueError(
                    f"Section is already in progress"
                )
            elif project_data_matrix.status == ProjectDataMatrixStatus.COMPLETED:
                raise ValueError(
                    f"Section is already completed"
                )
            else:
                raise ValueError(
                    f"Section cannot be started. Current status: {project_data_matrix.status}"
                )

        return project_data_matrix

    async def _update_section_status(
        self,
        project_data_matrix: ProjectDataMatrix,
        new_status: ProjectDataMatrixStatus,
        db: AsyncSession
    ) -> None:
        """
        Update the section status in the database.

        Args:
            project_data_matrix: The section to update
            new_status: The new status
            db: Database session
        """
        try:
            project_data_matrix.status = new_status
            db.add(project_data_matrix)
            await db.commit()
            await db.refresh(project_data_matrix)

            logger.debug(f"Updated section status to {new_status.value}")

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to update section status: {str(e)}")
            raise RuntimeError(f"Failed to update section status: {str(e)}")

    async def _get_relevant_guidelines(
        self,
        data_matrix_id: str,
        db: AsyncSession,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant knowledge base content for the given data matrix.

        Args:
            data_matrix_id: The data matrix ID
            db: Database session
            limit: Maximum number of chunks to retrieve

        Returns:
            List of knowledge base content dictionaries
        """
        try:
            # Query for knowledge base content via the junction table
            result = await db.execute(
                select(KnowledgeBase)
                .join(DataMatrixKnowledgeBase, KnowledgeBase.id == DataMatrixKnowledgeBase.knowledge_base_id)
                .where(DataMatrixKnowledgeBase.data_matrix_id == data_matrix_id)
                .limit(limit)
            )
            knowledge_base_items = result.scalars().all()

            # Convert to dictionaries for AI service (matching expected format)
            guideline_data = []
            for item in knowledge_base_items:
                guideline_data.append({
                    "section_reference": item.reference,
                    "section_title": item.reference,  # Using reference as title
                    "section_level": 4,  # Default level
                    "chunk_text": item.content
                })

            logger.debug(f"Retrieved {len(guideline_data)} knowledge base items for data matrix {data_matrix_id}")
            return guideline_data

        except Exception as e:
            logger.error(f"Error retrieving knowledge base content for data matrix {data_matrix_id}: {str(e)}")
            # Return empty list if retrieval fails
            return []

    async def get_section_status(
        self,
        project_data_matrix_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Get the current status of a section.

        Args:
            project_data_matrix_id: The ProjectDataMatrix ID
            db: Database session

        Returns:
            Dict containing section status information
        """
        try:
            result = await db.execute(
                select(ProjectDataMatrix).where(ProjectDataMatrix.id == project_data_matrix_id)
            )
            project_data_matrix = result.scalar_one_or_none()

            if not project_data_matrix:
                raise ValueError(f"Section with ID {project_data_matrix_id} not found")

            return {
                "project_data_matrix_id": project_data_matrix_id,
                "status": project_data_matrix.status,
                "output": project_data_matrix.output,
                "created_at": project_data_matrix.created_at.isoformat() if project_data_matrix.created_at else None,
                "updated_at": project_data_matrix.updated_at.isoformat() if project_data_matrix.updated_at else None
            }

        except Exception as e:
            logger.error(f"Error getting section status: {str(e)}")
            raise

    async def process_section_answer(
        self,
        project_data_matrix_id: str,
        question_text: str,
        answer_text: str,
        user_id: Optional[str] = None,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """
        Process a section answer and determine next step.

        Args:
            project_data_matrix_id: The ProjectDataMatrix ID
            question_text: The question that was answered
            answer_text: The user's answer
            user_id: Optional user ID who provided the answer
            db: Database session

        Returns:
            Dict containing next_question or draft_output

        Raises:
            ValueError: If validation fails
            RuntimeError: If processing fails
        """
        try:
            # Step 1: Validate section exists and is in progress
            project_data_matrix = await self._validate_section_answer(project_data_matrix_id, db)

            # Step 2: Save the answer as a message
            await self._save_message(project_data_matrix_id, user_id, "user", answer_text, db)

            # Step 3: Retrieve all previous messages for this section
            previous_messages = await self._get_section_messages(project_data_matrix_id, db)

            # Step 4: Get relevant knowledge base content
            knowledge_base_content = await self._get_relevant_guidelines(project_data_matrix.data_matrix_id, db)

            # Step 5: Call AI service to determine next step
            ai_service = AIService(db)
            ai_result = await ai_service.process_answer_and_generate_next(
                section_number=project_data_matrix.data_matrix_id,
                current_question=question_text,
                current_answer=answer_text,
                previous_answers=previous_messages,
                ontario_chunks=knowledge_base_content
            )

            # Step 6: Handle the AI result
            response = await self._handle_ai_result(
                project_data_matrix, ai_result, len(previous_messages), db
            )

            logger.info(f"Successfully processed answer for section {project_data_matrix_id}")
            return response

        except Exception as e:
            logger.error(f"Error processing answer for section {project_data_matrix_id}: {str(e)}")
            await db.rollback()
            raise

    async def _validate_section_answer(
        self,
        project_data_matrix_id: str,
        db: AsyncSession
    ) -> ProjectDataMatrix:
        """
        Validate that the section exists and is in progress.

        Args:
            project_data_matrix_id: The ProjectDataMatrix ID
            db: Database session

        Returns:
            The ProjectDataMatrix object

        Raises:
            ValueError: If validation fails
        """
        # Check if section exists and is in progress
        result = await db.execute(
            select(ProjectDataMatrix).where(ProjectDataMatrix.id == project_data_matrix_id)
        )
        project_data_matrix = result.scalar_one_or_none()

        if not project_data_matrix:
            raise ValueError(f"Section with ID {project_data_matrix_id} not found")

        if project_data_matrix.status != ProjectDataMatrixStatus.IN_PROGRESS:
            raise ValueError(
                f"Section is not in progress. Current status: {project_data_matrix.status}"
            )

        return project_data_matrix

    async def _save_message(
        self,
        project_data_matrix_id: str,
        user_id: Optional[str],
        role: str,
        content: str,
        db: AsyncSession
    ) -> Message:
        """
        Save a message to the database.

        Args:
            project_data_matrix_id: The ProjectDataMatrix ID
            user_id: Optional user ID
            role: The message role (user, assistant, system)
            content: The message content
            db: Database session

        Returns:
            The created message object
        """
        try:
            message = Message(
                project_data_matrix_id=project_data_matrix_id,
                user_id=user_id,
                role=role,
                content=content
            )

            db.add(message)
            await db.commit()
            await db.refresh(message)

            logger.debug(f"Saved message for section {project_data_matrix_id}")
            return message

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to save message: {str(e)}")
            raise RuntimeError(f"Failed to save message: {str(e)}")

    async def _get_section_messages(
        self,
        project_data_matrix_id: str,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all messages for a section.

        Args:
            project_data_matrix_id: The ProjectDataMatrix ID
            db: Database session

        Returns:
            List of message dictionaries
        """
        try:
            result = await db.execute(
                select(Message)
                .where(Message.project_data_matrix_id == project_data_matrix_id)
                .order_by(Message.created_at)
            )
            messages = result.scalars().all()

            # Convert to dictionaries
            message_data = []
            for message in messages:
                message_data.append({
                    "id": message.id,
                    "role": message.role,
                    "content": message.content,
                    "user_id": message.user_id,
                    "created_at": message.created_at.isoformat() if message.created_at else None
                })

            return message_data

        except Exception as e:
            logger.error(f"Error retrieving messages for section {project_data_matrix_id}: {str(e)}")
            return []

    async def _handle_ai_result(
        self,
        project_data_matrix: ProjectDataMatrix,
        ai_result: Dict[str, Any],
        messages_count: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Handle the AI service result and update section if needed.

        Args:
            project_data_matrix: The section object
            ai_result: Result from AI service
            messages_count: Number of messages for this section
            db: Database session

        Returns:
            Response dictionary
        """
        try:
            action = ai_result.get("action", "question")

            if action == "draft":
                # Update section with draft output
                draft_output = ai_result.get("draft_output")
                project_data_matrix.output = draft_output
                db.add(project_data_matrix)
                await db.commit()
                await db.refresh(project_data_matrix)

                return {
                    "project_data_matrix_id": project_data_matrix.id,
                    "status": project_data_matrix.status,
                    "next_question": None,
                    "output": draft_output,
                    "message": f"Draft generated for section",
                    "messages_count": messages_count
                }
            else:
                # Return next question
                next_question = ai_result.get("next_question")

                return {
                    "project_data_matrix_id": project_data_matrix.id,
                    "status": project_data_matrix.status,
                    "next_question": next_question,
                    "output": None,
                    "message": f"Next question generated for section",
                    "messages_count": messages_count
                }

        except Exception as e:
            logger.error(f"Error handling AI result: {str(e)}")
            raise RuntimeError(f"Error handling AI result: {str(e)}")

    async def confirm_section(
        self,
        project_data_matrix_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Confirm a section by marking it as completed.

        Args:
            project_data_matrix_id: The ProjectDataMatrix ID to confirm
            db: Database session

        Returns:
            Dict containing confirmation details

        Raises:
            ValueError: If validation fails
            RuntimeError: If database operations fail
        """
        try:
            # Step 1: Validate the section can be confirmed
            project_data_matrix = await self._validate_section_confirm(project_data_matrix_id, db)

            # Step 2: Mark section as completed
            await self._finalize_section(project_data_matrix, db)

            # Step 3: Prepare the response
            response = {
                "project_data_matrix_id": project_data_matrix.id,
                "status": ProjectDataMatrixStatus.COMPLETED.value,
                "output": project_data_matrix.output,
                "message": f"Section confirmed successfully"
            }

            logger.info(f"Successfully confirmed section {project_data_matrix_id}")
            return response

        except Exception as e:
            logger.error(f"Error confirming section {project_data_matrix_id}: {str(e)}")
            # Rollback any changes if needed
            await db.rollback()
            raise

    async def _validate_section_confirm(
        self,
        project_data_matrix_id: str,
        db: AsyncSession
    ) -> ProjectDataMatrix:
        """
        Validate that the section can be confirmed.

        Args:
            project_data_matrix_id: The ProjectDataMatrix ID
            db: Database session

        Returns:
            The ProjectDataMatrix object

        Raises:
            ValueError: If validation fails
        """
        # Check if section exists
        result = await db.execute(
            select(ProjectDataMatrix).where(ProjectDataMatrix.id == project_data_matrix_id)
        )
        project_data_matrix = result.scalar_one_or_none()

        if not project_data_matrix:
            raise ValueError(f"Section with ID {project_data_matrix_id} not found")

        # Check if section is in progress
        if project_data_matrix.status != ProjectDataMatrixStatus.IN_PROGRESS:
            raise ValueError(
                f"Section is not in progress. Current status: {project_data_matrix.status}"
            )

        # Check if section has output to confirm
        if not project_data_matrix.output:
            raise ValueError(
                f"Section has no output to confirm"
            )

        return project_data_matrix

    async def _finalize_section(
        self,
        project_data_matrix: ProjectDataMatrix,
        db: AsyncSession
    ) -> None:
        """
        Finalize the section by marking it as completed.

        Args:
            project_data_matrix: The section to finalize
            db: Database session
        """
        try:
            # Mark section as completed
            project_data_matrix.status = ProjectDataMatrixStatus.COMPLETED

            db.add(project_data_matrix)
            await db.commit()
            await db.refresh(project_data_matrix)

            logger.debug(f"Finalized section {project_data_matrix.id}")

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to finalize section: {str(e)}")
            raise RuntimeError(f"Failed to finalize section: {str(e)}")

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
