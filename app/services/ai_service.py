"""
AI Service Module

This module provides AI-powered functionality using Google Gemini.
It includes text generation, analysis, and conversation management.
"""
from typing import Dict, List, Optional, Any
import logging
from dataclasses import asdict

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
    
    def __init__(self, gemini_client: Optional[Any] = None):
        """
        Initialize the AI service.
        
        Args:
            gemini_client: Optional pre-configured GeminiClient (mock for now)
        """
        try:
            # Try to import the real Gemini client
            from app.utils.gemini_client import (
                GeminiClient, 
                GeminiConfig, 
                GeminiResponse, 
                create_gemini_client
            )
            self.client = gemini_client or create_gemini_client()
        except ImportError:
            # Use mock client if real one is not available
            logger.warning("Gemini client not available - using mock implementation")
            self.client = MockGeminiClient()
        
        self._chat_sessions: Dict[str, Any] = {}
    
    def start_project_analysis(self, org_id: str, project_id: str) -> Dict[str, Any]:
        """
        Start AI analysis for a project - mock implementation for now
        
        Args:
            org_id: Organization ID
            project_id: Project ID
            
        Returns:
            Dictionary with AI analysis response (question or decision)
        """
        try:
            # Mock implementation that returns different scenarios
            import random
            import datetime
            
            scenarios = [
                # Scenario 1: Multiple choice single answer
                {
                    "id": f"question-{random.randint(1000, 9999)}",
                    "type": "question",
                    "question": {
                        "text": "What is the primary construction material for this project?",
                        "type": "multiple_choice_single",
                        "options": [
                            {"id": "1", "text": "Concrete"},
                            {"id": "2", "text": "Steel"},
                            {"id": "3", "text": "Wood"},
                            {"id": "4", "text": "Masonry"}
                        ]
                    },
                    "metadata": {
                        "session_id": f"session-{random.randint(10000, 99999)}",
                        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                        "next_step": "awaiting_user_response"
                    }
                },
                # Scenario 2: Decision with follow-up
                {
                    "id": f"decision-{random.randint(1000, 9999)}",
                    "type": "decision",
                    "decision": {
                        "text": "Based on initial analysis, this appears to be a residential project with moderate complexity.",
                        "confidence": 0.78,
                        "follow_up_required": True
                    },
                    "metadata": {
                        "session_id": f"session-{random.randint(10000, 99999)}",
                        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                        "next_step": "awaiting_user_confirmation"
                    }
                },
                # Scenario 3: Numerical input question
                {
                    "id": f"question-{random.randint(1000, 9999)}",
                    "type": "question",
                    "question": {
                        "text": "What is the estimated square footage of the building?",
                        "type": "numerical",
                        "validation": {
                            "min": 100,
                            "max": 10000
                        }
                    },
                    "metadata": {
                        "session_id": f"session-{random.randint(10000, 99999)}",
                        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                        "next_step": "awaiting_user_response"
                    }
                },
                # Scenario 4: Text input question
                {
                    "id": f"question-{random.randint(1000, 9999)}",
                    "type": "question",
                    "question": {
                        "text": "Please describe any special requirements or constraints for this project:",
                        "type": "text"
                    },
                    "metadata": {
                        "session_id": f"session-{random.randint(10000, 99999)}",
                        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                        "next_step": "awaiting_user_response"
                    }
                }
            ]
            
            return random.choice(scenarios)
            
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
