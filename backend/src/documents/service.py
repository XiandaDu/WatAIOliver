from .CRUD import (
    create_document, get_documents, get_document,
    update_document, delete_document
)
from .models import DocumentCreate, DocumentUpdate, DocumentResponse

def create_document_service(doc_data: DocumentCreate):
    return create_document(
        doc_data.document_id,
        doc_data.course_id,
        doc_data.term,
        doc_data.title,
        doc_data.content
    )

def get_documents_service(course_id=None):
    return get_documents(course_id)

def get_document_service(document_id):
    return get_document(document_id)

def update_document_service(document_id, doc_data: DocumentUpdate):
    return update_document(document_id, **doc_data.dict(exclude_unset=True))

def delete_document_service(document_id):
    return delete_document(document_id)