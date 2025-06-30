from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .config import get_settings
from ..services.rag_service import RAGService

app = FastAPI(title="RAG Backend")
_rag_service: RAGService | None = None

def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService(get_settings())
    return _rag_service

@app.get("/health")
def health():
    return {"status": "ok"}

class DocumentIn(BaseModel):
    course_id: str
    content: str

class QuestionIn(BaseModel):
    course_id: str
    question: str

@app.post("/process_document")
def process_document(doc: DocumentIn):
    result = get_rag_service().process_document(doc.course_id, doc.content)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result

@app.post("/ask")
def ask_question(data: QuestionIn):
    result = get_rag_service().answer_question(data.course_id, data.question)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result
