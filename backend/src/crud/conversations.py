from db.client import supabase
from datetime import datetime, timezone
import uuid


# CREATE
def create_conversation(conversation_id, title, user_id):
    data = {
        "conversation_id": conversation_id or str(uuid.uuid4()),
        "title": title,
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    response = supabase.table("conversations").insert(data).execute()
    print("responsessssssssss", response)
    return response.data[0] if response.data else None


# READ (get all conversations for a user)
def read_conversations(user_id):
    response = (
        supabase.table("conversations")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=False)
        .execute()
    )
    return response.data


# UPDATE (update title by conversation_id)
def update_conversation(conversation_id, new_title):
    data = {"title": new_title, "updated_at": datetime.now(timezone.utc).isoformat()}
    response = (
        supabase.table("conversations")
        .update(data)
        .eq("conversation_id", conversation_id)
        .execute()
    )
    return response.data if response.data else []


# DELETE (delete conversation by conversation_id)
def delete_conversation(conversation_id):
    response = (
        supabase.table("conversations")
        .delete()
        .eq("conversation_id", conversation_id)
        .execute()
    )
    return response.data
