"""
Authentication Module
Handles JWT validation and user authentication using AWS Cognito
"""
from app.auth.cognito import get_current_user, get_optional_user, get_current_user_and_org

__all__ = ["get_current_user", "get_optional_user", "get_current_user_and_org"]
