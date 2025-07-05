from fastapi import HTTPException
from .CRUD import (
    create_conversation, get_conversations, update_conversation, delete_conversation
)
from .models import ConversationCreate, ConversationUpdate, ConversationResponse
from typing import List
import uuid

def create_conversation_service(convo: ConversationCreate) -> ConversationResponse:
    conversation_id = convo.conversation_id or str(uuid.uuid4())
    data = create_conversation(conversation_id, convo.title, convo.user_id)
    if data:
        return ConversationResponse(**data[0])
    raise HTTPException(status_code=400, detail="Conversation not created")

def get_conversations_service(user_id: str) -> List[ConversationResponse]:
    data = get_conversations(user_id)
    return [ConversationResponse(**item) for item in data]

def update_conversation_service(conversation_id: str, convo: ConversationUpdate) -> ConversationResponse:
    data = update_conversation(conversation_id, convo.title)
    if data:
        return ConversationResponse(**data[0])
    raise HTTPException(status_code=404, detail="Conversation not found")

def delete_conversation_service(conversation_id: str):
    data = delete_conversation(conversation_id)
    if data:
        return {"detail": "Conversation deleted"}
    raise HTTPException(status_code=404, detail="Conversation not found")