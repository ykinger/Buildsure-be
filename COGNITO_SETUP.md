# AWS Cognito JWT Authentication - Setup Complete! 🎉

## ✅ What's Been Implemented

All JWT authentication code is ready to use:

### Files Created:
- ✅ `app/auth/cognito.py` - JWT validation logic
- ✅ `app/auth/__init__.py` - Package initialization  
- ✅ `app/auth/README.md` - Quick reference guide
- ✅ `docs/authentication-usage.md` - Detailed usage examples

### Files Updated:
- ✅ `requirements.txt` - Added `cognitojwt==1.4.1`
- ✅ `app/config/settings.py` - Added Cognito configuration
- ✅ `.env.example` - Added environment variable templates

### Package Installed:
- ✅ `cognitojwt==1.4.1` - JWT validation library

---

## 🚀 Quick Start (3 Steps)

### Step 1: Configure Environment Variables

Add to your `.env` file:

```env
# AWS Cognito Configuration
COGNITO_REGION=us-east-2
COGNITO_USER_POOL_ID=us-east-2_uM4bmGp4F
COGNITO_APP_CLIENT_ID=1jnked1f39lijtnhkc2j69f4c9
```

### Step 2: Restart Your Application

```bash
# Stop your current server (Ctrl+C)
# Then restart
python run.py
# or
uvicorn app.main:app --reload
```

### Step 3: Add Authentication to Routes

Choose which routes need protection:

#### Protected Route (Requires Authentication):
```python
from fastapi import Depends
from app.auth.cognito import get_current_user

@router.get("/api/v1/projects")
async def list_projects(
    current_user: dict = Depends(get_current_user),  # ← Add this line
    session: AsyncSession = Depends(get_db)
):
    """Now requires valid JWT token"""
    user_sub = current_user["sub"]  # Get Cognito user ID
    
    # Query your database using sub
    user = await get_user_by_id(user_sub, session)
    projects = await get_projects_by_user(user.id, session)
    return {"projects": projects}
```

#### Public Route (No Authentication):
```python
@router.get("/api/v1/health")
async def health_check():
    """Public route - no authentication needed"""
    return {"status": "healthy"}
```

---

## 📱 Frontend Integration

### Using Amplify (Current Setup)

```javascript
import { Auth } from 'aws-amplify';

// Get ID token (recommended)
const session = await Auth.currentSession();
const idToken = session.getIdToken().getJwtToken();

// Make authenticated request
const response = await fetch('http://localhost:8000/api/v1/projects', {
  headers: {
    'Authorization': `Bearer ${idToken}`
  }
});
```

### Important Note:
Your frontend is currently sending **access tokens**. For best results, switch to **ID tokens**:

```javascript
// Access token (current)
const accessToken = session.getAccessToken().getJwtToken();

// ID token (recommended)
const idToken = session.getIdToken().getJwtToken();  // ← Use this
```

---

## 🧪 Testing Authentication

### Test 1: Get a Token from Frontend

1. Open browser dev tools (F12)
2. Go to Console tab
3. Run:
   ```javascript
   const session = await Auth.currentSession();
   console.log(session.getIdToken().getJwtToken());
   ```
4. Copy the token

### Test 2: Test with cURL

```bash
# Replace <TOKEN> with your actual JWT
curl -H "Authorization: Bearer <TOKEN>" \
     http://localhost:8000/api/v1/projects
```

### Test 3: Check Token Contents

Visit https://jwt.io and paste your token to see:
```json
{
  "sub": "c17b35c0-d051-7000-5fb7-55cead7e0d38",
  "email": "user@example.com",
  "aud": "1jnked1f39lijtnhkc2j69f4c9"
}
```

---

## 📋 Routes to Protect

Consider adding authentication to these existing routes:

### app/routers/projects.py
- ✅ `GET /api/v1/projects` - List user's projects
- ✅ `POST /api/v1/projects` - Create project
- ✅ `GET /api/v1/projects/{id}` - Get project details
- ✅ `PUT /api/v1/projects/{id}` - Update project
- ✅ `DELETE /api/v1/projects/{id}` - Delete project

### app/routers/sections.py
- ✅ `GET /api/v1/sections` - List sections
- ✅ `POST /api/v1/sections` - Create section
- ✅ `PUT /api/v1/sections/{id}` - Update section

### app/routers/users.py
- ✅ `GET /api/v1/users/me` - Get current user profile
- ⚠️ `GET /api/v1/users` - List all users (admin only?)

### app/routers/organizations.py
- Depends on your business logic

---

## 🔐 User Table Considerations

Your user table should reference Cognito users:

### Option 1: Use `sub` as Primary Key
```python
class User(CustomBase, table=True):
    id: str = Field(primary_key=True)  # Store Cognito sub here
    organization_id: str
    name: str
    email: str
```

### Option 2: Add `cognito_sub` Column
```python
class User(CustomBase, table=True):
    id: str = Field(primary_key=True)  # Your own UUID
    cognito_sub: str = Field(unique=True)  # Cognito's sub
    organization_id: str
    name: str
    email: str
```

---

## 🐛 Troubleshooting

### Error: "Invalid authentication credentials"

**Cause:** Token validation failed

**Solutions:**
1. Check `.env` has correct values
2. Verify token isn't expired (tokens expire in 1 hour)
3. Make sure frontend sends ID token, not access token
4. Confirm region matches your Cognito User Pool

### Error: "Not authenticated"

**Cause:** Missing Authorization header

**Solution:**
Frontend must send: `Authorization: Bearer <token>`

### Error: "User not found in database"

**Cause:** User exists in Cognito but not in your database

**Solution:**
Implement user sync (Just-in-Time provisioning or manual sync)

---

## 📚 Additional Resources

- **Quick Reference:** `app/auth/README.md`
- **Detailed Guide:** `docs/authentication-usage.md`
- **FastAPI Security:** https://fastapi.tiangolo.com/tutorial/security/
- **Cognito Docs:** https://docs.aws.amazon.com/cognito/

---

## ✨ You're All Set!

1. ✅ Add Cognito config to `.env`
2. ✅ Restart your server
3. ✅ Add `Depends(get_current_user)` to routes you want to protect
4. ✅ Test with JWT from frontend

**Need help?** Check the documentation or ask questions!
