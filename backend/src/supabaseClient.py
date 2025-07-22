from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

from supabase import create_client, Client
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Create a test user if it doesn't exist
def ensure_test_user():
    try:
        # Check if user123 already exists
        existing_user = supabase.table("users").select("*").eq("user_id", "user123").execute()
        
        if not existing_user.data:
            # THIS IS JUST A TEST USER
            user_data = {
                "user_id": "user123",
                "username": "testuser",
                "email": "test@test.com",
                "role": "student"
            }
            
            supabase.table("users").insert(user_data).execute()
            print("test user 'user123' created")
        else:
            print("test user 'user123' already exists")
            
    except Exception as e:
        print(f"User creation error: {e}")

# Call this when the app starts
ensure_test_user()