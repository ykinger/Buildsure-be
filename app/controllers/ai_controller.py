"""
AI Controller Module

This module handles HTTP requests for AI-powered functionality.
It provides endpoints for building analysis, recommendations, and consultations.
"""
from flask import Blueprint, request, jsonify, Response
from typing import Tuple, Dict, Any
import uuid
import logging

from app.services.ai_service import AIService

logger = logging.getLogger(__name__)

# Create blueprint for AI endpoints
ai_bp = Blueprint('ai', __name__)

# Initialize AI service with error handling
try:
    ai_service = AIService()
    logger.info("AI service initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize AI service: {e}")
    ai_service = None


@ai_bp.route('/analyze/building-description', methods=['POST'])
def analyze_building_description() -> Tuple[Response, int]:
    """
    Analyze a building description and extract key information.
    
    Expected JSON payload:
    {
        "description": "Building description text"
    }
    
    Returns:
        JSON response with analysis results
    """
    try:
        if ai_service is None:
            return jsonify({
                "status": "error",
                "error": "AI service is not available"
            }), 503
        
        data = request.get_json()
        
        if not data or 'description' not in data:
            return jsonify({
                "error": "Missing 'description' field in request body"
            }), 400
        
        description = data['description']
        
        if not description.strip():
            return jsonify({
                "error": "Description cannot be empty"
            }), 400
        
        logger.info(f"Analyzing building description: {description[:100]}...")
        
        result = ai_service.analyze_building_description(description)
        
        if result['success']:
            return jsonify({
                "status": "success",
                "data": {
                    "analysis": result['analysis'],
                    "metadata": result['metadata']
                }
            }), 200
        else:
            return jsonify({
                "status": "error",
                "error": result['error']
            }), 500
            
    except Exception as e:
        logger.error(f"Error in analyze_building_description endpoint: {e}")
        return jsonify({
            "status": "error",
            "error": "Internal server error"
        }), 500


@ai_bp.route('/recommendations/project', methods=['POST'])
def get_project_recommendations() -> Tuple[Response, int]:
    """
    Get AI-powered project recommendations.
    
    Expected JSON payload:
    {
        "project_type": "residential",
        "size": "medium",
        "budget": "100000",
        "location": "urban",
        "requirements": ["eco-friendly", "modern design"]
    }
    
    Returns:
        JSON response with recommendations
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "Request body is required"
            }), 400
        
        logger.info(f"Generating project recommendations for: {data}")
        
        result = ai_service.generate_project_recommendations(data)
        
        if result['success']:
            return jsonify({
                "status": "success",
                "data": {
                    "recommendations": result['recommendations'],
                    "metadata": result['metadata']
                }
            }), 200
        else:
            return jsonify({
                "status": "error",
                "error": result['error']
            }), 500
            
    except Exception as e:
        logger.error(f"Error in get_project_recommendations endpoint: {e}")
        return jsonify({
            "status": "error",
            "error": "Internal server error"
        }), 500


@ai_bp.route('/assess/complexity', methods=['POST'])
def assess_project_complexity() -> Tuple[Response, int]:
    """
    Assess project complexity using AI analysis.
    
    Expected JSON payload:
    {
        "project_details": {
            "type": "commercial",
            "size": "large",
            "requirements": [...],
            "timeline": "12 months"
        }
    }
    
    Returns:
        JSON response with complexity assessment
    """
    try:
        data = request.get_json()
        
        if not data or 'project_details' not in data:
            return jsonify({
                "error": "Missing 'project_details' field in request body"
            }), 400
        
        project_details = data['project_details']
        
        logger.info(f"Assessing project complexity for: {project_details}")
        
        result = ai_service.estimate_project_complexity(project_details)
        
        if result['success']:
            return jsonify({
                "status": "success",
                "data": {
                    "complexity_analysis": result['complexity_analysis'],
                    "metadata": result['metadata']
                }
            }), 200
        else:
            return jsonify({
                "status": "error",
                "error": result['error']
            }), 500
            
    except Exception as e:
        logger.error(f"Error in assess_project_complexity endpoint: {e}")
        return jsonify({
            "status": "error",
            "error": "Internal server error"
        }), 500


@ai_bp.route('/assess/risks', methods=['POST'])
def assess_project_risks() -> Tuple[Response, int]:
    """
    Generate comprehensive risk assessment for a project.
    
    Expected JSON payload:
    {
        "project_details": {
            "type": "residential",
            "location": "coastal",
            "budget": "500000",
            "timeline": "18 months"
        }
    }
    
    Returns:
        JSON response with risk assessment
    """
    try:
        data = request.get_json()
        
        if not data or 'project_details' not in data:
            return jsonify({
                "error": "Missing 'project_details' field in request body"
            }), 400
        
        project_details = data['project_details']
        
        logger.info(f"Generating risk assessment for: {project_details}")
        
        result = ai_service.generate_risk_assessment(project_details)
        
        if result['success']:
            return jsonify({
                "status": "success",
                "data": {
                    "risk_assessment": result['risk_assessment'],
                    "metadata": result['metadata']
                }
            }), 200
        else:
            return jsonify({
                "status": "error",
                "error": result['error']
            }), 500
            
    except Exception as e:
        logger.error(f"Error in assess_project_risks endpoint: {e}")
        return jsonify({
            "status": "error",
            "error": "Internal server error"
        }), 500


@ai_bp.route('/chat/start', methods=['POST'])
def start_consultation_chat() -> Tuple[Response, int]:
    """
    Start an AI consultation chat session.
    
    Expected JSON payload:
    {
        "initial_context": "I need help planning a residential project"
    }
    
    Returns:
        JSON response with session ID and initial response
    """
    try:
        data = request.get_json() or {}
        initial_context = data.get('initial_context')
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        logger.info(f"Starting consultation chat session: {session_id}")
        
        result = ai_service.start_consultation_chat(session_id, initial_context)
        
        if result['success']:
            return jsonify({
                "status": "success",
                "data": {
                    "session_id": result['session_id'],
                    "initial_response": result['initial_response'],
                    "metadata": result['metadata']
                }
            }), 200
        else:
            return jsonify({
                "status": "error",
                "error": result['error']
            }), 500
            
    except Exception as e:
        logger.error(f"Error in start_consultation_chat endpoint: {e}")
        return jsonify({
            "status": "error",
            "error": "Internal server error"
        }), 500


@ai_bp.route('/chat/message', methods=['POST'])
def send_chat_message() -> Tuple[Response, int]:
    """
    Send a message to an existing chat session.
    
    Expected JSON payload:
    {
        "session_id": "uuid-string",
        "message": "What materials should I use for a coastal home?"
    }
    
    Returns:
        JSON response with AI response
    """
    try:
        data = request.get_json()
        
        if not data or 'session_id' not in data or 'message' not in data:
            return jsonify({
                "error": "Missing 'session_id' or 'message' field in request body"
            }), 400
        
        session_id = data['session_id']
        message = data['message']
        
        if not message.strip():
            return jsonify({
                "error": "Message cannot be empty"
            }), 400
        
        logger.info(f"Sending chat message to session {session_id}: {message[:100]}...")
        
        result = ai_service.send_chat_message(session_id, message)
        
        if result['success']:
            return jsonify({
                "status": "success",
                "data": {
                    "response": result['response'],
                    "metadata": result['metadata']
                }
            }), 200
        else:
            return jsonify({
                "status": "error",
                "error": result['error']
            }), 500 if "not found" not in result['error'] else 404
            
    except Exception as e:
        logger.error(f"Error in send_chat_message endpoint: {e}")
        return jsonify({
            "status": "error",
            "error": "Internal server error"
        }), 500


@ai_bp.route('/chat/history/<session_id>', methods=['GET'])
def get_chat_history(session_id: str) -> Tuple[Response, int]:
    """
    Get chat session history.
    
    Args:
        session_id: Chat session identifier
    
    Returns:
        JSON response with chat history
    """
    try:
        logger.info(f"Getting chat history for session: {session_id}")
        
        result = ai_service.get_chat_history(session_id)
        
        if result['success']:
            return jsonify({
                "status": "success",
                "data": {
                    "history": result['history']
                }
            }), 200
        else:
            return jsonify({
                "status": "error",
                "error": result['error']
            }), 404 if "not found" in result['error'] else 500
            
    except Exception as e:
        logger.error(f"Error in get_chat_history endpoint: {e}")
        return jsonify({
            "status": "error",
            "error": "Internal server error"
        }), 500


@ai_bp.route('/chat/end/<session_id>', methods=['DELETE'])
def end_chat_session(session_id: str) -> Tuple[Response, int]:
    """
    End a chat session.
    
    Args:
        session_id: Chat session identifier
    
    Returns:
        JSON response with operation result
    """
    try:
        logger.info(f"Ending chat session: {session_id}")
        
        result = ai_service.end_chat_session(session_id)
        
        return jsonify({
            "status": "success" if result['success'] else "error",
            "message": result['message']
        }), 200 if result['success'] else 404
        
    except Exception as e:
        logger.error(f"Error in end_chat_session endpoint: {e}")
        return jsonify({
            "status": "error",
            "error": "Internal server error"
        }), 500


@ai_bp.route('/health', methods=['GET'])
def ai_health_check() -> Tuple[Response, int]:
    """
    Health check endpoint for AI service.
    
    Returns:
        JSON response with AI service health status
    """
    try:
        health_status = ai_service.health_check()
        
        status_code = 200 if health_status['status'] in ['healthy', 'degraded'] else 503
        
        return jsonify({
            "status": health_status['status'],
            "data": health_status
        }), status_code
        
    except Exception as e:
        logger.error(f"Error in AI health check: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": "Health check failed"
        }), 503
