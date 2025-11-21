"""
AWS Cognito JWT Authentication
Validates JWT tokens from AWS Cognito and extracts user claims
"""
from typing import Dict, Optional, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from cognitojwt import decode as cognito_jwt_decode
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.settings import settings
from app.database import get_db
from app.repository.user import get_user_by_id

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


async def get_current_user_and_org(
    current_user: Dict[str, str] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    FastAPI Dependency: Validate JWT token and retrieve user with organization ID
    
    This dependency combines JWT validation with database lookup to provide:
    1. JWT token validation (via get_current_user)
    2. User record from database
    3. Organization ID the user belongs to
    
    Usage in routes:
        @router.get("/protected")
        async def protected_route(
            user_and_org: dict = Depends(get_current_user_and_org)
        ):
            user_id = user_and_org["user_claims"]["sub"]
            org_id = user_and_org["organization_id"]
            user_email = user_and_org["user"].email
            user_name = user_and_org["user"].name
            ...
    
    Raises:
        HTTPException: 
            - 401 if token is invalid, expired, or malformed
            - 404 if user doesn't exist in database
    
    Returns:
        dict: Dictionary containing:
            - user_claims: Dict with JWT claims (sub, email, email_verified, etc.)
            - organization_id: str - The ID of the organization the user belongs to
            - user: User object with all user data from database
    """
    try:
        # Extract user ID from JWT claims
        user_id = current_user.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Fetch user from database
        user = await get_user_by_id(user_id, session)
        
        # Return combined data
        return {
            "user_claims": current_user,
            "organization_id": user.organization_id,
            "user": user
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions (from get_user_by_id or above)
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user and organization: {str(e)}"
        )
