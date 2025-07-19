from src.supabaseClient import supabase
from .models import EmailSignupRequest, EmailLoginRequest, PasswordResetRequest, PasswordUpdateRequest, AuthResponse
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class EmailAuthService:
    @staticmethod
    async def signup_with_email(signup_data: EmailSignupRequest) -> AuthResponse:
        """
        Sign up a new user with email and password
        """
        try:
            # Sign up with Supabase Auth
            auth_response = supabase.auth.sign_up({
                "email": signup_data.email,
                "password": signup_data.password,
                "options": {
                    "data": {
                        "username": signup_data.username,
                        "full_name": signup_data.full_name
                    }
                }
            })
            
            if auth_response.user:
                # Create user profile in your users table
                user_profile = {
                    "user_id": auth_response.user.id,
                    "email": signup_data.email,
                    "username": signup_data.username or signup_data.email.split('@')[0],
                    "full_name": signup_data.full_name,
                    "role": "student"  # Default role
                }
                
                # Insert into users table
                try:
                    supabase.table("users").insert(user_profile).execute()
                except Exception as db_error:
                    logger.error(f"Error creating user profile: {db_error}")
                    # Continue even if profile creation fails
                
                return AuthResponse(
                    success=True,
                    message="User created successfully. Please check your email for verification.",
                    user={
                        "id": auth_response.user.id,
                        "email": auth_response.user.email,
                        "username": signup_data.username,
                        "email_confirmed": auth_response.user.email_confirmed_at is not None
                    },
                    access_token=auth_response.session.access_token if auth_response.session else None,
                    refresh_token=auth_response.session.refresh_token if auth_response.session else None
                )
            else:
                return AuthResponse(
                    success=False,
                    message="Failed to create user"
                )
                
        except Exception as e:
            logger.error(f"Signup error: {e}")
            return AuthResponse(
                success=False,
                message=f"Signup failed: {str(e)}"
            )

    @staticmethod
    async def login_with_email(login_data: EmailLoginRequest) -> AuthResponse:
        """
        Login user with email and password
        """
        try:
            # Sign in with Supabase Auth
            auth_response = supabase.auth.sign_in_with_password({
                "email": login_data.email,
                "password": login_data.password
            })
            
            if auth_response.user and auth_response.session:
                # Get user profile from database
                user_profile = supabase.table("users").select("*").eq("user_id", auth_response.user.id).execute()
                
                user_data = {
                    "id": auth_response.user.id,
                    "email": auth_response.user.email,
                    "email_confirmed": auth_response.user.email_confirmed_at is not None,
                    "last_sign_in": auth_response.user.last_sign_in_at
                }
                
                # Add profile data if available
                if user_profile.data:
                    profile = user_profile.data[0]
                    user_data.update({
                        "username": profile.get("username"),
                        "full_name": profile.get("full_name"),
                        "role": profile.get("role")
                    })
                
                return AuthResponse(
                    success=True,
                    message="Login successful",
                    user=user_data,
                    access_token=auth_response.session.access_token,
                    refresh_token=auth_response.session.refresh_token
                )
            else:
                return AuthResponse(
                    success=False,
                    message="Invalid email or password"
                )
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return AuthResponse(
                success=False,
                message=f"Login failed: {str(e)}"
            )

    @staticmethod
    async def logout() -> AuthResponse:
        """
        Logout current user
        """
        try:
            supabase.auth.sign_out()
            return AuthResponse(
                success=True,
                message="Logged out successfully"
            )
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return AuthResponse(
                success=False,
                message=f"Logout failed: {str(e)}"
            )

    @staticmethod
    async def reset_password(reset_data: PasswordResetRequest) -> AuthResponse:
        """
        Send password reset email
        """
        try:
            supabase.auth.reset_password_email(reset_data.email)
            return AuthResponse(
                success=True,
                message="Password reset email sent. Please check your inbox."
            )
        except Exception as e:
            logger.error(f"Password reset error: {e}")
            return AuthResponse(
                success=False,
                message=f"Failed to send reset email: {str(e)}"
            )

    @staticmethod
    async def update_password(password_data: PasswordUpdateRequest) -> AuthResponse:
        """
        Update user password (requires valid session)
        """
        try:
            auth_response = supabase.auth.update_user({
                "password": password_data.new_password
            })
            
            if auth_response.user:
                return AuthResponse(
                    success=True,
                    message="Password updated successfully"
                )
            else:
                return AuthResponse(
                    success=False,
                    message="Failed to update password"
                )
        except Exception as e:
            logger.error(f"Password update error: {e}")
            return AuthResponse(
                success=False,
                message=f"Password update failed: {str(e)}"
            )

    @staticmethod
    async def get_current_user() -> Dict[str, Any]:
        """
        Get current authenticated user
        """
        try:
            user = supabase.auth.get_user()
            if user.user:
                # Get user profile from database
                user_profile = supabase.table("users").select("*").eq("user_id", user.user.id).execute()
                
                user_data = {
                    "id": user.user.id,
                    "email": user.user.email,
                    "email_confirmed": user.user.email_confirmed_at is not None,
                    "created_at": user.user.created_at,
                    "last_sign_in": user.user.last_sign_in_at
                }
                
                # Add profile data if available
                if user_profile.data:
                    profile = user_profile.data[0]
                    user_data.update({
                        "username": profile.get("username"),
                        "full_name": profile.get("full_name"),
                        "role": profile.get("role")
                    })
                
                return {"success": True, "user": user_data}
            else:
                return {"success": False, "message": "No authenticated user"}
        except Exception as e:
            logger.error(f"Get current user error: {e}")
            return {"success": False, "message": f"Error getting user: {str(e)}"}

    @staticmethod
    async def refresh_token() -> AuthResponse:
        """
        Refresh the current session token
        """
        try:
            auth_response = supabase.auth.refresh_session()
            if auth_response.session:
                return AuthResponse(
                    success=True,
                    message="Token refreshed successfully",
                    access_token=auth_response.session.access_token,
                    refresh_token=auth_response.session.refresh_token
                )
            else:
                return AuthResponse(
                    success=False,
                    message="Failed to refresh token"
                )
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return AuthResponse(
                success=False,
                message=f"Token refresh failed: {str(e)}"
            )
