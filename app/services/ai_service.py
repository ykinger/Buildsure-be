"""
AI Service Module

This module provides AI-powered functionality using Google Gemini.
It includes text generation, analysis, and conversation management.
"""
from typing import Dict, List, Optional, Any
import logging
from dataclasses import asdict
from app.utils.prompt_builder import PromptBuilder
from json import loads

logger = logging.getLogger(__name__)

# Mock classes for when Gemini client is not available
class MockGeminiClient:
    """Mock Gemini client for when the real client is not available."""
    
    def generate_text(self, prompt: str) -> 'MockGeminiResponse':
        return MockGeminiResponse(False, None, "Gemini client not configured", None)
    
    def start_chat(self) -> 'MockChatSession':
        return MockChatSession()
    
    def health_check(self) -> bool:
        return False

class MockGeminiResponse:
    def __init__(self, success: bool, content: Optional[Any], error_message: Optional[str], usage_metadata: Optional[Any]):
        self.success = success
        self.content = content
        self.error_message = error_message
        self.usage_metadata = usage_metadata

class MockChatSession:
    def send_message(self, message: str) -> MockGeminiResponse:
        return MockGeminiResponse(False, None, "Chat not available", None)
    
    def get_history(self) -> List[Any]:
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

    
    def query(self, 
        current_question_number: str,
        form_questions_and_answers: list[dict],
        clarifying_questions_and_answers: list[dict]
        ) -> Dict[str, Any]:
        """
        Start AI analysis for a project - mock implementation for now
        
        Args:
            org_id: Organization ID
            project_id: Project ID
            
        Returns:
            Dictionary with AI analysis response (question or decision)
        """
        try:
            ai_response = self.client.generate_content(self.prompt_builder.render(
                current_question_number=current_question_number,
                form_questions_and_answers=form_questions_and_answers,
                clarifying_questions_and_answers=clarifying_questions_and_answers
                ))
            # remove ```json and ``` if present
            ai_response = ai_response.content.replace("```json", "").replace("```", "").strip()
            # TODO:
            #   1. [x] Trim excessive text (JSON code block markdown, etc)
            #   2. [ ] Make sure returned value matches expected JSON structure
            #   3. [ ] Throw exception if not
            #   4. Turn response into actual object/dict
            return loads(ai_response)
            
        except Exception as e:
            logger.error(f"Error in mock project analysis: {e}")
            # Fallback response if mock generation fails
            return {
                "id": "fallback-response",
                "type": "decision",
                "decision": {
                    "text": "AI analysis service is temporarily unavailable. Please try again later.",
                    "confidence": 0.0,
                    "follow_up_required": False
                },
                "metadata": {
                    "session_id": "fallback-session",
                    "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                    "next_step": "complete"
                }
            }
