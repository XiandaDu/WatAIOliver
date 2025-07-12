from fastapi import APIRouter, Request, UploadFile, File, Form, Query, HTTPException, status
from . import service
from src.supabaseClient import supabase
import logging
from .models import UserCreate  # Add the missing import

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix='/user',
    tags=['user']
)

@router.get("/")
async def get_user_info():
    """Get current user info from the session"""
    try:
        # First get the current user from auth
        try:
            session = supabase.auth.get_session()
            if not session or not session.user:
                return {"error": "Not authenticated"}
            
            user_id = session.user.id
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return {"error": "Error retrieving session"}
        
        # Then get user details from database
        return service.get_user_info(user_id)
    except Exception as e:
        logger.error(f"Error in get_user_info: {e}")
        return {"error": str(e)}
    
@router.post("/create")
async def create_user(user: UserCreate):
    """Create a new user"""
    try:
        return service.create_user(user)
    except Exception as e:
        logger.error(f"Error in create_user endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/login")
async def login():
    return service.login()

@router.get("/logout")
async def logout():
    return service.logout()






