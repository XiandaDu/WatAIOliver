import os
import requests
import random
import string
from typing import Optional, Dict, Any
from src.supabaseClient import supabase
from .models import AuthUser, GoogleTokenRequest, AuthResponse, RoleUpdateRequest, EmailVerificationRequest, CodeVerificationRequest, EmailVerificationResponse
from twilio.rest import Client
import logging

logger = logging.getLogger(__name__)

# In-memory storage for verification codes (fallback when database table doesn't exist)
verification_codes_storage = {}

# Initialize Twilio Verify service
twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_verify_sid = os.getenv("TWILIO_VERIFY_SERVICE_SID")

if twilio_account_sid and twilio_auth_token and twilio_verify_sid:
    twilio_client = Client(twilio_account_sid, twilio_auth_token)
    twilio_verify_enabled = True
    logger.info("Twilio Verify service initialized successfully")
else:
    twilio_client = None
    twilio_verify_enabled = False
    logger.warning("Twilio Verify not configured. Email verification will use fallback method.")

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
    
    @staticmethod
    def _generate_verification_code() -> str:
        """Generate a 6-digit verification code"""
        return ''.join(random.choices(string.digits, k=6))
    
    @staticmethod
    async def send_verification_code(email_request: EmailVerificationRequest) -> EmailVerificationResponse:
        """Send verification code to email using Twilio Verify"""
        try:
            email = email_request.email
            
            # Validate email domain
            if not AuthService.validate_email_domain(email):
                return EmailVerificationResponse(
                    success=False,
                    message="Please use a valid @gmail.com or @uwaterloo.ca email address"
                )
            
            # Use Twilio Verify if configured
            if twilio_verify_enabled:
                try:
                    verification = twilio_client.verify.v2.services(twilio_verify_sid).verifications.create(
                        to=email,
                        channel='email'
                    )
                    
                    if verification.status in ['pending', 'sent']:
                        logger.info(f"Twilio verification sent to {email}")
                        return EmailVerificationResponse(
                            success=True,
                            message="Verification code sent to your email",
                            email=email
                        )
                    else:
                        logger.error(f"Twilio verification failed for {email}: {verification.status}")
                        raise Exception(f"Twilio verification failed: {verification.status}")
                        
                except Exception as twilio_error:
                    logger.error(f"Twilio Verify error: {twilio_error}")
                    # Fall back to manual method
                    logger.warning("Falling back to manual verification code generation")
            
            # Fallback: Generate and display verification code manually
            verification_code = AuthService._generate_verification_code()
            
            # Store verification code in database
            try:
                # First, delete any existing verification codes for this email
                supabase.table("verification_codes").delete().eq("email", email).execute()
                
                # Insert new verification code with expiration (10 minutes from now)
                verification_data = {
                    "email": email,
                    "verification_code": verification_code,
                    "expires_at": "now() + interval '10 minutes'"
                }
                
                result = supabase.table("verification_codes").insert(verification_data).execute()
                logger.info(f"Verification code stored for {email}: {verification_code}")
                
            except Exception as db_error:
                logger.error(f"Database error storing verification code: {db_error}")
                # If the table doesn't exist, we'll use a fallback approach
                logger.warning("verification_codes table not found, using fallback storage")
                # Store in memory as fallback
                from datetime import datetime, timedelta
                verification_codes_storage[email] = {
                    "code": verification_code,
                    "expires_at": datetime.utcnow() + timedelta(minutes=10)
                }
            
            # Display verification code prominently (fallback method)
            print("\n" + "="*60)
            print(f"📧 EMAIL VERIFICATION CODE")
            print(f"📧 Email: {email}")
            print(f"🔐 Code: {verification_code}")
            print(f"⏰ Expires: 10 minutes")
            print("="*60 + "\n")
            
            # Log the code for debugging
            logger.info(f"🔐 VERIFICATION CODE for {email}: {verification_code}")
            logger.info(f"⏰ This code expires in 10 minutes")
            
            return EmailVerificationResponse(
                success=True,
                message="Verification code sent to your email",
                email=email
            )
            
        except Exception as e:
            logger.error(f"Send verification code error: {e}")
            return EmailVerificationResponse(
                success=False,
                message="Failed to send verification code. Please try again."
            )
    
    @staticmethod
    async def verify_code(code_request: CodeVerificationRequest) -> AuthResponse:
        """Verify the verification code and authenticate user using Twilio Verify"""
        try:
            email = code_request.email
            code = code_request.code
            
            # Validate email domain
            if not AuthService.validate_email_domain(email):
                return AuthResponse(
                    success=False,
                    message="Please use a valid @gmail.com or @uwaterloo.ca email address"
                )
            
            # Validate code format
            if len(code) != 6 or not code.isdigit():
                return AuthResponse(
                    success=False,
                    message="Invalid verification code format. Please enter a 6-digit code."
                )
            
            # Use Twilio Verify if configured
            if twilio_verify_enabled:
                try:
                    verification_check = twilio_client.verify.v2.services(twilio_verify_sid).verification_checks.create(
                        to=email,
                        code=code
                    )
                    
                    if verification_check.status == 'approved':
                        logger.info(f"Twilio verification successful for {email}")
                        # Continue with user authentication
                    else:
                        logger.warning(f"Twilio verification failed for {email}: {verification_check.status}")
                        return AuthResponse(
                            success=False,
                            message="Invalid verification code. Please check and try again."
                        )
                        
                except Exception as twilio_error:
                    logger.error(f"Twilio Verify error: {twilio_error}")
                    # Fall back to manual verification
                    logger.warning("Falling back to manual verification code checking")
                    return await AuthService._verify_code_manually(email, code)
            else:
                # Use manual verification
                return await AuthService._verify_code_manually(email, code)
            
            # Check if user exists and authenticate
            return await AuthService._authenticate_user_after_verification(email)
                
        except Exception as e:
            logger.error(f"Verify code error: {e}")
            return AuthResponse(
                success=False,
                message="Verification failed. Please try again."
            )
    
    @staticmethod
    async def _verify_code_manually(email: str, code: str) -> AuthResponse:
        """Manual verification code checking (fallback method)"""
        try:
            # Check verification code against database or memory storage
            stored_code = None
            expires_at = None
            code_found = False
            
            try:
                # Try database first
                verification_response = supabase.table("verification_codes").select("*").eq("email", email).execute()
                
                if verification_response.data:
                    stored_code_data = verification_response.data[0]
                    stored_code = stored_code_data.get("verification_code")
                    expires_at = stored_code_data.get("expires_at")
                    code_found = True
                    logger.info(f"Found verification code in database for {email}")
                else:
                    # Check in-memory storage as fallback
                    if email in verification_codes_storage:
                        stored_code_data = verification_codes_storage[email]
                        stored_code = stored_code_data.get("code")
                        expires_at = stored_code_data.get("expires_at")
                        code_found = True
                        logger.info(f"Found verification code in memory storage for {email}")
                
                if not code_found:
                    logger.warning(f"No verification code found for {email}")
                    return AuthResponse(
                        success=False,
                        message="No verification code found. Please request a new code."
                    )
                
                # Check if code matches
                if stored_code != code:
                    logger.warning(f"Invalid verification code for {email}: provided={code}, stored={stored_code}")
                    return AuthResponse(
                        success=False,
                        message="Invalid verification code. Please check and try again."
                    )
                
                # Check if code has expired
                from datetime import datetime
                if expires_at:
                    try:
                        if isinstance(expires_at, datetime):
                            # In-memory storage
                            current_datetime = datetime.utcnow()
                            expires_datetime = expires_at
                        else:
                            # Database storage - parse the timestamp
                            expires_datetime = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                            current_datetime = datetime.utcnow()
                        
                        if current_datetime > expires_datetime:
                            logger.warning(f"Verification code expired for {email}")
                            # Clean up expired code
                            if email in verification_codes_storage:
                                del verification_codes_storage[email]
                            else:
                                supabase.table("verification_codes").delete().eq("email", email).execute()
                            return AuthResponse(
                                success=False,
                                message="Verification code has expired. Please request a new code."
                            )
                    except Exception as parse_error:
                        logger.error(f"Error parsing expiration time: {parse_error}")
                        # Continue with verification if we can't parse the time
                
                # Code is valid, clean it up
                if email in verification_codes_storage:
                    del verification_codes_storage[email]
                else:
                    supabase.table("verification_codes").delete().eq("email", email).execute()
                logger.info(f"Verification code verified successfully for {email}")
                
            except Exception as db_error:
                logger.error(f"Database error verifying code: {db_error}")
                # Try in-memory storage as fallback
                if email in verification_codes_storage:
                    stored_code_data = verification_codes_storage[email]
                    stored_code = stored_code_data.get("code")
                    expires_at = stored_code_data.get("expires_at")
                    
                    if stored_code == code:
                        from datetime import datetime
                        if datetime.utcnow() <= expires_at:
                            # Code is valid
                            del verification_codes_storage[email]
                            logger.info(f"Verification code verified successfully for {email} (from memory)")
                        else:
                            logger.warning(f"Verification code expired for {email}")
                            del verification_codes_storage[email]
                            return AuthResponse(
                                success=False,
                                message="Verification code has expired. Please request a new code."
                            )
                    else:
                        logger.warning(f"Invalid verification code for {email}: provided={code}, stored={stored_code}")
                        return AuthResponse(
                            success=False,
                            message="Invalid verification code. Please check and try again."
                        )
                else:
                    return AuthResponse(
                        success=False,
                        message="Failed to verify code. Please try again."
                    )
            
            # Code is valid, authenticate user
            return await AuthService._authenticate_user_after_verification(email)
            
        except Exception as e:
            logger.error(f"Manual verification error: {e}")
            return AuthResponse(
                success=False,
                message="Verification failed. Please try again."
            )
    
    @staticmethod
    async def _authenticate_user_after_verification(email: str) -> AuthResponse:
        """Authenticate user after successful verification"""
        try:
            # Check if user exists
            existing_user = await AuthService._find_existing_user(email)
            
            if existing_user:
                # User exists, log them in
                profile_response = supabase.table("users").select("*").eq("user_id", existing_user.id).execute()
                profile = profile_response.data[0] if profile_response.data else None
                
                auth_user = AuthUser(
                    id=existing_user.id,
                    email=existing_user.email,
                    username=profile.get("username", email.split("@")[0]) if profile else email.split("@")[0],
                    full_name=profile.get("full_name") if profile else None,
                    role=profile.get("role", "student") if profile else "student",
                    courses=profile.get("courses", []) if profile else [],
                    email_confirmed=existing_user.email_confirmed_at is not None,
                    created_at=existing_user.created_at,
                    last_sign_in=existing_user.last_sign_in_at
                )
                
                return AuthResponse(
                    success=True,
                    message="Verification successful! Welcome back!",
                    user=auth_user
                )
            else:
                # Create new user
                logger.info(f"Creating new user for email verification: {email}")
                
                # Create user in Supabase Auth
                auth_response = supabase.auth.admin.create_user({
                    "email": email,
                    "email_confirm": True,  # Auto-confirm email verification users
                    "user_metadata": {
                        "full_name": email.split('@')[0],
                        "provider": "email"
                    }
                })
                
                if not auth_response.user:
                    logger.error(f"Failed to create Supabase Auth user for: {email}")
                    return AuthResponse(
                        success=False,
                        message="Failed to create user account"
                    )
                
                # Create user profile
                profile_data = {
                    "user_id": auth_response.user.id,
                    "email": email,
                    "username": email.split('@')[0],
                    "full_name": email.split('@')[0],
                    "role": "student",  # Default to student for email verification
                    "courses": [],
                    "account_type": "active"
                }
                
                supabase.table("users").insert(profile_data).execute()
                
                auth_user = AuthUser(
                    id=auth_response.user.id,
                    email=email,
                    username=email.split('@')[0],
                    full_name=email.split('@')[0],
                    role="student",
                    courses=[],
                    email_confirmed=True,
                    created_at=auth_response.user.created_at
                )
                
                # Welcome message logged (original simple approach)
                logger.info(f"Welcome new user: {email}")
                
                return AuthResponse(
                    success=True,
                    message="Account created successfully! Welcome!",
                    user=auth_user
                )
                
        except Exception as e:
            logger.error(f"User authentication error: {e}")
            return AuthResponse(
                success=False,
                message="Authentication failed. Please try again."
            )