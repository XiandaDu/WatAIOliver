from fastapi import APIRouter, Request, UploadFile, File, Form, Query, HTTPException, status

from typing import List
import tempfile
import os
import httpx

from backend.constants import TimeoutConfig, ServiceConfig

from . import service
from .models import ConversationCreate, ConversationUpdate, ConversationDelete, MessageCreate, MessageUpdate, MessageDelete, ConversationOut, MessageOut, ChatRequest
from . import CRUD as supabase_crud

router = APIRouter(
    prefix='/chat',
    tags=['chat']
)


@router.post("/")
async def chat(data: ChatRequest):
    result = await service.generate_response(data)
    
    return {"result": result}

@router.post("")
async def chat_root(data: ChatRequest):
    result = await service.generate_response(data)
    
    return {"result": result}

@router.post("/open_ask")
async def open_ask(data: ConversationCreate):
    return service.open_ask(data)

@router.post("/create_conversation")
async def create_conversation(data: ConversationCreate, response_model=ConversationOut):
    result = supabase_crud.create_conversation(data)
    return result

@router.get("/conversations/{user_id}")
async def get_conversations(user_id: str, response_model=ConversationOut):
    result = supabase_crud.get_conversations(user_id)
    return result

@router.post("/update_conversation")
async def update_conversation(data: ConversationUpdate, response_model=ConversationOut):
    result = supabase_crud.update_conversation(data)
    return result

@router.post("/delete_conversation")
async def delete_conversation(data: ConversationDelete, response_model=ConversationOut):
    result = supabase_crud.delete_conversation(data)
    return result

@router.post("/create_message")
async def create_message(data: MessageCreate, response_model=MessageOut):
    result = supabase_crud.create_message(data)
    return result

@router.get("/messages/{conversation_id}")
async def get_messages(conversation_id: str, response_model=MessageOut):
    result = supabase_crud.get_messages(conversation_id)
    return result

@router.post("/update_message")
async def update_message(data: MessageUpdate, response_model=MessageOut):
    return supabase_crud.update_message(data)

@router.post("/delete_message")
async def delete_message(data: MessageDelete, response_model=MessageOut):
    return supabase_crud.delete_message(data)

@router.post("/upload_files")
async def upload_files(
    files: List[UploadFile] = File(...),
    conversation_id: str = Form(...),
    user_id: str = Form(...)
):
    """
    Upload and process files for chat context:
    PDF files: Convert to markdown and attach as context (NOT sent to RAG)
    Text files: Attach directly as context (NOT sent to RAG)
    """
    try:
        results = []
        
        for file in files:
            filename = file.filename or 'unknown_file'
            
            # Read file content
            file_content = await file.read()
            
            # Process based on file type
            if filename.lower().endswith('.pdf'):
                # Convert PDF to markdown for chat context
                pdf_result = await process_pdf_file(file_content, filename)
                
                if pdf_result.get('success'):
                    # Store markdown content as chat context, NOT in RAG
                    markdown_content = pdf_result.get('markdown_content', '')
                    
                    results.append({
                        'filename': filename,
                        'type': 'pdf',
                        'markdown_content': markdown_content,
                        'content_length': len(markdown_content),
                        'status': 'completed'
                    })
                else:
                    results.append({
                        'filename': filename,
                        'type': 'pdf',
                        'error': pdf_result.get('error_message', 'PDF processing failed'),
                        'status': 'failed'
                    })
            
            elif filename.lower().endswith(('.txt', '.md', '.mdx')):
                # Direct text processing for chat context
                text_content = file_content.decode('utf-8')
                
                results.append({
                    'filename': filename,
                    'type': 'text',
                    'text_content': text_content,
                    'content_length': len(text_content),
                    'status': 'completed'
                })
            
            else:
                results.append({
                    'filename': filename,
                    'type': 'unsupported',
                    'error': 'Unsupported file type. Please upload PDF, TXT, MD, or MDX files.',
                    'status': 'failed'
                })
        
        return {
            'message': 'Files processed for chat context',
            'results': results,
            'conversation_id': conversation_id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"File upload and processing failed: {str(e)}"
        )

@router.post("/upload_files_for_rag")
async def upload_files_for_rag(
    files: List[UploadFile] = File(...),
    course_id: str = Form(...),
    user_id: str = Form(...),
    rag_model: str | None = Form(None),
):
    """
    Upload and process files for RAG knowledge base (admin only):
    PDF files: Backend → PDF Processor (port 8001) → RAG System (port 8002)
    Text files: Backend → RAG System (port 8002)
    """
    try:
        results = []
        
        for file in files:
            filename = file.filename or 'unknown_file'
            
            # Read file content
            file_content = await file.read()
            
            # Process based on file type
            if filename.lower().endswith('.pdf'):
                # Stage 1: Send to PDF processor service
                pdf_result = await process_pdf_file(file_content, filename)
                
                if pdf_result.get('success'):
                    # Stage 2: Send processed markdown to RAG system
                    rag_result = await process_document_with_rag(
                        course_id,  # Use the course_id parameter from the form
                        pdf_result.get('markdown_content', ''),
                        filename,
                        rag_model,
                    )
                    
                    results.append({
                        'filename': filename,
                        'type': 'pdf',
                        'pdf_processing': pdf_result,
                        'rag_processing': rag_result,
                        'status': 'completed'
                    })
                else:
                    results.append({
                        'filename': filename,
                        'type': 'pdf',
                        'error': pdf_result.get('error_message', 'PDF processing failed'),
                        'status': 'failed'
                    })
            
            elif filename.lower().endswith(('.txt', '.md', '.mdx')):
                # Direct text processing - send to RAG system
                text_content = file_content.decode('utf-8')
                rag_result = await process_document_with_rag(
                    course_id,  # Use the course_id parameter from the form
                    text_content,
                    filename,
                    rag_model,
                )
                
                results.append({
                    'filename': filename,
                    'type': 'text',
                    'rag_processing': rag_result,
                    'status': 'completed'
                })
            
            else:
                results.append({
                    'filename': filename,
                    'type': 'unsupported',
                    'error': 'Unsupported file type. Please upload PDF, TXT, MD, or MDX files.',
                    'status': 'failed'
                })
        
        return {
            'message': 'Files processed for RAG knowledge base',
            'results': results,
            'course_id': course_id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"RAG file upload and processing failed: {str(e)}"
        )

@router.get("/courses")
async def get_courses():
    """Get all courses for course selection"""
    try:
        from src.course.CRUD import get_all_courses
        courses = get_all_courses()
        return {"courses": courses}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching courses: {str(e)}")

@router.post("/courses")
async def create_course(data: dict):
    """Create a new course"""
    try:
        from src.course.CRUD import create_course
        course = create_course(
            created_by=data.get('created_by', 'admin'),
            title=data.get('title', ''),
            description=data.get('description', ''),
            term=data.get('term', '')
        )
        return {"course": course}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating course: {str(e)}")

async def process_pdf_file(file_content: bytes, filename: str) -> dict:
    """
    Send PDF file to the PDF processor service running on port 8001.
    """
    try:
        # Create temporary file for PDF processor
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(file_content)
            tmp_file_path = tmp_file.name
        
        try:
            # Send to PDF processor service
            async with httpx.AsyncClient(timeout=TimeoutConfig.PDF_PROCESSING_TIMEOUT) as client:
                with open(tmp_file_path, 'rb') as f:
                    files = {'file': (filename, f, 'application/pdf')}
                    response = await client.post(
                        f'http://{ServiceConfig.LOCALHOST}:{ServiceConfig.PDF_PROCESSOR_PORT}/convert',
                        files=files
                    )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        'success': False,
                        'error_message': f'PDF processor service returned {response.status_code}: {response.text}'
                    }
        
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
    
    except Exception as e:
        return {
            'success': False,
            'error_message': f'PDF processing failed: {str(e)}'
        }

async def process_document_with_rag(course_id: str, content: str, filename: str, rag_model: str | None = None) -> dict:
    """
    Send processed document content to the RAG system for embedding and vector storage.
    RAG system will be running on port 8002 to avoid conflicts with backend.
    """
    try:
        async with httpx.AsyncClient(timeout=TimeoutConfig.RAG_PROCESSING_TIMEOUT) as client:
            rag_payload = {
                'course_id': course_id,  # Use the actual course_id parameter
                'content': content
            }
            if rag_model:
                rag_payload['embedding_model'] = rag_model
            
            print(f"DEBUG: Processing document '{filename}' for course_id='{course_id}'")
            
            response = await client.post(
                f'http://{ServiceConfig.LOCALHOST}:{ServiceConfig.RAG_SYSTEM_PORT}/process_document',
                json=rag_payload
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'success': False,
                    'error': f'RAG system returned {response.status_code}: {response.text}'
                }
    
    except Exception as e:
        return {
            'success': False,
            'error': f'RAG processing failed: {str(e)}'
        }
