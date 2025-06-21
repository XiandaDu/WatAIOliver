from supabase import create_client, Client

SUPABASE_URL = "https://zeyggksxsfrqziseysnr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpleWdna3N4c2ZycXppc2V5c25yIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0OTg1OTU1NiwiZXhwIjoyMDY1NDM1NTU2fQ.RNiZ2p_mVMwztyBhUea39iphKw7VatjS6VXu_VGkHuo"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print(supabase.table('conversation_table').select('*').execute())