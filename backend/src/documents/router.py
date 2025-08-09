from fastapi import APIRouter, HTTPException, Query
from .model import DocumentCreate, DocumentUpdate, DocumentResponse
from .service import (
    create_document_service, get_documents_service, get_document_service,
    update_document_service, delete_document_service
)
from typing import List, Optional
from fastapi import Query
from .service import get_kb_documents_service, delete_kb_document_service

router = APIRouter(
    prefix='/documents',
    tags=['documents']
)

@router.post("/", response_model=DocumentResponse)
async def create_document_api(doc: DocumentCreate):
    data = create_document_service(doc)
    if data:
        return data[0]
    raise HTTPException(status_code=400, detail="Document not created")

@router.get("/", response_model=List[DocumentResponse])
async def get_documents_api(course_id: Optional[str] = Query(None)):
    return get_documents_service(course_id)


@router.get("/kb")
async def list_kb_documents(course_id: str = Query(...)):
    return get_kb_documents_service(course_id)

@router.delete("/kb")
async def delete_kb_document(course_id: str = Query(...), document_id: str = Query(...)):
    return delete_kb_document_service(course_id, document_id)

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document_api(document_id: str):
    data = get_document_service(document_id)
    if data:
        return data
    raise HTTPException(status_code=404, detail="Document not found")

@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document_api(document_id: str, doc: DocumentUpdate):
    data = update_document_service(document_id, doc)
    if data:
        return data[0]
    raise HTTPException(status_code=404, detail="Document not found")

@router.delete("/{document_id}")
async def delete_document_api(document_id: str):
    data = delete_document_service(document_id)
    if data:
        return {"detail": "Document deleted"}
    raise HTTPException(status_code=404, detail="Document not found")