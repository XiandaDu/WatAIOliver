# Email Authentication with Supabase

This module provides complete email authentication functionality using Supabase Auth.

## Features

- ✅ User registration with email/password
- ✅ User login with email/password  
- ✅ Password reset via email
- ✅ Password update for authenticated users
- ✅ User logout
- ✅ JWT token refresh
- ✅ User profile management
- ✅ Role-based access control
- ✅ Authentication middleware

## Setup

### 1. Supabase Configuration

Make sure your Supabase project has email authentication enabled:

1. Go to your Supabase dashboard
2. Navigate to Authentication > Settings
3. Enable "Email" provider
4. Configure email templates (optional)
5. Set up email delivery (SMTP) for production

### 2. Environment Variables

Ensure your `.env` file contains:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

### 3. Database Schema

The system expects a `users` table with the following structure:

```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id),
    email VARCHAR NOT NULL,
    username VARCHAR,
    full_name VARCHAR,
    role VARCHAR DEFAULT 'student',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## API Endpoints

All endpoints are under the `/auth/email` prefix.

### Authentication Endpoints

#### POST `/auth/email/signup`
Register a new user with email and password.

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "securepassword123",
    "username": "johndoe",
    "full_name": "John Doe"
}
```

**Response:**
```json
{
    "success": true,
    "message": "User created successfully. Please check your email for verification.",
    "user": {
        "id": "uuid",
        "email": "user@example.com",
        "username": "johndoe",
        "email_confirmed": false
    },
    "access_token": "jwt_token",
    "refresh_token": "refresh_token"
}
```

#### POST `/auth/email/login`
Login with email and password.

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "securepassword123"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Login successful",
    "user": {
        "id": "uuid",
        "email": "user@example.com",
        "username": "johndoe",
        "full_name": "John Doe",
        "role": "student",
        "email_confirmed": true,
        "last_sign_in": "2025-01-18T12:00:00Z"
    },
    "access_token": "jwt_token",
    "refresh_token": "refresh_token"
}
```

#### POST `/auth/email/logout`
Logout the current user.

**Response:**
```json
{
    "success": true,
    "message": "Logged out successfully"
}
```

#### POST `/auth/email/reset-password`
Send password reset email.

**Request Body:**
```json
{
    "email": "user@example.com"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Password reset email sent. Please check your inbox."
}
```

#### POST `/auth/email/update-password`
Update password (requires authentication).

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Request Body:**
```json
{
    "new_password": "newsecurepassword123"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Password updated successfully"
}
```

### User Information Endpoints

#### GET `/auth/email/me`
Get current user information (requires authentication).

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
    "success": true,
    "user": {
        "id": "uuid",
        "email": "user@example.com",
        "username": "johndoe",
        "full_name": "John Doe",
        "role": "student",
        "email_confirmed": true,
        "created_at": "2025-01-18T10:00:00Z",
        "last_sign_in": "2025-01-18T12:00:00Z"
    }
}
```

#### POST `/auth/email/refresh`
Refresh JWT token (requires authentication).

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
    "success": true,
    "message": "Token refreshed successfully",
    "access_token": "new_jwt_token",
    "refresh_token": "new_refresh_token"
}
```

## Usage in Other Routes

### Basic Authentication

```python
from fastapi import Depends
from src.emailAuth.auth_utils import get_current_user

@router.get("/protected")
async def protected_route(current_user: dict = Depends(get_current_user)):
    return {"message": f"Hello {current_user['username']}!"}
```

### Role-Based Access Control

```python
from src.emailAuth.auth_utils import require_admin, require_instructor, require_student

@router.get("/admin-only")
async def admin_only(current_user: dict = Depends(require_admin)):
    return {"message": "Admin access granted"}

@router.get("/instructor-or-admin")
async def instructor_route(current_user: dict = Depends(require_instructor)):
    return {"message": "Instructor/Admin access granted"}

@router.get("/any-authenticated-user")
async def student_route(current_user: dict = Depends(require_student)):
    return {"message": "Authenticated user access granted"}
```

### Optional Authentication

```python
from src.emailAuth.auth_utils import get_current_user_optional

@router.get("/optional-auth")
async def optional_auth_route(current_user: dict = Depends(get_current_user_optional)):
    if current_user:
        return {"message": f"Hello {current_user['username']}!"}
    else:
        return {"message": "Hello anonymous user!"}
```

## Frontend Integration

### JavaScript/TypeScript Example

```javascript
// Login
const login = async (email, password) => {
    const response = await fetch('/auth/email/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
    });
    
    const data = await response.json();
    if (data.success) {
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
    }
    return data;
};

// Make authenticated requests
const makeAuthenticatedRequest = async (url, options = {}) => {
    const token = localStorage.getItem('access_token');
    return fetch(url, {
        ...options,
        headers: {
            ...options.headers,
            'Authorization': `Bearer ${token}`,
        },
    });
};

// Get current user
const getCurrentUser = async () => {
    const response = await makeAuthenticatedRequest('/auth/email/me');
    return response.json();
};
```

## Error Handling

All endpoints return standardized error responses:

```json
{
    "detail": "Error message here"
}
```

Common HTTP status codes:
- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Authentication required or invalid credentials
- `403 Forbidden`: Insufficient permissions
- `500 Internal Server Error`: Server-side error

## Security Considerations

1. **HTTPS Only**: Always use HTTPS in production
2. **Token Storage**: Store JWT tokens securely (httpOnly cookies recommended)
3. **Token Expiration**: Implement proper token refresh logic
4. **Rate Limiting**: Consider implementing rate limiting for auth endpoints
5. **Email Verification**: Encourage users to verify their email addresses
6. **Strong Passwords**: Implement password strength requirements on frontend

## Testing

You can test the endpoints using curl:

```bash
# Signup
curl -X POST "http://localhost:8000/auth/email/signup" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123","username":"testuser"}'

# Login
curl -X POST "http://localhost:8000/auth/email/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# Get current user (replace TOKEN with actual JWT)
curl -X GET "http://localhost:8000/auth/email/me" \
  -H "Authorization: Bearer TOKEN"
```
