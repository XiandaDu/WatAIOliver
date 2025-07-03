from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

# Qwen model endpoint (from legacy uw_llm.py)
BASE_URL = "http://ece-nebula07.eng.uwaterloo.ca:8976"

app = FastAPI()

# Allow CORS for local frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    prompt: str
    reasoning: bool = False

class ChatResponse(BaseModel):
    result: str

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    response = requests.post(f"{BASE_URL}/generate", data={"prompt": req.prompt, "reasoning": req.reasoning})
    result = response.json().get("result", "No result returned")
    return ChatResponse(result=result) 