from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .config import get_settings
from ..services.rag_service import RAGService

app = FastAPI(title="OliverAI Gemini Backend")
_rag_service: RAGService | None = None


def get_rag_service() -> RAGService:
    """Lazily initialize the RAG service using environment settings."""
    global _rag_service
    if _rag_service is None:
        settings = get_settings()
        _rag_service = RAGService(settings)
    return _rag_service


@app.get("/health")
async def health() -> dict:
    """Basic health check endpoint."""
    return {"status": "ok"}


class DocumentIn(BaseModel):
    course_id: str
    content: str


class QuestionIn(BaseModel):
    course_id: str
    question: str


@app.post("/process_document")
async def process_document(doc: DocumentIn):
    try:
        await get_rag_service().process_document(doc.course_id, doc.content)
        return {"status": "processed"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/ask")
async def ask_question(data: QuestionIn):
    try:
        answer = await get_rag_service().answer_question(data.course_id, data.question)
        return {"answer": answer}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
