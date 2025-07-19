from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.supabaseClient import supabase
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Dependency to get current authenticated user from JWT token
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Verify the JWT token with Supabase
        user_response = supabase.auth.get_user(credentials.credentials)
        
        if not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user profile from database
        user_profile = supabase.table("users").select("*").eq("user_id", user_response.user.id).execute()
        
        user_data = {
            "id": user_response.user.id,
            "email": user_response.user.email,
            "email_confirmed": user_response.user.email_confirmed_at is not None,
            "created_at": user_response.user.created_at,
            "last_sign_in": user_response.user.last_sign_in_at
        }
        
        # Add profile data if available
        if user_profile.data:
            profile = user_profile.data[0]
            user_data.update({
                "username": profile.get("username"),
                "full_name": profile.get("full_name"),
                "role": profile.get("role")
            })
        
        return user_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user_optional(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[Dict[str, Any]]:
    """
    Optional dependency to get current authenticated user
    Returns None if no valid authentication is provided
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None

def require_roles(allowed_roles: list):
    """
    Decorator factory to require specific user roles
    """
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_role = current_user.get("role")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {allowed_roles}"
            )
        return current_user
    return role_checker

# Common role checkers
require_admin = require_roles(["admin"])
require_instructor = require_roles(["admin", "instructor"])
require_student = require_roles(["admin", "instructor", "student"])
