from fastapi import APIRouter, Request, UploadFile, File, Form, Query, HTTPException, status
from fastapi.responses import Response, JSONResponse
from typing import List
import tempfile
import os
import httpx
from . import service
from .models import ConversationCreate, ConversationUpdate, ConversationDelete, MessageCreate, MessageUpdate, MessageDelete, ConversationOut, MessageOut, ChatRequest
from . import CRUD as supabase_crud

router = APIRouter(
    prefix='/chat',
    tags=['chat']
)

@router.options("/create_conversation")
async def create_conversation_options():
    return Response(
        content="",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )

@router.options("/conversations/{user_id}")
async def get_conversations_options():
    return Response(
        content="",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )

@router.options("/delete_conversation")
async def delete_conversation_options():
    return Response(
        content="",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )

@router.options("/update_conversation")
async def update_conversation_options():
    return Response(
        content="",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )

@router.options("/create_message")
async def create_message_options():
    return Response(
        content="",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )

@router.options("/messages/{conversation_id}")
async def get_messages_options():
    return Response(
        content="",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )

@router.options("/")
async def chat_options():
    return Response(
        content="",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )

@router.options("")
async def chat_root_options():
    return Response(
        content="",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )

@router.options("/upload_files")
async def upload_files_options():
    return Response(
        content="",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )

@router.post("/")
async def chat(data: ChatRequest):
    # Check if we should use RAG enhancement
    if hasattr(data, 'conversation_id') and data.conversation_id:
        # Try to enhance the prompt with RAG context
        rag_result = await service.query_rag_system(data.conversation_id, data.prompt)
        
        if rag_result and rag_result.get('success'):
            # Enhance the prompt with RAG context
            enhanced_prompt = service.enhance_prompt_with_rag_context(data.prompt, rag_result)
            
            # Create a new request with enhanced prompt
            enhanced_data = ChatRequest(
                prompt=enhanced_prompt,
                conversation_id=data.conversation_id if hasattr(data, 'conversation_id') else None
            )
            result = service.nebula_text_endpoint(enhanced_data)
        else:
            # Fall back to regular processing
            result = service.nebula_text_endpoint(data)
    else:
        # No conversation ID, use regular processing
        result = service.nebula_text_endpoint(data)
    
    return JSONResponse(
        content={"result": result},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )

@router.post("")
async def chat_root(data: ChatRequest):
    # Check if we should use RAG enhancement
    if hasattr(data, 'conversation_id') and data.conversation_id:
        # Try to enhance the prompt with RAG context
        rag_result = await service.query_rag_system(data.conversation_id, data.prompt)
        
        if rag_result and rag_result.get('success'):
            # Enhance the prompt with RAG context
            enhanced_prompt = service.enhance_prompt_with_rag_context(data.prompt, rag_result)
            
            # Create a new request with enhanced prompt
            enhanced_data = ChatRequest(
                prompt=enhanced_prompt,
                conversation_id=data.conversation_id if hasattr(data, 'conversation_id') else None
            )
            result = service.nebula_text_endpoint(enhanced_data)
        else:
            # Fall back to regular processing
            result = service.nebula_text_endpoint(data)
    else:
        # No conversation ID, use regular processing
        result = service.nebula_text_endpoint(data)
    
    return JSONResponse(
        content={"result": result},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )

@router.post("/open_ask")
async def open_ask(data: ConversationCreate):
    return service.open_ask(data)

@router.post("/create_conversation")
async def create_conversation(data: ConversationCreate, response_model=ConversationOut):
    result = supabase_crud.create_conversation(data)
    return JSONResponse(
        content=result,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )

@router.get("/conversations/{user_id}")
async def get_conversations(user_id: str, response_model=ConversationOut):
    result = supabase_crud.get_conversations(user_id)
    return JSONResponse(
        content=result,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )

@router.post("/update_conversation")
async def update_conversation(data: ConversationUpdate, response_model=ConversationOut):
    result = supabase_crud.update_conversation(data)
    return JSONResponse(
        content=result,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )

@router.post("/delete_conversation")
async def delete_conversation(data: ConversationDelete, response_model=ConversationOut):
    result = supabase_crud.delete_conversation(data)
    return JSONResponse(
        content=result,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )

@router.post("/create_message")
async def create_message(data: MessageCreate, response_model=MessageOut):
    result = supabase_crud.create_message(data)
    return JSONResponse(
        content=result,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )

@router.get("/messages/{conversation_id}")
async def get_messages(conversation_id: str, response_model=MessageOut):
    result = supabase_crud.get_messages(conversation_id)
    return JSONResponse(
        content=result,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )

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
    Upload and process files through the ML services pipeline:
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
                        conversation_id, 
                        pdf_result.get('markdown_content', ''),
                        filename
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
                    conversation_id, 
                    text_content,
                    filename
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
        
        return JSONResponse(
            content={
                'message': 'Files processed successfully',
                'results': results,
                'conversation_id': conversation_id
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"File upload and processing failed: {str(e)}"
        )

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
            async with httpx.AsyncClient(timeout=300.0) as client:
                with open(tmp_file_path, 'rb') as f:
                    files = {'file': (filename, f, 'application/pdf')}
                    response = await client.post(
                        'http://localhost:8001/convert',
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

async def process_document_with_rag(conversation_id: str, content: str, filename: str) -> dict:
    """
    Send processed document content to the RAG system for embedding and vector storage.
    RAG system will be running on port 8002 to avoid conflicts with backend.
    """
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            rag_payload = {
                'course_id': conversation_id,  # Using conversation_id as course_id
                'content': content
            }
            
            response = await client.post(
                'http://localhost:8002/process_document',
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