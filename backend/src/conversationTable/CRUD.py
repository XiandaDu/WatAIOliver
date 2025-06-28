from supabaseClient import supabase
from datetime import datetime, timezone
import uuid

# CREATE
def create_conversation(conversation_id, title, user_id):
    data = {
        "conversation_id": conversation_id or str(uuid.uuid4()),
        "title": title,
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    response = supabase.table("conversations").insert(data).execute()
    return response.data

# READ (get all conversations for a user)
def get_conversations(user_id):
    response = supabase.table("conversations").select("*").eq("user_id", user_id).order("created_at", desc=False).execute()
    return response.data

# UPDATE (update title by conversation_id)
def update_conversation(conversation_id, new_title):
    data = {
        "title": new_title,
        "updated_at": datetime.now(timezone.utc)
    }
    response = supabase.table("conversations").update(data).eq("conversation_id", conversation_id).execute()
    return response.data

# DELETE (delete conversation by conversation_id)
def delete_conversation(conversation_id):
    response = supabase.table("conversations").delete().eq("conversation_id", conversation_id).execute()
    return response.data