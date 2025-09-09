"""
AI Service Module

This module provides AI-powered functionality using Google Gemini.
It includes text generation, analysis, and conversation management.
"""
from typing import Dict, List, Optional, Any, Union
import logging
import datetime
from dataclasses import asdict
from app.utils.prompt_builder import PromptBuilder
from app.models.ai_response import AIResponse, create_error_response, FinalAnswerData, MultipleChoiceMultipleOptionsData, MultipleChoiceSingleOptionData, NumericInputData, TextInputData, Metadata
from json import loads, JSONDecodeError

logger = logging.getLogger(__name__)

# Mock classes for when Gemini client is not available
class MockGeminiClient:
    """Mock Gemini client for when the real client is not available."""
    
    def generate_text(self, prompt: str) -> 'MockGeminiResponse':
        return MockGeminiResponse(False, None, "Gemini client not configured", None)
    
    def generate_content(self, prompt: str) -> 'MockGeminiResponse':
        """Mock implementation of generate_content method."""
        return MockGeminiResponse(False, '{"type": "mock", "content": "Mock response"}', None, None)
    
    def start_chat(self) -> 'MockChatSession':
        return MockChatSession()
    
    def health_check(self) -> bool:
        return False

class MockGeminiResponse:
    def __init__(self, success: bool, content: Optional[str], error_message: Optional[str], usage_metadata: Optional[Dict[str, Any]]):
        self.success = success
        self.content = content
        self.error_message = error_message
        self.usage_metadata = usage_metadata

class MockChatSession:
    def send_message(self, message: str) -> 'MockGeminiResponse':
        return MockGeminiResponse(False, None, "Chat not available", None)
    
    def get_history(self) -> List[Dict[str, Any]]:
        return []

class AIService:
    """
    Service class for AI-powered operations using Google Gemini.
    
    This service provides high-level methods for BuildSure-specific
    AI functionality including text analysis, content generation,
    and intelligent assistance.
    """
    
    def __init__(self, gemini_client: Any, prompt_builder: PromptBuilder):
        """
        Initialize the AI service.
        
        Args:
            gemini_client: Optional pre-configured GeminiClient (mock for now)
            prompt_builder: PromptBuilder
        """
        self.client = gemini_client or MockGeminiClient()
        self.prompt_builder = prompt_builder

    def _parse_llm_response(self, llm_response_text: str) -> AIResponse:
        """
        Parse LLM response and convert to unified AIResponse format.
        
        Args:
            llm_response_text: Raw text response from LLM
            
        Returns:
            AIResponse object in unified format
        """
        try:
            # Clean and parse JSON response
            cleaned_text = llm_response_text.replace("```json", "").replace("```", "").strip()
            response_data = loads(cleaned_text)
            
            # Extract response type
            response_type = response_data.get("response_type")
            
            if not response_type:
                raise ValueError("Missing response_type in LLM response")
            
            # Create appropriate data object based on response type
            if response_type == "final_answer":
                data = FinalAnswerData(
                    form_question_number=response_data.get("form_question_number", ""),
                    form_question_title=response_data.get("form_question_title", ""),
                    final_answer=response_data.get("final_answer", ""),
                    justification=response_data.get("justification", "")
                )
                confidence = 0.9  # High confidence for final answers
                
            elif response_type == "clarifying_question":
                input_type = response_data.get("input_type")
                
                if input_type == "multiple_choice_multiple_options":
                    data = MultipleChoiceMultipleOptionsData(
                        clarifying_question=response_data.get("clarifying_question", ""),
                        clarifying_question_context=response_data.get("clarifying_question_context", ""),
                        choices=response_data.get("choices", [])
                    )
                elif input_type == "multiple_choice_single_option":
                    data = MultipleChoiceSingleOptionData(
                        clarifying_question=response_data.get("clarifying_question", ""),
                        clarifying_question_context=response_data.get("clarifying_question_context", ""),
                        choices=response_data.get("choices", [])
                    )
                elif input_type == "numeric":
                    data = NumericInputData(
                        clarifying_question=response_data.get("clarifying_question", ""),
                        clarifying_question_context=response_data.get("clarifying_question_context", ""),
                        unit=response_data.get("unit", ""),
                        validation=response_data.get("validation", {})
                    )
                elif input_type == "text":
                    data = TextInputData(
                        clarifying_question=response_data.get("clarifying_question", ""),
                        clarifying_question_context=response_data.get("clarifying_question_context", "")
                    )
                else:
                    raise ValueError(f"Unknown input_type: {input_type}")
                
                confidence = 0.8  # Moderate confidence for clarifying questions
                
            else:
                raise ValueError(f"Unknown response_type: {response_type}")
            
            # Create metadata
            metadata = Metadata(
                timestamp=datetime.datetime.utcnow().isoformat() + "Z",
                confidence=confidence
            )
            
            return AIResponse(
                response_type=response_type,
                data=data,
                metadata=metadata
            )
            
        except JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return create_error_response(
                error_type="validation_error",
                message="Invalid JSON response from AI service",
                suggestion="Please try again or check the prompt formatting",
                confidence=0.0
            )
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            return create_error_response(
                error_type="processing_error",
                message=f"Failed to process AI response: {str(e)}",
                suggestion="Please try again",
                confidence=0.0
            )
    
    def query_code_matrix(self, org_id: str, project_id: str, 
                         code_matrix_repository: Any) -> Dict[str, Any]:
        """
        Query AI service with code matrix data.
        
        Args:
            org_id: Organization ID
            project_id: Project ID
            code_matrix_repository: CodeMatrixRepository instance for data access
            
        Returns:
            Dictionary with AI response in unified format
        """
        try:
            # Get code matrix status from repository
            code_matrix_status = code_matrix_repository.get_code_matrix_status(org_id, project_id)
            
            # Use empty values if no code matrix status is found
            current_section = "3.01"
            code_matrix_questions = []
            clarifying_questions = []
            
            if code_matrix_status:
                current_section = code_matrix_status.curr_section or "3.01"
                code_matrix_questions = code_matrix_status.code_matrix_questions or []
                clarifying_questions = code_matrix_status.clarifying_questions or []
            
            if not self.client or isinstance(self.client, MockGeminiClient):
                logger.warning("AI service not available - returning fallback response")
                # Return fallback error response
                return create_error_response(
                    error_type="service_unavailable",
                    message="AI analysis service is currently unavailable",
                    suggestion="Please try again later",
                    confidence=0.0
                ).to_dict()
            
            # Call AI service query with code matrix data
            ai_response = self.client.generate_content(self.prompt_builder.render(
                current_question_number=current_section,
                form_questions_and_answers=code_matrix_questions,
                clarifying_questions_and_answers=clarifying_questions
            ))
            
            # Parse and return unified response
            unified_response = self._parse_llm_response(ai_response.text)
            return unified_response.to_dict()
            
        except Exception as e:
            logger.error(f"Error querying code matrix: {e}")
            return create_error_response(
                error_type="processing_error",
                message="An error occurred while querying code matrix",
                suggestion="Please try again",
                confidence=0.0
            ).to_dict()

    def save_answer_and_get_next_question(self, org_id: str, project_id: str, 
                                        question: str, answer: str,
                                        code_matrix_repository: Any) -> Dict[str, Any]:
        """
        Save user's answer to a clarifying question and get the next question.
        
        Args:
            org_id: Organization ID
            project_id: Project ID
            question: The original question that was asked
            answer: User's answer to the question
            code_matrix_repository: CodeMatrixRepository instance for data access
            
        Returns:
            Dictionary with next AI question or final answer in unified format
        """
        try:
            # Format the question-answer pair for storage
            qa_pair = f"Q: {question} | A: {answer}"
            
            # Save the answer to the database
            code_matrix_repository.add_clarifying_question(org_id, project_id, qa_pair)
            
            # Get the next question by calling query_code_matrix
            next_question_result = self.query_code_matrix(org_id, project_id, code_matrix_repository)
            
            return next_question_result
            
        except Exception as e:
            logger.error(f"Error saving answer and getting next question: {e}")
            return create_error_response(
                error_type="processing_error",
                message="An error occurred while processing your answer",
                suggestion="Please try again",
                confidence=0.0
            ).to_dict()

    def query(self, 
        current_question_number: str,
        form_questions_and_answers: List[str],
        clarifying_questions_and_answers: List[str]
        ) -> Dict[str, Any]:
        """
        Generic AI query method for direct interaction.
        
        Args:
            current_question_number: The current question number
            form_questions_and_answers: List of form questions and answers
            clarifying_questions_and_answers: List of clarifying questions and answers
            
        Returns:
            Dictionary with AI analysis response in unified format
        """
        try:
            ai_response = self.client.generate_content(self.prompt_builder.render(
                current_question_number=current_question_number,
                form_questions_and_answers=form_questions_and_answers,
                clarifying_questions_and_answers=clarifying_questions_and_answers
            ))
            
            # Parse and return unified response
            unified_response = self._parse_llm_response(ai_response.text)
            return unified_response.to_dict()
            
        except Exception as e:
            logger.error(f"Error in AI query: {e}")
            return create_error_response(
                error_type="processing_error",
                message="AI analysis service is temporarily unavailable",
                suggestion="Please try again later",
                confidence=0.0
            ).to_dict()
