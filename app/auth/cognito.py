"""
AWS Cognito JWT Authentication
Validates JWT tokens from AWS Cognito and extracts user claims
"""
from typing import Dict, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from cognitojwt import decode as cognito_jwt_decode
from app.config.settings import settings

# HTTPBearer automatically extracts "Bearer <token>" from Authorization header
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, str]:
    """
    FastAPI Dependency: Validate JWT token and return user claims
    
    This dependency:
    1. Extracts JWT from Authorization header
    2. Validates token signature using Cognito public keys
    3. Verifies token expiration, issuer, and audience
    4. Returns decoded claims (sub, email, name, etc.)
    
    Usage in routes:
        @router.get("/protected")
        async def protected_route(
            current_user: dict = Depends(get_current_user)
        ):
            user_id = current_user["sub"]
            email = current_user["email"]
            ...
    
    Raises:
        HTTPException: 401 if token is invalid, expired, or malformed
    
    Returns:
        dict: Decoded JWT claims containing:
            - sub: Unique user ID (UUID) from Cognito
            - email: User's email address
            - email_verified: Boolean indicating if email is verified
            - cognito:username: Username in Cognito
            - name: User's full name (if set)
            - custom:*: Any custom attributes set in Cognito
    """
    try:
        # Extract token from "Bearer <token>"
        token = credentials.credentials
        
        # Verify and decode JWT using cognitojwt
        # This internally:
        # - Fetches Cognito's public keys (JWKs) from AWS
        # - Verifies signature using RS256 algorithm
        # - Checks expiration (exp claim)
        # - Validates issuer (iss claim)
        claims = cognito_jwt_decode(
            token,
            region=settings.cognito_region,
            userpool_id=settings.cognito_user_pool_id,
            app_client_id=settings.cognito_app_client_id
        )
        
        return claims
        
    except Exception as e:
        # Token is invalid, expired, or malformed
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, str]]:
    """
    Optional authentication: Returns user claims if token is valid, None if missing/invalid
    
    Useful for routes that work with or without authentication.
    For example:
    - Public listings with optional filtering by user
    - Content that shows differently for authenticated users
    - Features available to both guests and users
    
    Usage in routes:
        @router.get("/public-content")
        async def public_content(
            current_user: dict | None = Depends(get_optional_user)
        ):
            if current_user:
                # Authenticated user - show personalized content
                user_id = current_user["sub"]
            else:
                # Guest - show public content only
                pass
    
    Returns:
        dict | None: User claims if authenticated, None otherwise
    """
    if not credentials:
        return None
        
    try:
        token = credentials.credentials
        claims = cognito_jwt_decode(
            token,
            region=settings.cognito_region,
            userpool_id=settings.cognito_user_pool_id,
            app_client_id=settings.cognito_app_client_id
        )
        return claims
    except:
        return None
