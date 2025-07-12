from fastapi import Depends, FastAPI, Request, UploadFile, File, Form, Query, HTTPException, status
from .models import UserBase, UserCreate, UserUpdate
from src.supabaseClient import supabase
import logging
import traceback

logger = logging.getLogger(__name__)

def get_user_info(user_id: str = None):
    """Get user information from the database"""
    try:
        if not user_id:
            # Get current user from supabase auth session
            # This assumes the request has the auth session cookie
            user = supabase.auth.get_session()
            if user and user.user:
                user_id = user.user.id
            else:
                return {"error": "Not authenticated"}
                
        # Query the users table
        result = supabase.table("users").select("*").eq("user_id", user_id).execute()
        
        if result and len(result.data) > 0:
            return {"data": result.data[0]}
        else:
            return {"error": "User not found"}
            
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        return {"error": str(e)}

def check_user_exists(user_id: str) -> bool:
    """Check if user exists in the users table"""
    try:
        logger.info(f"Checking if user exists: {user_id}")
        result = supabase.table("users").select("user_id").eq("user_id", user_id).execute()
        exists = result and len(result.data) > 0
        logger.info(f"User exists: {exists}, result: {result}")
        return exists
    except Exception as e:
        logger.error(f"Error checking user existence: {e}")
        logger.error(traceback.format_exc())  # Add this for better error logging
        return False

def create_user(user: UserCreate):
    """Create a new user in the users table"""
    try:
        logger.info(f"Creating user: {user.model_dump()}")
        
        # Convert to dict for Supabase
        user_data = {
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
        
        logger.info(f"User data for insert: {user_data}")
        
        # Insert into users table
        result = supabase.table("users").insert(user_data).execute()
        
        logger.info(f"Insert result: {result}")
        
        if result and result.data:
            return {"data": result.data[0]}
        else:
            raise HTTPException(status_code=500, detail="Failed to create user")
            
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        logger.error(traceback.format_exc())  # Add this for better error logging
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

def update_user(user_id: str, user_update: UserUpdate):
    """Update user details"""
    try:
        # Convert to dict and remove None values
        update_data = {k: v for k, v in user_update.model_dump().items() if v is not None}
        
        # Add updated_at timestamp
        update_data["updated_at"] = datetime.now()
        
        # Update user
        result = supabase.table("users").update(update_data).eq("user_id", user_id).execute()
        
        if result and result.data:
            return {"data": result.data[0]}
        else:
            raise HTTPException(status_code=404, detail="User not found or update failed")
            
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating user: {str(e)}")

def login():
    """Redirects to Google login - this is handled in auth router"""
    return {"message": "Use auth/signin/google endpoint for login"}