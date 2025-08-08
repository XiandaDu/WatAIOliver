from dotenv import load_dotenv
import os
import sys

# Load environment variables from backend .env file
backend_env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(backend_env_path)

from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Create a mock client if Supabase credentials are not available
if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("WARNING: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY not found. Using mock client.")
    
    class MockSupabaseClient:
        def table(self, name):
            return MockTable()
    
    class MockTable:
        def select(self, *args):
            return self
        def insert(self, data):
            return self
        def eq(self, field, value):
            return self
        def execute(self):
            return type('MockResult', (), {'data': []})()
    
    supabase = MockSupabaseClient()
else:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Production-ready initialization - no test data creation