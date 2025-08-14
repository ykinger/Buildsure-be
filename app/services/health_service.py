"""
Health Check Service
Business logic for health monitoring and status checks.
"""
from datetime import datetime
from typing import Dict, Any
import sys
import platform
from app import db


class HealthService:
    """Service class for handling health check operations."""
    
    @staticmethod
    def get_health_status() -> Dict[str, Any]:
        """
        Get comprehensive health status of the application.
        
        Returns:
            Dictionary containing health status information
        """
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "BuildSure Backend API",
            "version": "1.0.0",
            "environment": {
                "python_version": sys.version,
                "platform": platform.platform(),
            },
            "database": HealthService._check_database_connection(),
            "ai_service": HealthService._check_ai_service_health()
        }
        
        # Determine overall status based on component health
        if health_data["database"]["status"] == "disconnected" or health_data["ai_service"]["status"] == "unhealthy":
            health_data["status"] = "degraded"
        
        return health_data
    
    @staticmethod
    def get_simple_health_status() -> Dict[str, str]:
        """
        Get simple health status for basic health checks.
        
        Returns:
            Simple dictionary with status and timestamp
        """
        return {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def _check_database_connection() -> Dict[str, Any]:
        """
        Check database connectivity status.
        
        Returns:
            Dict containing database status information
        """
        try:
            # Try to execute a simple query to test database connection
            db.session.execute(db.text("SELECT 1"))
            return {
                "status": "connected",
                "message": "Database connection is healthy"
            }
        except Exception as e:
            return {
                "status": "disconnected",
                "message": f"Database connection failed: {str(e)}"
            }
    
    @staticmethod
    def _check_ai_service_health() -> Dict[str, Any]:
        """
        Check AI service health status.
        
        Returns:
            Dict containing AI service status information
        """
        try:
            # Import here to avoid circular imports and handle missing dependencies gracefully
            from app.services.ai_service import AIService
            
            ai_service = AIService()
            health_status = ai_service.health_check()
            
            return {
                "status": health_status.get("status", "unknown"),
                "gemini_client_healthy": health_status.get("gemini_client_healthy", False),
                "active_chat_sessions": health_status.get("active_chat_sessions", 0)
            }
        except ImportError as e:
            return {
                "status": "unavailable",
                "message": f"AI service dependencies not available: {str(e)}"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"AI service health check failed: {str(e)}"
            }
