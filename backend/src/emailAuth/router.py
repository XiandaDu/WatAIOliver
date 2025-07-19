from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .models import (
    EmailSignupRequest, 
    EmailLoginRequest, 
    PasswordResetRequest, 
    PasswordUpdateRequest,
    AuthResponse
)
from .service import EmailAuthService
import logging

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)

router = APIRouter(
    prefix='/auth/email',
    tags=['email-auth']
)

@router.post("/signup", response_model=AuthResponse)
async def signup_with_email(signup_data: EmailSignupRequest):
    """
    Sign up a new user with email and password
    """
    try:
        result = await EmailAuthService.signup_with_email(signup_data)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during signup"
        )

@router.post("/login", response_model=AuthResponse)
async def login_with_email(login_data: EmailLoginRequest):
    """
    Login user with email and password
    """
    try:
        result = await EmailAuthService.login_with_email(login_data)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result.message
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )

@router.post("/logout", response_model=AuthResponse)
async def logout():
    """
    Logout current user
    """
    try:
        result = await EmailAuthService.logout()
        return result
    except Exception as e:
        logger.error(f"Logout endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during logout"
        )

@router.post("/reset-password", response_model=AuthResponse)
async def reset_password(reset_data: PasswordResetRequest):
    """
    Send password reset email
    """
    try:
        result = await EmailAuthService.reset_password(reset_data)
        return result
    except Exception as e:
        logger.error(f"Password reset endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during password reset"
        )

@router.post("/update-password", response_model=AuthResponse)
async def update_password(
    password_data: PasswordUpdateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update user password (requires authentication)
    """
    try:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        result = await EmailAuthService.update_password(password_data)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password update endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during password update"
        )

@router.get("/me")
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get current authenticated user information
    """
    try:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        result = await EmailAuthService.get_current_user()
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result["message"]
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current user endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error getting user info"
        )

@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Refresh the current session token
    """
    try:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        result = await EmailAuthService.refresh_token()
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result.message
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during token refresh"
        )

@router.get("/health")
async def health_check():
    """
    Health check endpoint for email auth service
    """
    return {"status": "healthy", "service": "email-auth"}