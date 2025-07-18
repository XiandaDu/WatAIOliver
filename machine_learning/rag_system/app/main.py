from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from typing import Optional

from app.config import get_settings
from services.rag_service import RAGService

# Initialize FastAPI app
app = FastAPI(title="RAG Backend")

# Global vars for RAG service and error tracking
_rag_service: Optional[RAGService] = None
_initialization_error: Optional[str] = None

def get_rag_service() -> RAGService:
    """
    Initialize and return the RAGService instance.
    Handles initialization errors and returns appropriate HTTP exceptions.
    """
    global _rag_service, _initialization_error
    if _rag_service is None and _initialization_error is None:
        try:
            # Attempt to initialize RAGService with given settings
            _rag_service = RAGService(get_settings())
        except Exception as e:
            _initialization_error = f"RAG service initialization failed: {str(e)}"
            logging.error(_initialization_error)
    
    if _initialization_error:
        # If initialization failed, raise a 503 error with details
        raise HTTPException(
            status_code=503, 
            detail=f"RAG service unavailable: {_initialization_error}. Please check your Supabase configuration."
        )
    
    if _rag_service is None:
        # If service is still not initialized, raise 503 error
        raise HTTPException(
            status_code=503, 
            detail="RAG service not initialized"
        )
    
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
    # Input model for document processing
    course_id: str
    content: str

class QuestionIn(BaseModel):
    # Input model for question answering
    course_id: str
    question: str

@app.post("/process_document")
def process_document(doc: DocumentIn):
    """
    Endpoint to process and store a document for a given course.
    Returns result (or error if processing fails).
    """
    result = get_rag_service().process_document(doc.course_id, doc.content)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result

@app.post("/ask")
def ask_question(data: QuestionIn):
    """
    Endpoint to answer a question for a given course using RAG.
    Returns answer (or error if answering fails).
    """
    result = get_rag_service().answer_question(data.course_id, data.question)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result
