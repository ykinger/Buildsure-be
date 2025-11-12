# JWT Authentication Usage Guide

This guide demonstrates how to use AWS Cognito JWT authentication in your FastAPI routes.

## Setup

Before using authentication, ensure you have:

1. **Installed dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Updated your `.env` file** with Cognito configuration:
   ```env
   COGNITO_REGION=us-east-1
   COGNITO_USER_POOL_ID=us-east-1_XXXXXXXXX
   COGNITO_APP_CLIENT_ID=your-app-client-id
   ```

3. **Cognito User Pool ID and App Client ID** from AWS Console:
   - AWS Console → Cognito → User Pools → Your Pool
   - Copy User Pool ID (e.g., `us-east-1_abc123xyz`)
   - Go to App Integration → App Clients → Copy App Client ID

## Basic Usage

### Protected Route (Requires Authentication)

```python
from fastapi import APIRouter, Depends
from app.auth.cognito import get_current_user

router = APIRouter()

@router.get("/api/v1/profile")
async def get_profile(
    current_user: dict = Depends(get_current_user)
):
    """
    Protected route - requires valid JWT token
    Returns user profile information
    """
    return {
        "user_id": current_user["sub"],
        "email": current_user["email"],
        "name": current_user.get("name", ""),
        "email_verified": current_user.get("email_verified", False)
    }
```

### Public Route (No Authentication)

```python
@router.get("/api/v1/health")
async def health_check():
    """Public route - no authentication required"""
    return {"status": "healthy"}
```

### Optional Authentication

```python
from app.auth.cognito import get_optional_user

@router.get("/api/v1/projects")
async def list_projects(
    current_user: dict | None = Depends(get_optional_user)
):
    """
    Works with or without authentication
    Shows personalized content if authenticated
    """
    if current_user:
        # Authenticated user - show their projects
        user_id = current_user["sub"]
        return {"projects": get_user_projects(user_id)}
    else:
        # Guest - show public projects only
        return {"projects": get_public_projects()}
```

## Real-World Examples

### Example 1: Get User's Projects

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.cognito import get_current_user
from app.database import get_db
from app.repository.user import get_user_by_id
from app.repository.project import get_projects_by_user

router = APIRouter()

@router.get("/api/v1/my-projects")
async def get_my_projects(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get authenticated user's projects"""
    # Extract user ID from JWT
    user_sub = current_user["sub"]
    
    # Query database using Cognito sub
    user = await get_user_by_id(user_sub, session)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's projects
    projects = await get_projects_by_user(user.id, session)
    
    return {"projects": projects}
```

### Example 2: Create Project for Authenticated User

```python
from app.schemas.project import ProjectCreate

@router.post("/api/v1/projects")
async def create_project(
    project_data: ProjectCreate,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Create a new project for authenticated user"""
    user_sub = current_user["sub"]
    
    # Get user from database
    user = await get_user_by_id(user_sub, session)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create project
    project = Project(
        name=project_data.name,
        user_id=user.id,
        organization_id=user.organization_id
    )
    
    await create_project_repo(project, session)
    return {"project": project}
```

### Example 3: Update User Profile

```python
from app.schemas.user import UserUpdate

@router.put("/api/v1/profile")
async def update_profile(
    user_data: UserUpdate,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Update authenticated user's profile"""
    user_sub = current_user["sub"]
    
    # Only allow users to update their own profile
    user = await get_user_by_id(user_sub, session)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update user
    updated_user = await update_user_repo(
        user.id, 
        user_data.model_dump(exclude_unset=True),
        session
    )
    
    return {"user": updated_user}
```

## Available JWT Claims

When you use `Depends(get_current_user)`, you get access to these claims:

```python
current_user = {
    "sub": "a1b2c3d4-5678-90ab-cdef-1234567890ab",  # Unique user ID
    "email": "user@example.com",                     # Email address
    "email_verified": True,                          # Email verification status
    "cognito:username": "johndoe",                   # Cognito username
    "name": "John Doe",                              # Full name (if set)
    "iss": "https://cognito-idp.us-east-1...",      # Token issuer
    "aud": "your-app-client-id",                     # Token audience
    "exp": 1234567890,                               # Expiration timestamp
    "iat": 1234567890,                               # Issued at timestamp
    # Any custom attributes you set in Cognito:
    "custom:organization_id": "org-123",
    "custom:role": "admin"
}
```

## Testing Authentication

### 1. Get JWT from Frontend

Your frontend should send requests with the Authorization header:

```typescript
// Frontend example (React/Next.js with AWS Amplify)
import { Auth } from 'aws-amplify';

const response = await fetch('http://localhost:8000/api/v1/profile', {
  headers: {
    'Authorization': `Bearer ${(await Auth.currentSession()).getIdToken().getJwtToken()}`
  }
});
```

### 2. Test with cURL

```bash
# Replace <JWT_TOKEN> with actual token from your frontend
curl -H "Authorization: Bearer <JWT_TOKEN>" \
     http://localhost:8000/api/v1/profile
```

### 3. Test with Python

```python
import requests

token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
headers = {"Authorization": f"Bearer {token}"}

response = requests.get(
    "http://localhost:8000/api/v1/profile",
    headers=headers
)

print(response.json())
```

### 4. Decode JWT (for debugging)

Visit https://jwt.io and paste your JWT to see the claims without making API calls.

## Error Handling

### Invalid Token

```json
Status: 401 Unauthorized
{
  "detail": "Invalid authentication credentials: Token signature is invalid"
}
```

### Expired Token

```json
Status: 401 Unauthorized
{
  "detail": "Invalid authentication credentials: Token is expired"
}
```

### Missing Token

```json
Status: 403 Forbidden
{
  "detail": "Not authenticated"
}
```

## Best Practices

1. **Use `sub` as User ID**: Always use the `sub` claim from Cognito as your user identifier in the database, not email (email can change).

2. **Validate on Backend**: Never trust frontend validation alone. Always validate JWT on the backend.

3. **Store Minimal Data**: Don't store passwords or sensitive Cognito data in your database. JWT contains what you need.

4. **Handle Token Refresh**: Implement token refresh logic in your frontend to handle expired tokens gracefully.

5. **User Sync**: Ensure your user table stays in sync with Cognito (use the `sub` as the primary key or foreign key reference).

## Complete Route Example

Here's a complete example showing multiple authentication patterns:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.cognito import get_current_user, get_optional_user
from app.database import get_db
from app.repository.user import get_user_by_id

router = APIRouter(prefix="/api/v1/users", tags=["users"])

@router.get("/me")
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get authenticated user's profile - PROTECTED"""
    user = await get_user_by_id(current_user["sub"], session)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user": user}

@router.get("/public")
async def get_public_users():
    """Get public user list - NO AUTH"""
    return {"users": [...]}

@router.get("/dashboard")
async def get_dashboard(
    current_user: dict | None = Depends(get_optional_user),
    session: AsyncSession = Depends(get_db)
):
    """Get dashboard - OPTIONAL AUTH"""
    if current_user:
        # Personalized dashboard
        user = await get_user_by_id(current_user["sub"], session)
        return {"dashboard": "personalized", "user": user}
    else:
        # Public dashboard
        return {"dashboard": "public"}
```

## Next Steps

1. Add the Cognito configuration to your `.env` file
2. Install dependencies: `pip install -r requirements.txt`
3. Add `Depends(get_current_user)` to routes you want to protect
4. Test with JWT tokens from your frontend
5. Ensure your user table uses Cognito `sub` as the user identifier

For questions or issues, check the FastAPI documentation on dependencies and security.
