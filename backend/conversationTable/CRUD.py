from supabaseClient import supabase
from datetime import datetime, timezone

# CREATE
def create_conversation(user_id, sender, message):
    data = {
        "user_id": user_id,
        "sender": sender,
        "message": message,
    }
    response = supabase.table("conversation_table").insert(data).execute()
    return response.data

# READ (get all conversations for a user)
def get_conversations(user_id):
    response = supabase.table("conversation_table").select("*").eq("user_id", user_id).order("created_at", desc=False).execute()
    return response.data

# UPDATE (update message by id)
def update_conversation(conversation_id, new_message):
    data = {
        "message": new_message,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    response = supabase.table("conversation_table").update(data).eq("id", conversation_id).execute()
    return response.data

# DELETE (delete conversation by id)
def delete_conversation(conversation_id):
    response = supabase.table("conversation_table").delete().eq("id", conversation_id).execute()
    return response.data