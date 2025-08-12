from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.supabaseClient import supabase
from .models import AuthUser
from .service import AuthService
import logging
from typing import Optional

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> AuthUser:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        import requests
        google_response = requests.get(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            headers={'Authorization': f'Bearer {credentials.credentials}'},
            timeout=10
        )
        
        if google_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google access token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        google_user = google_response.json()
        email = google_user.get('email')
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google user data",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        users_response = supabase.auth.admin.list_users()
        for user in users_response:
            if user.email == email:
                auth_user = await AuthService.get_user_by_id(user.id)
                if auth_user:
                    try:
                        profile_response = supabase.table("users").select("account_type").eq("user_id", user.id).execute()
                        if profile_response.data and profile_response.data[0].get("account_type") == "blocked":
                            raise HTTPException(
                                status_code=status.HTTP_403_FORBIDDEN,
                                detail="Account has been suspended",
                            )
                    except Exception:
                        pass
                    logger.info(f"Authenticated user: {email}")
                    return auth_user
                break
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user_optional(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[AuthUser]:
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None

def auth_required(current_user: AuthUser = Depends(get_current_user)) -> AuthUser:
    return current_user

def instructor_required(current_user: AuthUser = Depends(get_current_user)) -> AuthUser:
    if current_user.role not in ["instructor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Instructor access required"
        )
    return current_user

def admin_required(current_user: AuthUser = Depends(get_current_user)) -> AuthUser:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user