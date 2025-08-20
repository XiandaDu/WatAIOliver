from src.supabaseClient import supabase
from datetime import datetime, timezone

# CREATE
async def create_message(message_id, user_id, content, sender, conversation_id, course_id=None, model=None):
    data = {
        "message_id": message_id,
        "user_id": user_id,
        "content": content,
        "sender": sender,
        "conversation_id": conversation_id,
        "course_id": course_id,
        "model": model,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    response = await supabase.table("messages").insert(data).execute()
    return response.data

# READ (all messages for a conversation)
async def get_messages(conversation_id):
    response = await supabase.table("messages").select("*").eq("conversation_id", conversation_id).order("created_at", desc=False).execute()
    return response.data

# READ single message by message_id
async def get_message(message_id):
    response = await supabase.table("messages").select("*").eq("message_id", message_id).single().execute()
    return response.data

# UPDATE
async def update_message(message_id, **kwargs):
    kwargs["updated_at"] = datetime.now(timezone.utc)
    response = await supabase.table("messages").update(kwargs).eq("message_id", message_id).execute()
    return response.data

# DELETE
async def delete_message(message_id):
    response = await supabase.table("messages").delete().eq("message_id", message_id).execute()
    return response.data