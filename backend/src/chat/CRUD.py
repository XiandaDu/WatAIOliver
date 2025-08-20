from src.supabaseClient import supabase
from .models import ConversationCreate, ConversationUpdate, ConversationDelete, MessageCreate, MessageUpdate, MessageDelete
from datetime import datetime
import uuid

##### CONVERSATION TABLE #####
# CREATE
def create_conversation(data: ConversationCreate):
    try:
        conversation_data = {
            "conversation_id": str(uuid.uuid4()),
            "user_id": data.user_id,
            "title": data.title, 
            "course_id": getattr(data, "course_id", None),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        response = supabase.table("conversations").insert(conversation_data).execute()
        return response.data
    except Exception as e:
        print(f"eror creating conversation: {e}")
        raise e

# READ (get all conversations for a user)
def get_conversations(user_id: str):
    try:
        response = supabase.table("conversations").select("*").eq("user_id", user_id).order("created_at", desc=False).execute()
        return response.data
    except Exception as e:
        print(f"error getting conversations: {e}")
        return []

# UPDATE (update message by id)
def update_conversation(data: ConversationUpdate):
    try:
        response = supabase.table("conversations").update({
            "title": data.title, 
            "updated_at": datetime.now().isoformat()
        }).eq("conversation_id", data.conversation_id).execute()
        return response.data
    except Exception as e:
        print(f"errorupdating conversation: {e}")
        raise e

# DELETE (delete conversation by id)
def delete_conversation(data: ConversationDelete):
    try:
        # First, delete all messages associated with this conversation
        supabase.table("messages").delete().eq("conversation_id", data.conversation_id).execute()
        
        # Then, delete the conversation
        response = supabase.table("conversations").delete().eq("conversation_id", data.conversation_id).execute()
        return response.data
    except Exception as e:
        print(f"error deleting conversation: {e}")
        raise e

##### MESSAGES TABLE #####

# CREATE
def create_message(data: MessageCreate):
    try:
        message_data = {
            "message_id": str(uuid.uuid4()),
            "conversation_id": data.conversation_id,
            "user_id": data.user_id,
            "sender": data.sender,
            "content": data.content, 
            "course_id": getattr(data, "course_id", None),
            "model": getattr(data, "model", None),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        response = supabase.table("messages").insert(message_data).execute()
        return response.data
    except Exception as e:
        print(f"errors creating message: {e}")
        raise e

# READ (get all messages within a conversation)
def get_messages(conversation_id: str):
    try:
        response = supabase.table("messages").select("*").eq("conversation_id", conversation_id).order("created_at", desc=False).execute()
        return response.data
    except Exception as e:
        print(f"error getting messages: {e}")
        return []

# UPDATE (update message by id)
def update_message(data: MessageUpdate):
    try:
        response = supabase.table("messages").update({
            "content": data.content, 
            "updated_at": datetime.now().isoformat()
        }).eq("message_id", data.message_id).execute()
        return response.data
    except Exception as e:
        print(f"error updating message: {e}")
        raise e

# DELETE (delete message by id)
def delete_message(data: MessageDelete):
    try:
        response = supabase.table("messages").delete().eq("message_id", data.message_id).execute()
        return response.data
    except Exception as e:
        print(f"error deleting message: {e}")
        raise e
