from fastapi import APIRouter, HTTPException, Query
from documents.models import DocumentCreate, DocumentUpdate, DocumentResponse
from documents.service import (
    create_document_service, get_documents_service, get_document_service,
    update_document_service, delete_document_service
)
from typing import List, Optional

router = APIRouter(
    prefix='/documents',
    tags=['documents']
)

@router.post("/", response_model=DocumentResponse)
async def create_document_api(doc: DocumentCreate):
    data = await create_document_service(doc)
    if data:
        return data[0]
    raise HTTPException(status_code=400, detail="Document not created")

@router.get("/", response_model=List[DocumentResponse])
async def get_documents_api(course_id: Optional[str] = Query(None)):
    return await get_documents_service(course_id)

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document_api(document_id: str):
    data = await get_document_service(document_id)
    if data:
        return data
    raise HTTPException(status_code=404, detail="Document not found")

@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document_api(document_id: str, doc: DocumentUpdate):
    data = await update_document_service(document_id, doc)
    if data:
        return data[0]
    raise HTTPException(status_code=404, detail="Document not found")

@router.delete("/{document_id}")
async def delete_document_api(document_id: str):
    data = await delete_document_service(document_id)
    if data:
        return {"detail": "Document deleted"}
    raise HTTPException(status_code=404, detail="Document not found")