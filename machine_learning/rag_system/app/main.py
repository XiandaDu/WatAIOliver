from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from typing import Optional

# Configure logging to suppress noisy external libraries
logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("google").setLevel(logging.WARNING)
logging.getLogger("google_genai").setLevel(logging.WARNING)
logging.getLogger("supabase").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

from rag_system.app.config import get_settings
from rag_system.services import RAGService

# Initialize FastAPI app
app = FastAPI(title="RAG Backend")

# Global vars for services and error tracking
_rag_service: Optional[RAGService] = None
_initialization_error: Optional[str] = None

def get_rag_service() -> RAGService:
    """Get or initialize the RAG service."""
    global _rag_service, _initialization_error
    if _rag_service is None and _initialization_error is None:
        try:
            _rag_service = RAGService(get_settings())
        except Exception as e:
            _initialization_error = f"RAG service initialization failed: {str(e)}"
            logging.error(_initialization_error)
    if _initialization_error:
        raise HTTPException(status_code=503, detail=f"RAG service unavailable: {_initialization_error}")
    return _rag_service

@app.get("/")
def root():
    """
    Root endpoint providing API status and available endpoints.
    """
    return {
        "message": "RAG System API",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "health_full": "/health/full",
            "process_document": "/process_document",
            "ask": "/ask",
            "docs": "/docs"
        }
    }

@app.get("/health")
def health():
    """
    Basic health check endpoint for FastAPI server.
    """
    return {"status": "ok", "message": "FastAPI server is running"}

@app.get("/health/full")
def health_full():
    """
    Detailed health check including RAG service status.
    Returns partial status if RAG service is unavailable.
    """
    try:
        get_rag_service()
        status = "ready"
    except HTTPException as e:
        status = "unavailable"
        error = e.detail
    else:
        error = None

    response = {
        "status": "ok" if status == "ready" else "partial",
        "services": {
            "fastapi": "running",
            "rag_service": status,
            "database": "connected" if status == "ready" else "not configured",
        },
    }
    if error:
        response["error"] = error
    return response

class DocumentIn(BaseModel):
    # Input model for document processing
    course_id: str
    content: str
    embedding_model: str | None = None

class QuestionIn(BaseModel):
    # Input model for question answering
    course_id: str
    question: str
    embedding_model: str | None = None

@app.post("/process_document")
def process_document(doc: DocumentIn):
    """
    Endpoint to process and store a document for a given course.
    Returns result (or error if processing fails).
    """
    rag_service = get_rag_service()
    result = rag_service.process_document(doc.course_id, doc.content)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result

@app.post("/ask")
def ask_question(data: QuestionIn):
    """
    Endpoint to answer a question for a given course using RAG.
    Returns answer (or error if answering fails).
    """
    model = data.embedding_model or get_settings().embedding_model
    rag_service = get_rag_service()
    result = rag_service.answer_question(data.course_id, data.question)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result
