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
    async def _get_google_user_info(access_token: str) -> Dict[str, Any]:
        """Get user info from Google API"""
        google_response = requests.get(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10
        )
        
        if google_response.status_code != 200:
            raise Exception("Invalid Google access token")
        
        google_user = google_response.json()
        email = google_user.get('email')
        
        if not email:
            raise Exception("Could not retrieve email from Google")
        
        return google_user
    
    @staticmethod
    async def _find_existing_user(email: str):
        """Find existing user by email"""
        users_response = supabase.auth.admin.list_users()
        for user in users_response:
            if user.email == email:
                return user
        return None
    
    @staticmethod
    async def _handle_existing_user(existing_user, google_user: Dict[str, Any], token_request: GoogleTokenRequest) -> AuthResponse:
        """Handle login for existing user"""
        logger.info(f"Processing existing user login: {existing_user.id}")
        
        # Get or create user profile
        profile_response = supabase.table("users").select("*").eq("user_id", existing_user.id).execute()
        
        if not profile_response.data:
            await AuthService._create_user_profile(existing_user, google_user, token_request.account_type)
            profile_response = supabase.table("users").select("*").eq("user_id", existing_user.id).execute()
        else:
            # Update role based on login request
            await AuthService._update_user_role_on_login(existing_user.id, profile_response.data[0], token_request.account_type)
            profile_response = supabase.table("users").select("*").eq("user_id", existing_user.id).execute()
        
        profile = profile_response.data[0] if profile_response.data else None
        login_role = token_request.account_type if token_request.account_type in ["student", "instructor"] else "student"
        
        auth_user = AuthUser(
            id=existing_user.id,
            email=existing_user.email,
            username=profile.get("username", google_user.get("name", existing_user.email.split("@")[0])) if profile else google_user.get("name", existing_user.email.split("@")[0]),
            full_name=profile.get("full_name", google_user.get("name")) if profile else google_user.get("name"),
            role=login_role,
            email_confirmed=existing_user.email_confirmed_at is not None,
            created_at=existing_user.created_at,
            last_sign_in=existing_user.last_sign_in_at
        )
        
        return AuthResponse(
            success=True,
            message="Welcome back! Authentication successful",
            user=auth_user,
            access_token=token_request.access_token
        )
    
    @staticmethod
    async def _update_user_role_on_login(user_id: str, profile: Dict[str, Any], requested_role: str):
        """Update user role if different from current"""
        normalized_role = requested_role if requested_role in ["student", "instructor"] else "student"
        current_role = profile.get('role', 'student')
        
        if normalized_role != current_role:
            logger.info(f"Updating user role from {current_role} to {normalized_role}")
            supabase.table("users").update({"role": normalized_role}).eq("user_id", user_id).execute()
    
    @staticmethod
    async def authenticate_with_google(token_request: GoogleTokenRequest) -> AuthResponse:
        try:
            # Get user info from Google
            google_user = await AuthService._get_google_user_info(token_request.access_token)
            email = google_user.get('email')
            
            # Validate email domain
            if not AuthService.validate_email_domain(email):
                return AuthResponse(
                    success=False,
                    message="Please use a valid @gmail.com or @uwaterloo.ca email address"
                )
            
            # Check if user exists
            existing_user = await AuthService._find_existing_user(email)
            
            if existing_user:
                return await AuthService._handle_existing_user(existing_user, google_user, token_request)
            else:
                return await AuthService._create_new_google_user(google_user, token_request.account_type, token_request.access_token)
                    
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return AuthResponse(
                success=False,
                message=str(e) if "Invalid Google" in str(e) or "Could not retrieve" in str(e) else "Authentication failed"
            )
    
    @staticmethod
    async def _create_new_google_user(google_user: Dict[str, Any], account_type: str, access_token: str) -> AuthResponse:
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
                user=auth_user,
                access_token=access_token
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
        return await AuthService._update_user_field(
            user_id=role_request.user_id,
            field_name="role",
            field_value=role_request.new_role,
            success_message=f"User role updated to {role_request.new_role}",
            operation_name="updating user role"
        )
    
    @staticmethod
    async def update_account_status(user_id: str, status: str) -> AuthResponse:
        if status not in ["active", "blocked"]:
            return AuthResponse(
                success=False,
                message="Invalid status. Must be 'active' or 'blocked'"
            )
        
        return await AuthService._update_user_field(
            user_id=user_id,
            field_name="account_type",
            field_value=status,
            success_message=f"Account {status}",
            operation_name="updating account status"
        )
    
    @staticmethod
    async def _update_user_field(user_id: str, field_name: str, field_value: str, success_message: str, operation_name: str) -> AuthResponse:
        """Helper method for updating user fields"""
        try:
            logger.info(f"Updating {field_name} for user {user_id} to {field_value}")
            
            update_response = supabase.table("users").update({
                field_name: field_value
            }).eq("user_id", user_id).execute()
            
            if not update_response.data:
                logger.error(f"Failed to update {field_name} for user {user_id}: no data returned")
                return AuthResponse(
                    success=False,
                    message="User not found or update failed"
                )
            
            logger.info(f"Successfully updated {field_name} for user {user_id} to {field_value}")
            return AuthResponse(
                success=True,
                message=success_message
            )
            
        except Exception as e:
            logger.error(f"Error {operation_name}: {e}")
            return AuthResponse(
                success=False,
                message=f"Failed to update {field_name}"
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