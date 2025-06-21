from supabase_client import supabase

##### CONVERSATION TABLE #####
# CREATE
def create_conversation(user_id, sender, message):
    data = {
        "user_id": user_id,
        "sender": sender,
        "message": message,
    }
    response = supabase.table("conversation").insert(data).execute()
    return response.data

# READ (get all conversations for a user)
def get_conversations(user_id):
    response = supabase.table("conversation").select("*").eq("user_id", user_id).order("created_at", desc=False).execute()
    return response.data

# UPDATE (update message by id)
def update_conversation(conversation_id, new_message):
    response = supabase.table("conversation").update({"message": new_message}).eq("conversation_id", conversation_id).execute()
    return response.data

# DELETE (delete conversation by id)
def delete_conversation(conversation_id):
    response = supabase.table("conversation").delete().eq("conversation_id", conversation_id).execute()
    return response.data

##### MESSAGES TABLE #####

# CREATE
def create_message(user_id, sender, content):
    data = {
        "user_id": user_id,
        "sender": sender,
        "content": content,
    }
    response = supabase.table("messages").insert(data).execute()
    return response.data

# READ (get all messages within a conversation)
def get_messages(conversation_id):
    response = supabase.table("messages").select("*").eq("conversation_id", conversation_id).order("created_at", desc=False).execute()
    return response.data

# UPDATE (update message by id)
def update_message(message_id, new_content):
    response = supabase.table("messages").update({"content": new_content}).eq("message_id", message_id).execute()
    return response.data

# DELETE (delete message by id)
def delete_message(message_id):
    response = supabase.table("messages").delete().eq("message_id", message_id).execute()
    return response.data
