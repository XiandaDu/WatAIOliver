from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from conversationTable.CRUD import (
    create_conversation,
    get_conversations,
    update_conversation,
    delete_conversation,
)

app = FastAPI()

class ConversationCreate(BaseModel):
    user_id: int          
    sender: str           
    message: str          

class ConversationUpdate(BaseModel):
    message: str

class Conversation(BaseModel):
    id: int                              
    user_id: int                         
    sender: str                          
    message: str                         
    created_at: str                      # timestamp with time zone (as ISO string)
    updated_at: Optional[str] = None     # timestamp with time zone (nullable)

@app.post("/conversations/", response_model=Conversation)
def api_create_conversation(convo: ConversationCreate):
    data = create_conversation(convo.user_id, convo.sender, convo.message)
    if data:
        return data[0]
    raise HTTPException(status_code=400, detail="Conversation not created")

@app.get("/conversations/{user_id}", response_model=List[Conversation])
def api_get_conversations(user_id: str):
    data = get_conversations(user_id)
    return data

@app.put("/conversations/{conversation_id}", response_model=Conversation)
def api_update_conversation(conversation_id: int, convo: ConversationUpdate):
    data = update_conversation(conversation_id, convo.message)
    if data:
        return data[0]
    raise HTTPException(status_code=404, detail="Conversation not found")

@app.delete("/conversations/{conversation_id}")
def api_delete_conversation(conversation_id: int):
    data = delete_conversation(conversation_id)
    if data:
        return {"detail": "Conversation deleted"}
    raise HTTPException(status_code=404, detail="Conversation not found")