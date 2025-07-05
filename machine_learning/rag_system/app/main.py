from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from typing import Optional

from app.config import get_settings
from services.rag_service import RAGService

app = FastAPI(title="RAG Backend")
_rag_service: Optional[RAGService] = None
_initialization_error: Optional[str] = None

def get_rag_service() -> RAGService:
    global _rag_service, _initialization_error
    if _rag_service is None and _initialization_error is None:
        try:
            _rag_service = RAGService(get_settings())
        except Exception as e:
            _initialization_error = f"RAG service initialization failed: {str(e)}"
            logging.error(_initialization_error)
    
    if _initialization_error:
        raise HTTPException(
            status_code=503, 
            detail=f"RAG service unavailable: {_initialization_error}. Please check your Supabase configuration."
        )
    
    return _rag_service

@app.get("/health")
def health():
    return {"status": "ok", "message": "FastAPI server is running"}

@app.get("/health/full")
def health_full():
    """Detailed health check including RAG service status"""
    try:
        rag_service = get_rag_service()
        return {
            "status": "ok",
            "services": {
                "fastapi": "running",
                "rag_service": "ready",
                "database": "connected"
            }
        }
    except HTTPException as e:
        return {
            "status": "partial",
            "services": {
                "fastapi": "running",
                "rag_service": "unavailable",
                "database": "not configured"
            },
            "error": e.detail
        }

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
