"""
Health Check Controller
Handles HTTP requests for health monitoring endpoints.
"""
from flask import Blueprint, jsonify, Response
from typing import Tuple

from app.services.health_service import HealthService

# Create blueprint for health endpoints
health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health_check() -> Tuple[Response, int]:
    """
    Health check endpoint that returns application status.
    
    Returns:
        JSON response with health status and HTTP 200 status code
    """
    try:
        health_data = HealthService.get_health_status()
        return jsonify(health_data), 200
    except Exception as e:
        # Log the error in a real application
        error_response = {
            "status": "unhealthy",
            "error": "Internal server error during health check"
        }
        return jsonify(error_response), 500


@health_bp.route('/health/simple', methods=['GET'])
def simple_health_check() -> Tuple[Response, int]:
    """
    Simple health check endpoint for basic monitoring.
    
    Returns:
        JSON response with simple status and HTTP 200 status code
    """
    try:
        health_data = HealthService.get_simple_health_status()
        return jsonify(health_data), 200
    except Exception as e:
        error_response = {
            "status": "error",
            "message": "Health check failed"
        }
        return jsonify(error_response), 500
