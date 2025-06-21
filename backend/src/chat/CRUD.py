from supabase_client import supabase
from .models import ConversationCreate, ConversationUpdate, ConversationDelete, MessageCreate, MessageUpdate, MessageDelete

##### CONVERSATION TABLE #####
# CREATE
def create_conversation(data: ConversationCreate):
    data = {
        "user_id": data.user_id,
        "sender": data.sender,
        "message": data.message,
    }
    response = supabase.table("conversation").insert(data).execute()
    return response.data

# READ (get all conversations for a user)
def get_conversations(user_id: str):
    response = supabase.table("conversation").select("*").eq("user_id", user_id).order("created_at", desc=False).execute()
    return response.data

# UPDATE (update message by id)
def update_conversation(data: ConversationUpdate):
    response = supabase.table("conversation").update({"message": data.message}).eq("conversation_id", data.conversation_id).execute()
    return response.data

# DELETE (delete conversation by id)
def delete_conversation(data: ConversationDelete):
    response = supabase.table("conversation").delete().eq("conversation_id", data.conversation_id).execute()
    return response.data

##### MESSAGES TABLE #####

# CREATE
def create_message(data: MessageCreate):
    data = {
        "user_id": data.user_id,
        "sender": data.sender,
        "content": data.content,
    }
    response = supabase.table("messages").insert(data).execute()
    return response.data

# READ (get all messages within a conversation)
def get_messages(conversation_id: str):
    response = supabase.table("messages").select("*").eq("conversation_id", conversation_id).order("created_at", desc=False).execute()
    return response.data

# UPDATE (update message by id)
def update_message(data: MessageUpdate):
    response = supabase.table("messages").update({"content": data.content}).eq("message_id", data.message_id).execute()
    return response.data

# DELETE (delete message by id)
def delete_message(data: MessageDelete):
    response = supabase.table("messages").delete().eq("message_id", data.message_id).execute()
    return response.data
