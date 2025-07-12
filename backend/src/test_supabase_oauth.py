from dotenv import load_dotenv
load_dotenv()

from supabase import create_client
import os

# Get environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print(f"Using URL: {SUPABASE_URL}")
print(f"Using KEY: {SUPABASE_KEY[:10]}...{SUPABASE_KEY[-5:]}")

# Create client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Try to get OAuth URL
try:
    response = supabase.auth.sign_in_with_oauth({
        "provider": "google",
        "options": {
            "redirect_to": "http://localhost:5173/login"
        }
    })
    
    print(f"Response type: {type(response)}")
    print(f"Response content: {response}")
    
    if hasattr(response, 'model_dump'):
        model_data = response.model_dump()
        print(f"model_dump: {model_data}")
        if isinstance(model_data, dict) and 'data' in model_data and 'url' in model_data.get('data', {}):
            print(f"URL found: {model_data['data']['url']}")
    
    if hasattr(response, '__dict__'):
        print(f"__dict__: {response.__dict__}")
    
except Exception as e:
    print(f"Error: {e}")