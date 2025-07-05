from supabase import create_client, Client

SUPABASE_URL = "https://zeyggksxsfrqziseysnr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpleWdna3N4c2ZycXppc2V5c25yIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0OTg1OTU1NiwiZXhwIjoyMDY1NDM1NTU2fQ.RNiZ2p_mVMwztyBhUea39iphKw7VatjS6VXu_VGkHuo"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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