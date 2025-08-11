from fastapi import APIRouter, HTTPException, status, Depends
from .models import GoogleTokenRequest, AuthResponse, RoleUpdateRequest, AccountStatusRequest
from .service import AuthService
from .middleware import auth_required, admin_required
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix='/auth',
    tags=['authentication']
)

@router.post("/google", response_model=AuthResponse)
async def authenticate_with_google(token_request: GoogleTokenRequest):
    try:
        result = await AuthService.authenticate_with_google(token_request)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google authentication endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during authentication"
        )

@router.post("/logout", response_model=AuthResponse)
async def logout():
    try:
        result = await AuthService.logout()
        return result
    except Exception as e:
        logger.error(f"Logout endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during logout"
        )

@router.get("/me")
async def get_current_user_info(current_user = Depends(auth_required)):
    return {
        "success": True,
        "user": current_user
    }

@router.post("/update-role", response_model=AuthResponse)
async def update_user_role(
    role_request: RoleUpdateRequest, 
    current_user = Depends(admin_required)
):
    try:
        result = await AuthService.update_user_role(role_request)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update role endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during role update"
        )

@router.post("/update-status", response_model=AuthResponse)
async def update_account_status(
    status_request: AccountStatusRequest, 
    current_user = Depends(admin_required)
):
    try:
        result = await AuthService.update_account_status(status_request.user_id, status_request.status)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update account status endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during status update"
        )

@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "authentication"}