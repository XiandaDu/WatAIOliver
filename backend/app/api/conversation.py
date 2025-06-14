from fastapi import APIRouter, HTTPException
from uuid import UUID
from app.models.conversation import ConversationCreate, ConversationUpdate, ConversationOut
from app.db import conversation_repository as repo

router = APIRouter(prefix="/conversations", tags=["Conversations"])

@router.post("/", response_model=ConversationOut)
def create_conversation(convo: ConversationCreate):
    return repo.create_conversation(convo.dict())

@router.get("/user/{user_id}", response_model=list[ConversationOut])
def list_conversations(user_id: UUID):
    return repo.get_conversations(user_id)

@router.get("/{convo_id}", response_model=ConversationOut)
def get_convo(convo_id: UUID):
    convo = repo.get_conversation(convo_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return convo

@router.put("/{convo_id}", response_model=ConversationOut)
def update_convo(convo_id: UUID, data: ConversationUpdate):
    return repo.update_conversation(convo_id, data.message)

@router.delete("/{convo_id}")
def delete_convo(convo_id: UUID):
    repo.delete_conversation(convo_id)
    return {"ok": True}
