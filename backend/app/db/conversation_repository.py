from app.core.supabase import supabase
from uuid import UUID
from typing import List, Optional
import uuid
from app.models.conversation import ConversationCreate
import json

def create_conversation(data: ConversationCreate):
    if not data["id"]:
        data["id"] = str(uuid.uuid4())
    print(data["id"])
    result = supabase.table("conversation").insert(data).execute()
    return result.data[0]

def get_conversations(user_id: UUID) -> List[dict]:
    result = supabase.table("conversation").select("*").eq("user_id", str(user_id)).execute()
    return result.data

def get_conversation(convo_id: UUID) -> Optional[dict]:
    result = supabase.table("conversation").select("*").eq("id", str(convo_id)).execute()
    return result.data[0] if result.data else None

def update_conversation(convo_id: UUID, message: str) -> dict:
    result = supabase.table("conversation").update({"message": message}).eq("id", str(convo_id)).execute()
    return result.data[0]

def delete_conversation(convo_id: UUID) -> None:
    supabase.table("conversation").delete().eq("id", str(convo_id)).execute()
