import requests
import requests.exceptions
import tempfile
import os
from typing import Optional, Dict, Any, List
from fastapi import UploadFile

from ..logger import logger
from .models import (
    ConversationCreate,
    ConversationUpdate,
    MessageCreate,
    MessageUpdate,
    MessageDelete,
    ChatRequest,
)
from .CRUD import get_messages
import httpx

from backend.constants import TimeoutConfig, ServiceConfig
from machine_learning.constants import ModelConfig
from machine_learning.rag_system.llm_clients.gemini_client import GeminiClient
from machine_learning.rag_system.llm_clients.cerebras_client import CerebrasClient
from machine_learning.rag_system.llm_clients.openai_client import OpenAIClient
from machine_learning.rag_system.llm_clients.anthropic_client import AnthropicClient
from machine_learning.rag_system.app.config import get_settings

BASE_URL = ServiceConfig.NEBULA_BASE_URL

def generate(data: ChatRequest) -> str:
    response = requests.post(f"{BASE_URL}/generate", data={"prompt": data.prompt, "reasoning": True})
    return response.json().get("result", "No result returned")

def generate_vision(prompt: str, image_path: str, fast: bool = False) -> str:
    with open(image_path, "rb") as img:
        files = {"file": img}
        data = {"prompt": prompt, "fast": str(fast).lower()}
        response = requests.post(f"{BASE_URL}/generate_vision", data=data, files=files)
    return response.json().get("result", "No result returned")

def nebula_text_endpoint(data: ChatRequest) -> str:
    """
    Sends a request to the API endpoint and returns the response with conversation context.

    Args:
        data: ChatRequest containing prompt and optional conversation_id

    Returns:
        str: The generated text from the API.
    """
    
    # Build conversation context if conversation_id is provided
    conversation_context = ""
    if data.conversation_id:
        try:
            messages = get_messages(data.conversation_id)
            
            if messages and len(messages) > 1:  # More than just the current message
                # Build conversation history (last 10 messages to avoid token limits)
                recent_messages = messages[-10:] if len(messages) > 10 else messages
                conversation_parts = []
                
                for msg in recent_messages[:-1]:  # Exclude the current message being processed
                    role = "User" if msg['sender'] == 'user' else "Assistant"
                    conversation_parts.append(f"{role}: {msg['content']}")
                
                if conversation_parts:
                    conversation_context = "\n".join(conversation_parts) + "\n\n"
        except Exception as e:
            logger.error(f"Error loading conversation context: {e}")
    
    # Add file context if provided
    file_context = ""
    if data.file_context:
        file_context = f"File content for reference:\n{data.file_context}\n\n"
    
    # Construct the full prompt with context
    if conversation_context:
        full_prompt = f"{file_context}Previous conversation:\n{conversation_context}User: {data.prompt}\n\nAssistant:"
    else:
        full_prompt = f"{file_context}User: {data.prompt}\n\nAssistant:"

    request_data = {
        "prompt": full_prompt,
        "reasoning": True,
    }
    
    try:
        response = requests.post(f"{BASE_URL}/generate", request_data, timeout=TimeoutConfig.CHAT_REQUEST_TIMEOUT)
        if response.status_code == 200:
            return response.json().get("result", "No result returned")
        else:
            return f"Error: {response.status_code} - {response.text}"
    except requests.exceptions.ConnectTimeout:
        logger.error("Connection timeout to UWaterloo server")
        return "Sorry, the AI service is currently unavailable due to network timeout. Please try again later."
    except requests.exceptions.ConnectionError:
        logger.error("Connection error to UWaterloo server") 
        return "Sorry, the AI service is currently unavailable. Please check your internet connection."
    except Exception as e:
        logger.error(f"Request failed: {e}")
        return f"Error communicating with model: {str(e)}"

def llm_text_endpoint(data: ChatRequest) -> str:
    """Generate a response using a specified LLM client."""

    conversation_context = ""
    if data.conversation_id:
        try:
            messages = get_messages(data.conversation_id)
            if messages and len(messages) > 1:
                recent_messages = messages[-10:] if len(messages) > 10 else messages
                parts = []
                for msg in recent_messages[:-1]:
                    role = "User" if msg["sender"] == "user" else "Assistant"
                    parts.append(f"{role}: {msg['content']}")
                if parts:
                    conversation_context = "\n".join(parts) + "\n\n"
        except Exception as e:
            logger.error(f"Error loading conversation context: {e}")

    file_context = ""
    if data.file_context:
        file_context = f"File content for reference:\n{data.file_context}\n\n"

    if conversation_context:
        full_prompt = (
            f"{file_context}Previous conversation:\n{conversation_context}User: {data.prompt}\n\nAssistant:"
        )
    else:
        full_prompt = f"{file_context}User: {data.prompt}\n\nAssistant:"

    settings = get_settings()
    model_name = data.model or "qwen-3-235b-a22b-instruct-2507"
    try:
        if model_name.startswith("gemini"):
            client = GeminiClient(
                api_key=settings.google_api_key,
                model=model_name,
                temperature=ModelConfig.DEFAULT_TEMPERATURE,
            )
        elif model_name.startswith("gpt"):
            client = OpenAIClient(
                api_key=settings.openai_api_key,
                model=model_name,
                temperature=0.6,
                top_p=0.95,
            )
        elif model_name.startswith("claude"):
            client = AnthropicClient(
                api_key=settings.anthropic_api_key,
                model=model_name,
                temperature=0.6,
                top_p=0.95,
            )
        elif model_name.startswith("qwen") or model_name.startswith("cerebras"):
            client = CerebrasClient(
                api_key=settings.cerebras_api_key,
                model=model_name,
                temperature=0.6,
                top_p=0.95,
            )
        else:
            client = GeminiClient(
                api_key=settings.google_api_key,
                model=model_name,
                temperature=ModelConfig.DEFAULT_TEMPERATURE,
            )
        return client.generate(full_prompt)
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        return f"Error communicating with model: {str(e)}"

def open_ask(data: ConversationCreate):
    pass



async def get_most_recent_user_query(conversation_id: str) -> Optional[str]:
    """
    Get the most recent user query from the messages table.
    Returns the content of the last user message in the conversation.
    """
    try:
        messages = get_messages(conversation_id)
        
        # Filter for user messages and get the most recent one
        user_messages = [msg for msg in messages if msg.get('sender') == 'user']
        
        if user_messages:
            # Messages are ordered by created_at, so take the last one
            most_recent = user_messages[-1]
            return most_recent.get('content', '')
        
        return None
    except Exception as e:
        logger.error(f"Error getting recent user query: {e}")
        return None

async def query_rag_system(conversation_id: str, question: str, course_id: Optional[str] = None, rag_model: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Query the RAG system for relevant information based on the user's question.
    """
    try:
        if course_id:
            target_course_id = course_id
        else:
            from src.course.CRUD import get_all_courses
            courses = get_all_courses()
            if not courses:
                return None
                
            target_course_id = str(courses[0]['course_id'])
        async with httpx.AsyncClient(timeout=TimeoutConfig.RAG_QUERY_TIMEOUT) as client:
            rag_payload = {
                'course_id': target_course_id,
                'question': question,
            }
            if rag_model:
                rag_payload['embedding_model'] = rag_model

            
            response = await client.post(
                f'http://{ServiceConfig.LOCALHOST}:{ServiceConfig.RAG_SYSTEM_PORT}/ask',
                json=rag_payload
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"RAG system returned {response.status_code}: {response.text}")
                return None
    
    except Exception as e:
        logger.error(f"Error querying RAG system: {e}")
        return None

def enhance_prompt_with_rag_context(original_prompt: str, rag_result: Optional[Dict[str, Any]]) -> str:
    """
    Enhance the original prompt with context from RAG system if available.
    """
    if not rag_result or not rag_result.get('success'):
        return original_prompt
    
    answer = rag_result.get('answer', '')
    sources = rag_result.get('sources', [])
    
    # Build context from actual document content
    document_context = ""
    if sources:
        document_context = "Relevant document content:\n\n"
        for i, source in enumerate(sources, 1):
            content = source.get('content', '')
            score = source.get('score', 0)
            # Convert score to float if it's a string
            try:
                score_float = float(score)
            except (ValueError, TypeError):
                score_float = 0.0
            document_context += f"Document {i} (relevance: {score_float:.3f}):\n{content}\n\n"
    
    # Create enhanced prompt with actual document content
    enhanced_prompt = f"""You have access to relevant information from uploaded documents. Use this context to answer the user's question.

{document_context}

User question: {original_prompt}

Please provide a comprehensive answer based on the document content above. Reference specific information from the documents when relevant."""
    
    return enhanced_prompt

async def generate_standard_rag_response(data: ChatRequest) -> str:
    """Generate a response using RAG with course-specific prompt."""
    if not data.course_id:
        return "RAG model requires a course selection to access the knowledge base."
    
    try:
        from src.course.CRUD import get_course
        course = get_course(data.course_id)
        
        if not course:
            return "Course not found. Please select a valid course."
        
        # Query RAG system for relevant context
        rag_result = await query_rag_system(
            data.conversation_id or "",
            data.prompt,
            data.course_id,
            data.rag_model
        )
        
        # Get course-specific prompt or use default
        system_prompt = course.get('prompt') or "You are a helpful educational assistant."
        
        # Build enhanced prompt with RAG context
        enhanced_prompt = enhance_prompt_with_rag_context(data.prompt, rag_result)
        
        # Create modified ChatRequest with enhanced prompt and system context
        modified_data = ChatRequest(
            prompt=f"System: {system_prompt}\n\n{enhanced_prompt}",
            conversation_id=data.conversation_id,
            file_context=data.file_context,
            model=data.model
        )
        
        return llm_text_endpoint(modified_data)
        
    except Exception as e:
        return f"Error generating standard response: {str(e)}"

async def generate_response(data: ChatRequest) -> str:
    """Generate response using daily (RAG) or rag (Multi-agent) systems"""
    
    mode = data.mode or "daily"
    
    if mode == "daily":
        return await generate_standard_rag_response(data)
    
    elif mode == "rag":
        if not data.course_id:
            return "Agent System requires a course selection to identify the knowledge base."

        try:
            # Get course prompt for agents system
            from src.course.CRUD import get_course
            course = get_course(data.course_id)
            course_prompt = course.get('prompt') if course else None
            
            result = await query_agents_system(
                data.conversation_id or "",
                data.prompt,
                data.course_id,
                data.rag_model,
                data.heavy_model,
                data.model,
                course_prompt,
            )

            if result and result.get('success'):
                return _format_agents_response_with_debug(result)
            else:
                error_msg = result.get('error', {}).get('message', "An unexpected error occurred.")
                return f"The Agent System encountered an error while processing your request.\n\nDetails: {error_msg}"
        
        except Exception as e:
            return f"The Agent System is currently unavailable. Please try again later.\n\nTechnical details: {str(e)}"
    
    else:
        return f"Unknown mode '{mode}'. Please select 'daily' for Daily mode or 'rag' for Problem Solving mode."

def _format_agents_response_with_debug(result: Dict[str, Any]) -> str:
    """Format agents response with optional debug information"""
    answer_data = result.get('answer', {})
    formatted_answer = format_agents_response(answer_data)
    
    debug_info = result.get('debug_info', {})
    if debug_info:
        debug_summary = f"\n\n**Reasoning Process:**"
        debug_summary += f"\n- Debate Status: {result.get('metadata', {}).get('debate_status', 'unknown')}"
        debug_summary += f"\n- Debate Rounds: {result.get('metadata', {}).get('debate_rounds', 'unknown')}"
        debug_summary += f"\n- Quality Score: {result.get('metadata', {}).get('convergence_score', 'unknown'):.3f}"
        debug_summary += f"\n- Context Items: {debug_info.get('context_items', 'unknown')}"
        formatted_answer += debug_summary
    
    return formatted_answer


async def query_agents_system(
    conversation_id: str,
    query: str,
    course_id: str,
    rag_model: Optional[str] = None,
    heavy_model: Optional[str] = None,
    base_model: Optional[str] = None,
    course_prompt: Optional[str] = None,
) -> dict:
    """Query the multi-agent system with optional model overrides"""
    
    try:
        async with httpx.AsyncClient(timeout=TimeoutConfig.RAG_QUERY_TIMEOUT) as client:
            payload = {
                "query": query,
                "course_id": course_id,
                "session_id": conversation_id,
                "metadata": {"source": "chat_interface", "base_model": base_model}
            }
            if rag_model:
                payload["embedding_model"] = rag_model
            if heavy_model:
                payload["heavy_model"] = heavy_model
            if base_model:
                payload["base_model"] = base_model
            if course_prompt:
                payload["course_prompt"] = course_prompt
            
            response = await client.post(
                f'http://{ServiceConfig.LOCALHOST}:{ServiceConfig.AGENTS_SYSTEM_PORT}/query',
                json=payload
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'success': False,
                    'error': {
                        'type': 'http_error',
                        'message': f'Agents service returned {response.status_code}: {response.text}'
                    }
                }
    
    except Exception as e:
        return {
            'success': False,
            'error': {
                'type': 'connection_error',
                'message': f'Failed to connect to Agents service: {str(e)}'
            }
        }


def format_agents_response(answer_data: dict) -> str:
    """Format the structured agents system response for display"""
    
    if not answer_data:
        return "No answer provided by the Speculative AI system."
    
    formatted_sections = []
    
    # Handle different response formats based on debate status
    if "partial_solution" in answer_data:
        # Deadlock format
        formatted_sections.append("## Partial Solution")
        formatted_sections.append(answer_data.get("partial_solution", ""))
        
        if answer_data.get("areas_of_uncertainty"):
            formatted_sections.append("\n## Areas of Uncertainty")
            formatted_sections.append(answer_data["areas_of_uncertainty"])
        
        if answer_data.get("what_we_can_conclude"):
            formatted_sections.append("\n## What We Can Conclude")
            formatted_sections.append(answer_data["what_we_can_conclude"])
        
        if answer_data.get("recommendations_for_further_exploration"):
            formatted_sections.append("\n## Recommendations for Further Exploration")
            formatted_sections.append(answer_data["recommendations_for_further_exploration"])
    
    else:
        # Standard approved format
        if answer_data.get("introduction"):
            formatted_sections.append("## Introduction")
            formatted_sections.append(answer_data["introduction"])
        
        if answer_data.get("step_by_step_solution"):
            formatted_sections.append("\n## Solution")
            formatted_sections.append(answer_data["step_by_step_solution"])
        
        if answer_data.get("key_takeaways"):
            formatted_sections.append("\n## Key Takeaways")
            formatted_sections.append(answer_data["key_takeaways"])
        
        if answer_data.get("important_notes"):
            formatted_sections.append("\n## Important Notes")
            formatted_sections.append(answer_data["important_notes"])
    
    # Add quality indicators
    quality_indicators = answer_data.get("quality_indicators", {})
    if quality_indicators:
        formatted_sections.append("\n## Quality Assessment")
        verification_level = quality_indicators.get("verification_level", "unknown")
        context_support = quality_indicators.get("context_support", "unknown")
        formatted_sections.append(f"- Verification Level: {verification_level}")
        formatted_sections.append(f"- Context Support: {context_support}")
    
    # Add sources if available
    sources = answer_data.get("sources", [])
    if sources:
        formatted_sections.append("\n## Sources")
        for i, source in enumerate(sources[:5], 1):  # Limit to 5 sources
            formatted_sections.append(f"{i}. {source}")
        
    return "\n".join(formatted_sections) if formatted_sections else "No structured content available."

# File Processing Services

async def process_files_for_chat(files: List[UploadFile], conversation_id: str, user_id: str) -> List[Dict[str, Any]]:
    """Process files for chat context (not sent to RAG)"""
    results = []
    
    for file in files:
        filename = file.filename or 'unknown_file'
        file_content = await file.read()
        
        if filename.lower().endswith('.pdf'):
            result = await _process_pdf_for_chat(file_content, filename)
        elif filename.lower().endswith(('.txt', '.md', '.mdx')):
            result = await _process_text_for_chat(file_content, filename)
        else:
            result = _create_unsupported_file_result(filename)
        
        results.append(result)
    
    return results

async def process_files_for_rag(files: List[UploadFile], course_id: str, user_id: str, rag_model: Optional[str] = None) -> List[Dict[str, Any]]:
    """Process files for RAG knowledge base"""
    results = []
    
    for file in files:
        filename = file.filename or 'unknown_file'
        file_content = await file.read()
        
        if filename.lower().endswith('.pdf'):
            result = await _process_pdf_for_rag(file_content, filename, course_id, rag_model)
        elif filename.lower().endswith(('.txt', '.md', '.mdx')):
            result = await _process_text_for_rag(file_content, filename, course_id, rag_model)
        else:
            result = _create_unsupported_file_result(filename)
        
        results.append(result)
    
    return results

async def _process_pdf_for_chat(file_content: bytes, filename: str) -> Dict[str, Any]:
    """Process PDF for chat context"""
    pdf_result = await _process_pdf_file(file_content, filename)
    
    if pdf_result.get('success'):
        markdown_content = pdf_result.get('markdown_content', '')
        return {
            'filename': filename,
            'type': 'pdf',
            'markdown_content': markdown_content,
            'content_length': len(markdown_content),
            'status': 'completed'
        }
    else:
        return {
            'filename': filename,
            'type': 'pdf',
            'error': pdf_result.get('error_message', 'PDF processing failed'),
            'status': 'failed'
        }

async def _process_text_for_chat(file_content: bytes, filename: str) -> Dict[str, Any]:
    """Process text file for chat context"""
    text_content = file_content.decode('utf-8')
    return {
        'filename': filename,
        'type': 'text',
        'text_content': text_content,
        'content_length': len(text_content),
        'status': 'completed'
    }

async def _process_pdf_for_rag(file_content: bytes, filename: str, course_id: str, rag_model: Optional[str]) -> Dict[str, Any]:
    """Process PDF for RAG knowledge base"""
    pdf_result = await _process_pdf_file(file_content, filename)
    
    if pdf_result.get('success'):
        rag_result = await _process_document_with_rag(
            course_id,
            pdf_result.get('markdown_content', ''),
            filename,
            rag_model
        )
        
        if rag_result.get('success'):
            document_id = rag_result.get('document_id', filename)
            _store_document_metadata(document_id, course_id, filename, 'pdf')
            return {
                'filename': filename,
                'type': 'pdf',
                'pdf_processing': pdf_result,
                'rag_processing': rag_result,
                'status': 'completed'
            }
        else:
            return {
                'filename': filename,
                'type': 'pdf',
                'pdf_processing': pdf_result,
                'rag_processing': rag_result,
                'error': rag_result.get('error_message', 'RAG processing failed'),
                'status': 'failed'
            }
    else:
        return {
            'filename': filename,
            'type': 'pdf',
            'error': pdf_result.get('error_message', 'PDF processing failed'),
            'status': 'failed'
        }

async def _process_text_for_rag(file_content: bytes, filename: str, course_id: str, rag_model: Optional[str]) -> Dict[str, Any]:
    """Process text file for RAG knowledge base"""
    text_content = file_content.decode('utf-8')
    rag_result = await _process_document_with_rag(course_id, text_content, filename, rag_model)
    
    if rag_result.get('success'):
        document_id = rag_result.get('document_id', filename)
        _store_document_metadata(document_id, course_id, filename, 'text')
    
    return {
        'filename': filename,
        'type': 'text',
        'rag_processing': rag_result,
        'status': 'completed'
    }

def _create_unsupported_file_result(filename: str) -> Dict[str, Any]:
    """Create result for unsupported file type"""
    return {
        'filename': filename,
        'type': 'unsupported',
        'error': 'Unsupported file type. Please upload PDF, TXT, MD, or MDX files.',
        'status': 'failed'
    }

async def _process_pdf_file(file_content: bytes, filename: str) -> Dict[str, Any]:
    """Send PDF file to the PDF processor service"""
    try:
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(file_content)
            tmp_file_path = tmp_file.name
        
        try:
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
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
    
    except Exception as e:
        return {
            'success': False,
            'error_message': f'PDF processing failed: {str(e)}'
        }

async def _process_document_with_rag(course_id: str, content: str, filename: str, rag_model: Optional[str] = None) -> Dict[str, Any]:
    """Send processed document content to the RAG system"""
    try:
        async with httpx.AsyncClient(timeout=TimeoutConfig.RAG_PROCESSING_TIMEOUT) as client:
            rag_payload = {
                'course_id': course_id,
                'content': content
            }
            if rag_model:
                rag_payload['embedding_model'] = rag_model
            
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

def _store_document_metadata(document_id: str, course_id: str, filename: str, file_type: str):
    """Store document metadata in the documents table"""
    try:
        from src.supabaseClient import supabase
        supabase.table("documents").insert({
            "document_id": document_id,
            "course_id": course_id,
            "title": filename,
            "content": f"Uploaded {file_type} file: {filename}",
            "term": None
        }).execute()
    except Exception as e:
        logger.error(f"Failed to store document metadata: {e}")
