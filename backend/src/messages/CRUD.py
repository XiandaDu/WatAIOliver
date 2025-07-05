from src.supabaseClient import supabase
from datetime import datetime, timezone

# CREATE
async def create_message(message_id, user_id, content, sender, conversation_id):
    now = datetime.now(timezone.utc).isoformat()
    data = {
        "message_id": message_id,
        "user_id": user_id,
        "content": content,
        "sender": sender,
        "conversation_id": conversation_id,
        "created_at": now,
        "updated_at": now,
    }
    response = await supabase.table("messages").insert(data).execute()
    return response.data

# READ (all messages for a conversation)
def get_messages(conversation_id):
    '''
    Fetch all messages for a given conversation_id, ordered by created_at in ascending order.
    return empty list if no messages found.
    '''
    response = supabase.table("messages").select("*").eq("conversation_id", conversation_id).order("created_at", desc=False).execute()
    return response.data

# READ single message by message_id
'''
Fetch a single message by its message_id.
Returns None and raise 404 if the message is not found or an error occurs.
'''
def get_message(message_id):
    try:
        response = supabase.table("messages").select("*").eq("message_id", message_id).single().execute()
        return response.data
    except Exception as e:
        # Optionally log e
        return None

# UPDATE
def update_message(message_id, **kwargs):
    kwargs["updated_at"] = datetime.now(timezone.utc).isoformat()
    response = supabase.table("messages").update(kwargs).eq("message_id", message_id).execute()
    return response.data

# DELETE
def delete_message(message_id):
    response = supabase.table("messages").delete().eq("message_id", message_id).execute()
    return response.data