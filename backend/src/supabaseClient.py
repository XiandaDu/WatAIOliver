from dotenv import load_dotenv
import os
import sys

# Load environment variables from .env file
load_dotenv()

# Debugging: Print the current directory and .env file path
print(f"Current directory: {os.getcwd()}")
env_path = os.path.join(os.getcwd(), '.env')
print(f"Looking for .env at: {env_path}")
print(f"Does .env exist: {os.path.exists(env_path)}")

# Import Supabase client
from supabase import create_client, Client

# Get environment variables with validation
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Validate environment variables
if not SUPABASE_URL:
    print("ERROR: SUPABASE_URL is not set in environment variables")
    print("Available environment variables:", list(os.environ.keys()))
    sys.exit(1)

if not SUPABASE_KEY:
    print("ERROR: SUPABASE_KEY is not set in environment variables")
    print("Available environment variables:", list(os.environ.keys()))
    sys.exit(1)

# Debug output - show values (but truncate for security)
print(f"SUPABASE_URL: {SUPABASE_URL}")
print(f"SUPABASE_KEY: {SUPABASE_KEY[:10]}...{SUPABASE_KEY[-5:] if SUPABASE_KEY else ''}")

# Create Supabase client
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Supabase client created successfully")
except Exception as e:
    print(f"Error creating Supabase client: {e}")
    sys.exit(1)

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