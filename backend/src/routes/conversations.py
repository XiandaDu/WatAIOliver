from fastapi import APIRouter, HTTPException
from typing import List
from schemas.conversations import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
)
from crud.conversations import (
    create_conversation,
    read_conversations,
    update_conversation,
    delete_conversation,
)

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("/", response_model=ConversationResponse)
def api_create_conversation(entry: ConversationCreate):
    return create_conversation(entry.conversation_id, entry.title, entry.user_id)


@router.get("/{user_id}", response_model=List[ConversationResponse])
def api_get_conversations(user_id: str):
    return read_conversations(user_id)


@router.put("/{conversation_id}", response_model=List[ConversationResponse])
def api_update_conversation(conversation_id: str, entry: ConversationUpdate):
    if entry.title is None:
        raise HTTPException(status_code=400, detail="Title is required for update")
    return update_conversation(conversation_id, entry.title)


@router.delete("/{conversation_id}", response_model=List[ConversationResponse])
def api_delete_conversation(conversation_id: str):
    return delete_conversation(conversation_id)
