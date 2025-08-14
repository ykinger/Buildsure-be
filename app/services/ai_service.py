"""
AI Service Module

This module provides AI-powered functionality using Google Gemini.
It includes text generation, analysis, and conversation management.
"""
from typing import Dict, List, Optional, Any
import logging
from dataclasses import asdict

from app.utils.gemini_client import (
    GeminiClient, 
    GeminiConfig, 
    GeminiResponse, 
    create_gemini_client
)

logger = logging.getLogger(__name__)


class AIService:
    """
    Service class for AI-powered operations using Google Gemini.
    
    This service provides high-level methods for BuildSure-specific
    AI functionality including text analysis, content generation,
    and intelligent assistance.
    """
    
    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        """
        Initialize the AI service.
        
        Args:
            gemini_client: Optional pre-configured GeminiClient
        """
        self.client = gemini_client or create_gemini_client()
        self._chat_sessions: Dict[str, Any] = {}
    
    def analyze_building_description(self, description: str) -> Dict[str, Any]:
        """
        Analyze a building description and extract relevant information.
        
        Args:
            description: Building description text
            
        Returns:
            Dictionary with analysis results
        """
        try:
            prompt = f"""
            Analyze the following building description and extract key information:
            
            1. Building type (residential, commercial, industrial, etc.)
            2. Size/scale indicators
            3. Materials mentioned
            4. Special features or requirements
            5. Location indicators
            6. Budget indicators (if any)
            7. Timeline indicators (if any)
            8. Risk factors or challenges
            
            Building Description: "{description}"
            
            Please provide a structured JSON response with the extracted information.
            """
            
            response = self.client.generate_text(prompt)
            
            return {
                "success": response.success,
                "analysis": response.content if response.success else None,
                "error": response.error_message,
                "metadata": response.usage_metadata
            }
            
        except Exception as e:
            logger.error(f"Error analyzing building description: {e}")
            return {
                "success": False,
                "analysis": None,
                "error": str(e),
                "metadata": None
            }
    
    def generate_project_recommendations(self, project_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate project recommendations based on project details.
        
        Args:
            project_details: Dictionary containing project information
            
        Returns:
            Dictionary with recommendations
        """
        try:
            project_summary = self._format_project_details(project_details)
            
            prompt = f"""
            Based on the following project details, provide comprehensive recommendations:
            
            {project_summary}
            
            Please provide recommendations for:
            1. Best practices for this type of project
            2. Potential risks and mitigation strategies
            3. Material suggestions
            4. Timeline considerations
            5. Budget optimization tips
            6. Regulatory compliance requirements
            7. Sustainability considerations
            
            Format the response as a structured JSON with clear sections.
            """
            
            response = self.client.generate_text(prompt)
            
            return {
                "success": response.success,
                "recommendations": response.content if response.success else None,
                "error": response.error_message,
                "metadata": response.usage_metadata
            }
            
        except Exception as e:
            logger.error(f"Error generating project recommendations: {e}")
            return {
                "success": False,
                "recommendations": None,
                "error": str(e),
                "metadata": None
            }
    
    def estimate_project_complexity(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimate project complexity based on various factors.
        
        Args:
            project_data: Project information dictionary
            
        Returns:
            Dictionary with complexity analysis
        """
        try:
            project_summary = self._format_project_details(project_data)
            
            prompt = f"""
            Analyze the complexity of this building project and provide:
            
            {project_summary}
            
            Assessment criteria:
            1. Technical complexity (1-10 scale)
            2. Regulatory complexity (1-10 scale)
            3. Timeline complexity (1-10 scale)
            4. Budget complexity (1-10 scale)
            5. Overall complexity score (1-10 scale)
            6. Key complexity factors
            7. Complexity mitigation strategies
            8. Recommended team size and expertise
            
            Provide response in JSON format with detailed explanations.
            """
            
            response = self.client.generate_text(prompt)
            
            return {
                "success": response.success,
                "complexity_analysis": response.content if response.success else None,
                "error": response.error_message,
                "metadata": response.usage_metadata
            }
            
        except Exception as e:
            logger.error(f"Error estimating project complexity: {e}")
            return {
                "success": False,
                "complexity_analysis": None,
                "error": str(e),
                "metadata": None
            }
    
    def generate_risk_assessment(self, project_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive risk assessment for a building project.
        
        Args:
            project_details: Project information dictionary
            
        Returns:
            Dictionary with risk assessment
        """
        try:
            project_summary = self._format_project_details(project_details)
            
            prompt = f"""
            Conduct a comprehensive risk assessment for this building project:
            
            {project_summary}
            
            Identify and analyze:
            1. Technical risks (structural, engineering, etc.)
            2. Financial risks (budget overruns, market changes, etc.)
            3. Timeline risks (delays, scheduling conflicts, etc.)
            4. Regulatory risks (permits, compliance, etc.)
            5. Environmental risks (weather, site conditions, etc.)
            6. Market risks (material costs, labor availability, etc.)
            7. Safety risks
            
            For each risk category, provide:
            - Risk level (Low/Medium/High)
            - Probability of occurrence
            - Potential impact
            - Mitigation strategies
            
            Format as structured JSON.
            """
            
            response = self.client.generate_text(prompt)
            
            return {
                "success": response.success,
                "risk_assessment": response.content if response.success else None,
                "error": response.error_message,
                "metadata": response.usage_metadata
            }
            
        except Exception as e:
            logger.error(f"Error generating risk assessment: {e}")
            return {
                "success": False,
                "risk_assessment": None,
                "error": str(e),
                "metadata": None
            }
    
    def start_consultation_chat(self, session_id: str, initial_context: Optional[str] = None) -> Dict[str, Any]:
        """
        Start an AI consultation chat session.
        
        Args:
            session_id: Unique identifier for the chat session
            initial_context: Optional context to start the conversation
            
        Returns:
            Dictionary with session information
        """
        try:
            system_prompt = """
            You are an expert construction and building consultant AI assistant for BuildSure.
            You help users with:
            - Building project planning and management
            - Construction best practices
            - Risk assessment and mitigation
            - Material selection and optimization
            - Regulatory compliance guidance
            - Cost estimation and budget planning
            - Timeline planning and scheduling
            
            Provide helpful, accurate, and practical advice based on industry standards
            and best practices. Ask clarifying questions when needed to provide
            better assistance.
            """
            
            chat = self.client.start_chat()
            
            # Initialize with system context
            if initial_context:
                context_message = f"{system_prompt}\n\nInitial Context: {initial_context}"
            else:
                context_message = system_prompt
            
            initial_response = chat.send_message(context_message)
            
            # Store the chat session
            self._chat_sessions[session_id] = chat
            
            return {
                "success": True,
                "session_id": session_id,
                "initial_response": initial_response.content if initial_response.success else None,
                "error": initial_response.error_message,
                "metadata": initial_response.usage_metadata
            }
            
        except Exception as e:
            logger.error(f"Error starting consultation chat: {e}")
            return {
                "success": False,
                "session_id": session_id,
                "initial_response": None,
                "error": str(e),
                "metadata": None
            }
    
    def send_chat_message(self, session_id: str, message: str) -> Dict[str, Any]:
        """
        Send a message to an existing chat session.
        
        Args:
            session_id: Chat session identifier
            message: User message
            
        Returns:
            Dictionary with AI response
        """
        try:
            if session_id not in self._chat_sessions:
                return {
                    "success": False,
                    "response": None,
                    "error": "Chat session not found",
                    "metadata": None
                }
            
            chat = self._chat_sessions[session_id]
            response = chat.send_message(message)
            
            return {
                "success": response.success,
                "response": response.content if response.success else None,
                "error": response.error_message,
                "metadata": response.usage_metadata
            }
            
        except Exception as e:
            logger.error(f"Error sending chat message: {e}")
            return {
                "success": False,
                "response": None,
                "error": str(e),
                "metadata": None
            }
    
    def get_chat_history(self, session_id: str) -> Dict[str, Any]:
        """
        Get chat session history.
        
        Args:
            session_id: Chat session identifier
            
        Returns:
            Dictionary with chat history
        """
        try:
            if session_id not in self._chat_sessions:
                return {
                    "success": False,
                    "history": None,
                    "error": "Chat session not found"
                }
            
            chat = self._chat_sessions[session_id]
            history = chat.get_history()
            
            return {
                "success": True,
                "history": history,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return {
                "success": False,
                "history": None,
                "error": str(e)
            }
    
    def end_chat_session(self, session_id: str) -> Dict[str, Any]:
        """
        End a chat session and clean up resources.
        
        Args:
            session_id: Chat session identifier
            
        Returns:
            Dictionary with operation result
        """
        try:
            if session_id in self._chat_sessions:
                del self._chat_sessions[session_id]
                return {
                    "success": True,
                    "message": "Chat session ended successfully"
                }
            else:
                return {
                    "success": False,
                    "message": "Chat session not found"
                }
                
        except Exception as e:
            logger.error(f"Error ending chat session: {e}")
            return {
                "success": False,
                "message": str(e)
            }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on AI service.
        
        Returns:
            Dictionary with health status
        """
        try:
            client_healthy = self.client.health_check()
            
            return {
                "ai_service_healthy": True,
                "gemini_client_healthy": client_healthy,
                "active_chat_sessions": len(self._chat_sessions),
                "status": "healthy" if client_healthy else "degraded"
            }
            
        except Exception as e:
            logger.error(f"AI service health check failed: {e}")
            return {
                "ai_service_healthy": False,
                "gemini_client_healthy": False,
                "active_chat_sessions": 0,
                "status": "unhealthy",
                "error": str(e)
            }
    
    def _format_project_details(self, project_details: Dict[str, Any]) -> str:
        """
        Format project details into a readable string for AI prompts.
        
        Args:
            project_details: Project information dictionary
            
        Returns:
            Formatted project summary string
        """
        formatted_details = "Project Details:\n"
        for key, value in project_details.items():
            formatted_details += f"- {key.replace('_', ' ').title()}: {value}\n"
        
        return formatted_details
