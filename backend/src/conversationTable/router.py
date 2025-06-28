from fastapi import APIRouter
from .models import ConversationCreate, ConversationUpdate, ConversationResponse
from .service import (
    create_conversation_service,
    get_conversations_service,
    update_conversation_service,
    delete_conversation_service,
)
from typing import List

router = APIRouter(
    prefix="/conversations",
    tags=["conversations"]
)

@router.post("/", response_model=ConversationResponse)
def api_create_conversation(convo: ConversationCreate):
    return create_conversation_service(convo)

@router.get("/{user_id}", response_model=List[ConversationResponse])
def api_get_conversations(user_id: str):
    return get_conversations_service(user_id)

@router.put("/{conversation_id}", response_model=ConversationResponse)
def api_update_conversation(conversation_id: str, convo: ConversationUpdate):
    return update_conversation_service(conversation_id, convo)

@router.delete("/{conversation_id}")
def api_delete_conversation(conversation_id: str):
    return delete_conversation_service(conversation_id)