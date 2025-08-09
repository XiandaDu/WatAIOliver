import os
import requests
from typing import Optional, Dict, Any
from src.supabaseClient import supabase
from .models import AuthUser, GoogleTokenRequest, AuthResponse, RoleUpdateRequest
import logging

logger = logging.getLogger(__name__)

class AuthService:
    @staticmethod
    def validate_email_domain(email: str) -> bool:
        allowed_domains = ["@gmail.com", "@uwaterloo.ca"]
        return any(email.lower().endswith(domain) for domain in allowed_domains)
    
    @staticmethod
    async def authenticate_with_google(token_request: GoogleTokenRequest) -> AuthResponse:
        try:
            # Get user info from Google using the access token
            google_response = requests.get(
                'https://www.googleapis.com/oauth2/v3/userinfo',
                headers={'Authorization': f'Bearer {token_request.access_token}'},
                timeout=10
            )
            
            if google_response.status_code != 200:
                return AuthResponse(
                    success=False,
                    message="Invalid Google access token"
                )
            
            google_user = google_response.json()
            email = google_user.get('email')
            
            if not email:
                return AuthResponse(
                    success=False,
                    message="Could not retrieve email from Google"
                )
            
            # Validate email domain
            if not AuthService.validate_email_domain(email):
                return AuthResponse(
                    success=False,
                    message="Please use a valid @gmail.com or @uwaterloo.ca email address"
                )
            
            # Check if user exists in Supabase Auth
            try:
                logger.info(f"Looking up existing user for email: {email}")
                # Try to get existing user by searching through users
                users_response = supabase.auth.admin.list_users()
                logger.info(f"Retrieved {len(users_response)} users from Supabase Auth")
                existing_user = None
                for user in users_response:
                    if user.email == email:
                        existing_user = user
                        logger.info(f"Found existing user: {user.id} ({user.email})")
                        break
                
                if not existing_user:
                    logger.info(f"No existing user found for email: {email}")
                
                if existing_user:
                    # User exists, just get their profile and return auth data
                    logger.info(f"Processing existing user login: {existing_user.id}")
                    
                    # Get user profile from database
                    logger.info(f"Looking up user profile for user_id: {existing_user.id}")
                    profile_response = supabase.table("users").select("*").eq("user_id", existing_user.id).execute()
                    
                    if not profile_response.data:
                        logger.info(f"No profile found for user {existing_user.id}, creating new profile")
                        # Create user profile if it doesn't exist
                        await AuthService._create_user_profile(existing_user, google_user, token_request.account_type)
                        # Refetch the profile
                        profile_response = supabase.table("users").select("*").eq("user_id", existing_user.id).execute()
                        logger.info(f"Profile created and retrieved for user {existing_user.id}")
                    else:
                        logger.info(f"Found existing profile for user {existing_user.id}: {profile_response.data[0].get('username')}")
                    
                    profile = profile_response.data[0] if profile_response.data else None
                    
                    auth_user = AuthUser(
                        id=existing_user.id,
                        email=existing_user.email,
                        username=profile.get("username", google_user.get("name", email.split("@")[0])) if profile else google_user.get("name", email.split("@")[0]),
                        full_name=profile.get("full_name", google_user.get("name")) if profile else google_user.get("name"),
                        role=profile.get("role", "student") if profile else "student",
                        email_confirmed=existing_user.email_confirmed_at is not None,
                        created_at=existing_user.created_at,
                        last_sign_in=existing_user.last_sign_in_at
                    )
                    
                    logger.info(f"Successful authentication for existing user: {existing_user.email}")
                    return AuthResponse(
                        success=True,
                        message="Welcome back! Authentication successful",
                        user=auth_user,
                        access_token=token_request.access_token  # Use the Google access token
                    )
                
                else:
                    # User doesn't exist, create new user
                    logger.info(f"Creating new user for email: {email}")
                    return await AuthService._create_new_google_user(google_user, token_request.account_type)
                    
            except Exception as supabase_error:
                logger.error(f"Supabase auth error: {supabase_error}")
                # If user doesn't exist in Supabase Auth, create them
                return await AuthService._create_new_google_user(google_user, token_request.account_type)
            
        except requests.RequestException as e:
            logger.error(f"Google API request failed: {e}")
            return AuthResponse(
                success=False,
                message="Failed to authenticate with Google"
            )
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return AuthResponse(
                success=False,
                message="Authentication failed"
            )
    
    @staticmethod
    async def _create_new_google_user(google_user: Dict[str, Any], account_type: str) -> AuthResponse:
        try:
            email = google_user.get('email')
            name = google_user.get('name', email.split('@')[0])
            
            logger.info(f"Creating new Supabase Auth user for: {email}")
            # Create user in Supabase Auth
            auth_response = supabase.auth.admin.create_user({
                "email": email,
                "email_confirm": True,  # Auto-confirm Google users
                "user_metadata": {
                    "full_name": name,
                    "provider": "google"
                }
            })
            
            if not auth_response.user:
                logger.error(f"Failed to create Supabase Auth user for: {email}")
                return AuthResponse(
                    success=False,
                    message="Failed to create user account"
                )
            
            logger.info(f"Successfully created Supabase Auth user: {auth_response.user.id} ({email})")
            
            # Create user profile
            await AuthService._create_user_profile(auth_response.user, google_user, account_type)
            
            auth_user = AuthUser(
                id=auth_response.user.id,
                email=email,
                username=name,
                full_name=name,
                role=account_type if account_type in ["student", "instructor"] else "student",
                courses=[],
                email_confirmed=True,
                created_at=auth_response.user.created_at
            )
            
            logger.info(f"Successfully created complete user account for: {email}")
            return AuthResponse(
                success=True,
                message="Account created successfully",
                user=auth_user
            )
            
        except Exception as e:
            logger.error(f"User creation error: {e}")
            return AuthResponse(
                success=False,
                message="Failed to create user account"
            )
    
    @staticmethod
    async def _create_user_profile(supabase_user, google_user: Dict[str, Any], account_type: str):
        try:
            email = google_user.get('email')
            profile_data = {
                "user_id": supabase_user.id,
                "email": email,
                "username": google_user.get('name', email.split('@')[0]),
                "full_name": google_user.get('name'),
                "role": account_type if account_type in ["student", "instructor"] else "student",
                "courses": [],
                "account_type": "active"
            }
            
            logger.info(f"Creating user profile in database for: {email} (user_id: {supabase_user.id})")
            logger.info(f"Profile data: {profile_data}")
            
            result = supabase.table("users").insert(profile_data).execute()
            logger.info(f"Successfully created user profile for {email}: {result.data}")
            
        except Exception as e:
            logger.error(f"Failed to create user profile for {google_user.get('email')}: {e}")
            raise
    
    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[AuthUser]:
        try:
            logger.info(f"Looking up user by ID: {user_id}")
            # Get user from Supabase Auth
            auth_response = supabase.auth.admin.get_user_by_id(user_id)
            if not auth_response.user:
                logger.info(f"No user found in Supabase Auth for ID: {user_id}")
                return None
            
            # Get user profile from database
            profile_response = supabase.table("users").select("*").eq("user_id", user_id).execute()
            profile = profile_response.data[0] if profile_response.data else None
            
            if profile:
                logger.info(f"Found user profile for {user_id}: {profile.get('email')}")
            else:
                logger.info(f"No profile found for user {user_id}")
            
            return AuthUser(
                id=auth_response.user.id,
                email=auth_response.user.email,
                username=profile.get("username", auth_response.user.email.split("@")[0]) if profile else auth_response.user.email.split("@")[0],
                full_name=profile.get("full_name") if profile else None,
                role=profile.get("role", "student") if profile else "student",
                courses=profile.get("courses", []) if profile else [],
                email_confirmed=auth_response.user.email_confirmed_at is not None,
                created_at=auth_response.user.created_at,
                last_sign_in=auth_response.user.last_sign_in_at
            )
            
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None
    
    @staticmethod
    async def update_user_role(role_request: RoleUpdateRequest) -> AuthResponse:
        try:
            logger.info(f"Updating role for user {role_request.user_id} to {role_request.new_role}")
            # Update role in users table
            update_response = supabase.table("users").update({
                "role": role_request.new_role
            }).eq("user_id", role_request.user_id).execute()
            
            if not update_response.data:
                logger.error(f"Failed to update role for user {role_request.user_id}: no data returned")
                return AuthResponse(
                    success=False,
                    message="User not found or update failed"
                )
            
            logger.info(f"Successfully updated role for user {role_request.user_id} to {role_request.new_role}")
            return AuthResponse(
                success=True,
                message=f"User role updated to {role_request.new_role}"
            )
            
        except Exception as e:
            logger.error(f"Error updating user role: {e}")
            return AuthResponse(
                success=False,
                message="Failed to update user role"
            )
    
    @staticmethod
    async def update_account_status(user_id: str, status: str) -> AuthResponse:
        try:
            if status not in ["active", "blocked"]:
                return AuthResponse(
                    success=False,
                    message="Invalid status. Must be 'active' or 'blocked'"
                )
            
            logger.info(f"Updating account status for user {user_id} to {status}")
            update_response = supabase.table("users").update({
                "account_type": status
            }).eq("user_id", user_id).execute()
            
            if not update_response.data:
                logger.error(f"Failed to update account status for user {user_id}: no data returned")
                return AuthResponse(
                    success=False,
                    message="User not found or update failed"
                )
            
            logger.info(f"Successfully updated account status for user {user_id} to {status}")
            return AuthResponse(
                success=True,
                message=f"Account {status}"
            )
            
        except Exception as e:
            logger.error(f"Error updating account status: {e}")
            return AuthResponse(
                success=False,
                message="Failed to update account status"
            )
    
    @staticmethod
    async def logout() -> AuthResponse:
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
                message="Logout failed"
            )