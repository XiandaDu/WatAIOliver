import logging
from fastapi import APIRouter, HTTPException, Response, Request
from pydantic import BaseModel
from src.supabaseClient import supabase
from typing import Optional
import traceback
from src.user import service as user_service
from src.user.models import UserCreate

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

@router.options("/{path:path}")
async def options_handler(path: str):
    return Response(
        content="",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept",
        }
    )

@router.get("/signin/google")
async def google_signin(redirect_to: Optional[str] = None):
    """Get Google OAuth URL"""
    try:
        logger.info(f"Starting Google sign-in, redirect_to: {redirect_to}")
        
        # Change the URL as needed for your frontend
        if not redirect_to:
            redirect_to = "http://localhost:5173/login"
        
        logger.info(f"Using redirect_to: {redirect_to}")
        
        # Use Supabase to get the Google OAuth URL
        response = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": redirect_to
            }
        })
        
        # Log the response structure in extreme detail
        logger.info(f"Response type: {type(response)}")
        logger.info(f"Response dir: {dir(response)}")
        
        # Try different ways to extract data based on response type
        if hasattr(response, "model_dump"):
            logger.info(f"model_dump output: {response.model_dump()}")
        
        # Try to get raw data if it's an object with a dict representation
        try:
            raw_dict = dict(response)
            logger.info(f"Dict representation: {raw_dict}")
        except:
            logger.info("Could not convert response to dict directly")
            
        # More verbose format for the final returned data
        final_response = None
        
        # Process response based on type
        if hasattr(response, "model_dump") and isinstance(response.model_dump(), dict):
            model_data = response.model_dump()
            logger.info(f"Using model_dump path: {model_data}")
            final_response = model_data
        elif isinstance(response, dict) and "data" in response and "url" in response.get("data", {}):
            logger.info(f"Using standard dict path with nested url")
            final_response = response
        elif isinstance(response, dict) and "url" in response:
            logger.info(f"Using dict with direct url path")
            final_response = {"data": {"url": response["url"]}}
        else:
            logger.info(f"No recognized response format!")
            # Hard-coded response for testing (remove in production)
            if hasattr(response, '__dict__'):
                attrs = {key: getattr(response, key) for key in dir(response) 
                        if not key.startswith('__')}
                logger.info(f"Object attributes: {attrs}")
            
            # Last resort: try to extract URL using string operations
            response_str = str(response)
            if "url" in response_str and "http" in response_str:
                import re
                url_match = re.search(r'(https?://\S+)', response_str)
                if url_match:
                    extracted_url = url_match.group(0).rstrip('\'",;:.')
                    logger.info(f"Extracted URL from string: {extracted_url}")
                    final_response = {"data": {"url": extracted_url}}
            
            if not final_response:
                logger.error(f"Unexpected response structure: {response}")
                raise HTTPException(
                    status_code=500, 
                    detail="Failed to generate authentication URL"
                )
        
        logger.info(f"Final response being returned: {final_response}")
        return final_response
            
    except Exception as e:
        logger.error(f"Error in Google sign-in: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error initiating Google sign-in: {str(e)}")

@router.get("/callback")
async def auth_callback(code: str = None, state: str = None):
    """Handle OAuth callback from Google"""
    try:
        logger.info(f"Received callback with code: {code[:10] if code else None}... state: {state}")
        
        # Exchange the code for a session
        result = supabase.auth.exchange_code_for_session({"auth_code": code})
        logger.info(f"Auth exchange result type: {type(result)}")
        
        if result and hasattr(result, "session"):
            # Get user details from the session
            user = result.session.user
            logger.info(f"User authenticated: {user.email}")
            
            # Create user record in the user table if it doesn't exist
            try:
                # First check if user already exists
                user_exists = user_service.check_user_exists(user.id)
                
                if not user_exists:
                    # Create new user record with username instead of nickname
                    # Extract username from email or use full_name from metadata
                    username = user.user_metadata.get("full_name", user.email.split("@")[0])
                    
                    new_user = UserCreate(
                        user_id=user.id,
                        username=username,
                        email=user.email,
                        role="student"  # Default role
                    )
                    user_service.create_user(new_user)
                    logger.info(f"Created new user record for {user.email}")
                else:
                    logger.info(f"User {user.email} already exists in users table")
                    
            except Exception as user_error:
                logger.error(f"Error creating user record: {user_error}")
                logger.error(traceback.format_exc())
                # Continue even if user record creation fails
            
            # Redirect to frontend root instead of /login
            redirect_url = "http://localhost:5173#success=true"  # Removed /login
            logger.info(f"Redirecting to: {redirect_url}")
            return Response(status_code=307, headers={"Location": redirect_url})
        else:
            logger.error("Failed to exchange code for session")
            raise HTTPException(status_code=400, detail="Authentication failed")
            
    except Exception as e:
        logger.error(f"Callback error: {str(e)}")
        logger.error(traceback.format_exc())
        # Redirect to frontend root with error
        redirect_url = "http://localhost:5173/login#error=auth_error" 
        return Response(status_code=307, headers={"Location": redirect_url})

@router.post("/signout")
async def signout():
    try:
        response = supabase.auth.sign_out()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/session")
async def get_session():
    try:
        response = supabase.auth.get_session()
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))