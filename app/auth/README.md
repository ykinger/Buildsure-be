# Authentication Module

AWS Cognito JWT authentication for FastAPI routes.

## Overview

This module provides JWT token validation using AWS Cognito. It validates tokens sent from your frontend and extracts user information (claims) from the JWT.

## Files

- `__init__.py` - Package initialization, exports main functions
- `cognito.py` - JWT validation logic and FastAPI dependencies

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs `cognitojwt` which handles JWT validation for Cognito tokens.

### 2. Configure Environment Variables

Add to your `.env` file:

```env
COGNITO_REGION=us-east-1
COGNITO_USER_POOL_ID=us-east-1_XXXXXXXXX
COGNITO_APP_CLIENT_ID=your-app-client-id
```

Get these values from AWS Console:
1. Go to AWS Cognito Console
2. Select your User Pool
3. Copy the User Pool ID
4. Go to App Integration → App Clients
5. Copy the App Client ID

### 3. Use in Routes

```python
from fastapi import APIRouter, Depends
from app.auth.cognito import get_current_user

router = APIRouter()

@router.get("/protected")
async def protected_route(
    current_user: dict = Depends(get_current_user)
):
    """This route requires authentication"""
    user_id = current_user["sub"]
    email = current_user["email"]
    return {"user_id": user_id, "email": email}
```

## Available Functions

### `get_current_user`

FastAPI dependency that requires authentication.

**Usage:**
```python
current_user: dict = Depends(get_current_user)
```

**Returns:**
- `dict` with JWT claims (sub, email, name, etc.)

**Raises:**
- `HTTPException(401)` if token is invalid, expired, or missing

### `get_optional_user`

FastAPI dependency for optional authentication.

**Usage:**
```python
current_user: dict | None = Depends(get_optional_user)
```

**Returns:**
- `dict` with JWT claims if authenticated
- `None` if not authenticated or token invalid

## JWT Claims

The decoded JWT contains these standard claims:

```python
{
    "sub": "user-uuid",              # Unique user ID
    "email": "user@example.com",     # Email
    "email_verified": true,          # Email verification
    "cognito:username": "username",  # Username
    "name": "John Doe",              # Full name
    "custom:*": "value"              # Custom attributes
}
```

## How It Works

1. **Frontend sends request** with JWT in Authorization header:
   ```
   Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

2. **HTTPBearer extracts token** from header

3. **CognitoJWTVerifier validates token**:
   - Fetches Cognito's public keys (JWKs) - cached after first call
   - Verifies signature using RS256 algorithm
   - Checks expiration (exp claim)
   - Validates issuer (iss claim)
   - Validates audience (aud claim)

4. **Returns decoded claims** to your route handler

5. **Use claims** to query your database and perform business logic

## Error Responses

### Invalid Token
```json
Status: 401
{
  "detail": "Invalid authentication credentials: Token signature is invalid"
}
```

### Expired Token
```json
Status: 401
{
  "detail": "Invalid authentication credentials: Token is expired"
}
```

### Missing Token
```json
Status: 403
{
  "detail": "Not authenticated"
}
```

## Examples

### Protected Route
```python
@router.get("/my-profile")
async def get_my_profile(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    user = await get_user_by_id(current_user["sub"], session)
    return {"user": user}
```

### Optional Auth Route
```python
@router.get("/public-data")
async def get_public_data(
    current_user: dict | None = Depends(get_optional_user)
):
    if current_user:
        # Show personalized data
        return {"data": get_personalized(current_user["sub"])}
    else:
        # Show public data
        return {"data": get_public()}
```

### Public Route (No Auth)
```python
@router.get("/health")
async def health_check():
    """No authentication needed"""
    return {"status": "healthy"}
```

## Testing

### With cURL
```bash
curl -H "Authorization: Bearer <JWT_TOKEN>" \
     http://localhost:8000/api/v1/protected
```

### With Python
```python
import requests

token = "your-jwt-token"
response = requests.get(
    "http://localhost:8000/api/v1/protected",
    headers={"Authorization": f"Bearer {token}"}
)
```

### Decode JWT
Visit https://jwt.io to decode and inspect JWT tokens.

## Best Practices

1. **Always use `sub` as user identifier** - Don't rely on email as it can change
2. **Don't store passwords** - Cognito handles authentication
3. **Validate on backend** - Never trust frontend validation alone
4. **Handle token refresh** - Implement token refresh in frontend
5. **Use HTTPS in production** - Protect tokens in transit

## Troubleshooting

### "Token signature is invalid"
- Verify User Pool ID and App Client ID are correct
- Ensure region matches your Cognito User Pool

### "Token is expired"
- Implement token refresh in frontend
- Check token expiration time (default: 1 hour)

### "Not authenticated"
- Verify Authorization header format: `Bearer <token>`
- Check token is being sent from frontend

## More Information

See `docs/authentication-usage.md` for detailed examples and usage patterns.
