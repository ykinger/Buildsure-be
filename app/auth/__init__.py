"""
Authentication Module
Handles JWT validation and user authentication using AWS Cognito
"""
from app.auth.cognito import get_current_user, get_optional_user

__all__ = ["get_current_user", "get_optional_user"]
