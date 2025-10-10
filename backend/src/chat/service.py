import requests
import requests.exceptions
import tempfile
import os
from typing import Optional, Dict, Any, List, AsyncGenerator
from fastapi import UploadFile
import json

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
from starlette.responses import StreamingResponse

from constants import TimeoutConfig, ServiceConfig
from machine_learning.constants import ModelConfig
from machine_learning.rag_system.llm_clients.gemini_client import GeminiClient
from machine_learning.rag_system.llm_clients.cerebras_client import CerebrasClient
from machine_learning.rag_system.llm_clients.openai_client import OpenAIClient
from machine_learning.rag_system.llm_clients.anthropic_client import AnthropicClient
from machine_learning.rag_system.app.config import get_settings

BASE_URL = ServiceConfig.NEBULA_BASE_URL


def get_custom_model_api_key(course_id: str, model_name: str) -> Optional[str]:
    """Get API key for a custom model in a specific course."""
    if not course_id or not model_name.startswith("custom-"):
        return None

    try:
        from src.course.CRUD import get_course

        course = get_course(course_id)
        if not course:
            return None

        custom_models = course.get("custom_models", []) or []
        custom_model_name = model_name.replace("custom-", "")

        for model in custom_models:
            if model.get("name") == custom_model_name:
                return model.get("api_key")

        return None
    except Exception as e:
        logger.error(f"Error getting custom model API key: {e}")
        return None


def generate(data: ChatRequest) -> str:
    response = requests.post(
        f"{BASE_URL}/generate", data={"prompt": data.prompt, "reasoning": True}
    )
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

                for msg in recent_messages[
                    :-1
                ]:  # Exclude the current message being processed
                    role = "User" if msg["sender"] == "user" else "Assistant"
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
        response = requests.post(
            f"{BASE_URL}/generate",
            request_data,
            timeout=TimeoutConfig.CHAT_REQUEST_TIMEOUT,
        )
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


async def llm_text_endpoint(data: ChatRequest) -> StreamingResponse:
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
        full_prompt = f"{file_context}Previous conversation:\n{conversation_context}User: {data.prompt}\n\nAssistant:"
    else:
        full_prompt = f"{file_context}User: {data.prompt}\n\nAssistant:"

    settings = get_settings()
    model_name = data.model or "qwen-3-235b-a22b-instruct-2507"

    # Check if this is a custom model
    custom_api_key = None
    if model_name.startswith("custom-") and data.course_id:
        custom_api_key = get_custom_model_api_key(data.course_id, model_name)
        if not custom_api_key:
            return f"Custom model '{model_name}' not found or API key not available for this course."

    try:

        async def format_stream_for_sse(stream_generator):
            """
            Convert LLM streaming responses to Server-Sent Events format.

            Ensures consistent JSON-encoded chunks and proper error handling.
            """
            full_response = ""
            try:
                async for chunk in stream_generator:
                    if chunk:
                        full_response += chunk
                        # JSON-encode prevents client-side parsing issues with quotes/newlines
                        json_chunk = json.dumps({"content": chunk})
                        yield f"data: {json_chunk}\n\n"
            except Exception as e:
                # Error recovery: send error as properly formatted SSE
                logger.error(f"Streaming error: {e}")
                error_chunk = json.dumps({"content": f"[Streaming Error: {str(e)}]"})
                yield f"data: {error_chunk}\n\n"
            finally:
                # Debug output for monitoring response quality
                logger.debug(f"LLM Response completed: {len(full_response)} chars")

        if model_name.startswith("gemini"):
            client = GeminiClient(
                api_key=settings.google_api_key,
                model=model_name,
                temperature=ModelConfig.DEFAULT_TEMPERATURE,
            )
            return StreamingResponse(
                format_stream_for_sse(client.generate_stream(full_prompt)),
                media_type="text/event-stream",
            )
        elif model_name.startswith("gpt") or (
            model_name.startswith("custom-") and custom_api_key
        ):
            # Use custom API key if available, otherwise use default
            api_key = custom_api_key if custom_api_key else settings.openai_api_key
            # For custom models, use a default GPT model
            actual_model = (
                "gpt-4o-mini" if model_name.startswith("custom-") else model_name
            )
            client = OpenAIClient(
                api_key=api_key,
                model=actual_model,
                temperature=0.6,
                top_p=0.95,
            )
            return StreamingResponse(
                format_stream_for_sse(client.generate_stream(full_prompt)),
                media_type="text/event-stream",
            )
        elif model_name.startswith("claude"):
            client = AnthropicClient(
                api_key=settings.anthropic_api_key,
                model=model_name,
                temperature=0.6,
                top_p=0.95,
            )
            return StreamingResponse(
                format_stream_for_sse(client.generate_stream(full_prompt)),
                media_type="text/event-stream",
            )
        elif model_name.startswith("qwen") or model_name.startswith("cerebras"):
            client = CerebrasClient(
                api_key=settings.cerebras_api_key,
                model=model_name,
                temperature=0.6,
                top_p=0.95,
            )
            return StreamingResponse(
                format_stream_for_sse(client.generate_stream(full_prompt)),
                media_type="text/event-stream",
            )
        else:
            client = GeminiClient(
                api_key=settings.google_api_key,
                model=model_name,
                temperature=ModelConfig.DEFAULT_TEMPERATURE,
            )
            return StreamingResponse(
                format_stream_for_sse(client.generate_stream(full_prompt)),
                media_type="text/event-stream",
            )
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
        user_messages = [msg for msg in messages if msg.get("sender") == "user"]

        if user_messages:
            # Messages are ordered by created_at, so take the last one
            most_recent = user_messages[-1]
            return most_recent.get("content", "")

        return None
    except Exception as e:
        logger.error(f"Error getting recent user query: {e}")
        return None


class UnifiedRAGService:
    """
    Unified RAG service for both daily and multi-agent modes.
    Ensures consistent behavior and score preservation across all modes.
    """
    
    def __init__(self, logger=None):
        import logging
        self.logger = logger or logging.getLogger(__name__)
    
    async def query_async(self, course_id: str, question: str, rag_model: Optional[str] = None) -> Dict[str, Any]:
        """
        Async query to RAG system - returns results with confidence scores.
        Used by daily mode and can be used by any async context.
        """
        try:
            self.logger.info(f"[UnifiedRAG] Querying course {course_id}: {question[:50]}...")
            
            async with httpx.AsyncClient(timeout=TimeoutConfig.RAG_QUERY_TIMEOUT) as client:
                payload = {
                    "course_id": course_id,
                    "question": question,
                }
                if rag_model:
                    payload["embedding_model"] = rag_model
                
                response = await client.post(
                    f"http://{ServiceConfig.LOCALHOST}:{ServiceConfig.RAG_SYSTEM_PORT}/ask",
                    json=payload,
                )
                
                if response.status_code == 200:
                    result = response.json()
                    sources = result.get('sources', [])
                    
                    # Log scores for debugging
                    self.logger.info(f"[UnifiedRAG] Success - {len(sources)} sources found")
                    for i, source in enumerate(sources[:3]):
                        score = source.get('score', 'N/A')
                        self.logger.info(f"  Source {i+1}: score={score}")
                    
                    return result
                else:
                    self.logger.error(f"[UnifiedRAG] HTTP {response.status_code}: {response.text}")
                    return {
                        "success": False,
                        "error": f"RAG system error: {response.status_code}",
                        "sources": []
                    }
        
        except Exception as e:
            self.logger.error(f"[UnifiedRAG] Exception: {e}")
            return {
                "success": False,
                "error": str(e),
                "sources": []
            }
    
    def query_sync(self, course_id: str, question: str, **kwargs) -> Dict[str, Any]:
        """
        Synchronous wrapper for multi-agent system.
        Handles the async-to-sync conversion properly.
        """
        import asyncio
        import concurrent.futures
        
        try:
            # Use thread pool to run async code when event loop is already running
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self.query_async(course_id, question, kwargs.get('rag_model'))
                )
                return future.result(timeout=60)
        except Exception as e:
            self.logger.error(f"[UnifiedRAG] Sync wrapper error: {e}")
            return {"success": False, "error": str(e), "sources": []}
    
    # Compatibility methods for multi-agent system
    def answer_question(self, course_id: str, question: str, **kwargs):
        """Compatibility method for multi-agent system"""
        return self.query_sync(course_id, question, **kwargs)
    
    def answer_question_with_scores(self, course_id: str, question: str, **kwargs):
        """Compatibility method - all queries now return scores"""
        return self.query_sync(course_id, question, **kwargs)


# Create global instance for easy access
_unified_rag = UnifiedRAGService(logger)


# Legacy compatibility function - redirects to unified service
async def query_rag_system(
    conversation_id: str,  # Kept for compatibility but not used
    question: str,
    course_id: Optional[str] = None,
    rag_model: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Legacy function - now uses UnifiedRAGService.
    Kept for backward compatibility.
    """
    if not course_id:
        from src.course.CRUD import get_all_courses
        courses = get_all_courses()
        if not courses:
            return None
        course_id = str(courses[0]["course_id"])
    
    return await _unified_rag.query_async(course_id, question, rag_model)


def enhance_prompt_with_rag_context(
    original_prompt: str, rag_result: Optional[Dict[str, Any]]
) -> str:
    """
    Enhance the original prompt with context from RAG system if available.
    """
    if not rag_result or not rag_result.get("success"):
        return original_prompt

    answer = rag_result.get("answer", "")
    sources = rag_result.get("sources", [])

    # Build context from actual document content
    document_context = ""
    if sources:
        document_context = "Relevant document content:\n\n"
        for i, source in enumerate(sources, 1):
            content = source.get("content", "")
            score = source.get("score", 0)
            # Convert score to float if it's a string
            try:
                score_float = float(score)
            except (ValueError, TypeError):
                score_float = 0.0
            document_context += (
                f"Document {i} (relevance: {score_float:.3f}):\n{content}\n\n"
            )

    # Create enhanced prompt with actual document content
    enhanced_prompt = f"""You are an educational assistant helping students understand course materials. You have access to relevant information from course documents.

RETRIEVED CONTEXT:
{document_context}

USER QUESTION: {original_prompt}

RENDERING SYSTEM: You are outputting to a Markdown renderer with KaTeX math support. DO NOT use Mermaid diagrams, HTML, or other unsupported formats.

SUPPORTED FORMATS:
LaTeX math: $f(x) = x^2$ and $$f(x) = x^2$$
Regular markdown: **bold**, *italic*, lists, headers
Code blocks: ```python ... ```

NOT SUPPORTED: Mermaid diagrams, HTML tags, custom graphics

EXAMPLES - FIX THESE EXACT PROBLEMS:
"f(x) = x^" →"$f(x) = x^2$" (complete the broken formula)
Lone "π" on separate line →"The $\pi$-periodic extension"
"[-π, π]" →"$[-\pi, \pi]$" (use LaTeX)
"x = ±π, ±π" →"$x = \pm\pi, \pm 2\pi$" (fix repetition)

GOOD OUTPUT EXAMPLES:
"The lesson covered the Fourier series of the $\pi$-periodic extension of $f(x) = x^2$."
"Key intervals: $[-\pi, \pi]$ and $[0, 2\pi]$"

CRITICAL LaTeX RULES:
Always use backslash: $\pi$ NOT $π$ 
Intervals: $[\pi, 3\pi]$ NOT $[π, 3π]$
Plus-minus: $\pm\pi$ NOT $±π$

COMMON MISTAKES TO AVOID:
"$π$" or "$[π, 3π]$" (literal Greek letters cause red errors)
"$ \pi $" (spaces inside math delimiters)  
"$\\pi$" (double backslashes in output)
"$\pi$" (single backslash, no spaces)
"$[\pi, 3\pi]$" (proper LaTeX syntax)

TASK: Transform the retrieved content into clean markdown with proper LaTeX math formatting. NO diagrams, NO Mermaid, NO HTML.

Critical Instructions:
Your output should follow this format: Express your logic using mathematical language and logical symbols whenever possible, especially in mathematics and physics; (use abbreviations like s.t. frequently)
Provide concise explanations in natural English (note: use only English under all circumstances); however, do not place explanations within the same paragraph as equations.
Avoid unnecessarily complicating the problem. If you believe this question could be posed to a high school student or freshman, solve it using methods accessible to those students. For complex problems, use ample line breaks and expand your explanations."""

    print("=== DEBUG RAG PROMPT ===")
    print("ORIGINAL PROMPT:", original_prompt)
    print(
        "ENHANCED PROMPT:", enhanced_prompt[-500:]
    )  # Last 500 chars to see instructions
    print("======================")

    return enhanced_prompt


async def generate_standard_rag_response(data: ChatRequest) -> StreamingResponse:
    """Generate a response using RAG with course-specific prompt."""
    if not data.course_id:

        async def error_generator():
            yield b"RAG model requires a course selection to access the knowledge base."

        return StreamingResponse(error_generator(), media_type="text/plain")

    try:
        from src.course.CRUD import get_course

        course = get_course(data.course_id)

        if not course:

            async def error_generator():
                yield b"Course not found. Please select a valid course."

            return StreamingResponse(error_generator(), media_type="text/plain")

        # Query RAG system for relevant context
        rag_result = await query_rag_system(
            data.conversation_id or "", data.prompt, data.course_id, data.rag_model
        )

        # Get course-specific prompt or use default
        system_prompt = (
            course.get("prompt") or "You are a helpful educational assistant."
        )

        # Build enhanced prompt with RAG context
        enhanced_prompt = enhance_prompt_with_rag_context(data.prompt, rag_result)

        # Create modified ChatRequest with enhanced prompt and system context
        modified_data = ChatRequest(
            prompt=f"System: {system_prompt}\n\n{enhanced_prompt}",
            conversation_id=data.conversation_id,
            file_context=data.file_context,
            model=data.model or "qwen-3-235b-a22b-instruct-2507",
            course_id=data.course_id,
        )

        return await llm_text_endpoint(modified_data)

    except Exception as e:

        async def error_generator():
            yield f"Error generating standard response: {str(e)}".encode("utf-8")

        return StreamingResponse(error_generator(), media_type="text/plain")


async def generate_response(data: ChatRequest) -> StreamingResponse:
    """Generate response using daily (RAG) or rag (Multi-agent) systems"""

    mode = data.mode or "daily"

    # Debug logging to see what's being received
    import logging
    debug_logger = logging.getLogger("ai_agents.debug")
    debug_logger.info(f"=== GENERATE_RESPONSE DEBUG ===")
    debug_logger.info(f"Received mode: '{mode}'")
    debug_logger.info(f"Data.mode: '{data.mode}'")
    debug_logger.info(f"Data.model: '{data.model}'")
    debug_logger.info(f"Data.course_id: '{data.course_id}'")
    debug_logger.info(f"Data.prompt: '{data.prompt[:50]}...'")

    # Log to ai_agents for Problem-Solving mode
    if mode == "rag":
        import logging

        ai_agents_logger = logging.getLogger("ai_agents.streaming")
        ai_agents_logger.info(f"\n=== GENERATE_RESPONSE CALLED ===")
        ai_agents_logger.info(f"Mode: {mode}")
        ai_agents_logger.info(f"Course ID: {data.course_id}")
        ai_agents_logger.info(f"Prompt: {data.prompt[:100]}")  # First 100 chars
    else:
        print(f"\n=== GENERATE_RESPONSE CALLED ===")
        print(f"Mode: {mode}")
        print(f"Course ID: {data.course_id}")
        print(f"Prompt: {data.prompt[:100]}")  # First 100 chars

    async def generate_chunks():
        if mode == "daily":
            streaming_response = await generate_standard_rag_response(data)
            async for chunk in streaming_response.body_iterator:
                yield chunk

        elif mode == "rag":
            if not data.course_id:
                # Send error as content chunk like daily mode
                error_msg = "Agent System requires a course selection to identify the knowledge base."
                yield f"data: {json.dumps({'content': error_msg})}\n\n".encode("utf-8")
                return

            try:
                # Get course prompt for agents system
                from src.course.CRUD import get_course

                course = get_course(data.course_id)
                course_prompt = course.get("prompt") if course else None

                # Collect the full response from agents system
                full_response = ""
                import logging

                ai_agents_logger = logging.getLogger("ai_agents.streaming")
                ai_agents_logger.info("\n=== AGENT SYSTEM START ===")
                chunk_count = 0
                # Send initial reasoning step
                initial_step = {
                    "content": "",
                    "reasoning": {
                        "status": "in_progress",
                        "stage": "retrieve",
                        "message": f"Starting multi-agent analysis for: {data.prompt[:50]}...",
                        "timestamp": "",
                        "agent": "retrieve"
                    }
                }
                yield f"data: {json.dumps(initial_step)}\n\n".encode("utf-8")

                async for chunk in query_agents_system_streaming(
                    data.conversation_id or "",
                    data.prompt,
                    data.course_id,
                    data.rag_model,
                    data.heavy_model,
                    data.model,
                    course_prompt,
                ):
                    chunk_count += 1
                    ai_agents_logger.info(f"=== AGENT CHUNK {chunk_count} RECEIVED ===")
                    ai_agents_logger.info(
                        f"Chunk type: {chunk.get('status', 'unknown')}"
                    )
                    ai_agents_logger.info(f"Chunk keys: {chunk.keys()}")
                    ai_agents_logger.info(f"Raw chunk: {str(chunk)[:200]}")

                    # If it's an error, yield and stop
                    if not chunk.get("success", True):
                        error_msg = chunk.get("error", {}).get(
                            "message", "An unexpected error occurred."
                        )
                        ai_agents_logger.error(f"ERROR: {error_msg}")
                        yield f"data: {json.dumps({'content': f'Error: {error_msg}'})}\n\n".encode(
                            "utf-8"
                        )
                        return

                    # Handle streaming content chunks
                    if (
                        chunk.get("success")
                        and chunk.get("answer")
                        and chunk.get("is_streaming")
                    ):
                        ai_agents_logger.info("=== STREAMING CHUNK RECEIVED ===")
                        answer = chunk.get("answer", {})

                        # Get the streaming content and send it directly to frontend
                        streaming_content = answer.get("step_by_step_solution", "")
                        if streaming_content:
                            ai_agents_logger.debug(
                                f"Sending streaming content: {repr(streaming_content[:50])}..."
                            )
                            chunk_json = json.dumps({"content": streaming_content})
                            yield f"data: {chunk_json}\n\n".encode("utf-8")

                    # Handle final completion signal (no additional content)
                    elif chunk.get("status") == "complete":
                        ai_agents_logger.info("=== STREAMING COMPLETE ===")
                        break
                    elif chunk.get("status") == "in_progress":
                        # Send agent progress to frontend for reasoning display
                        stage = chunk.get('stage', '')
                        message = chunk.get('message', '')
                        ai_agents_logger.debug(f"Agent progress: {stage} - {message}")

                        # Send reasoning metadata to frontend
                        reasoning_chunk = {
                            "content": "",  # No content, just reasoning metadata
                            "reasoning": {
                                "status": "in_progress",
                                "stage": stage,
                                "message": message,
                                "timestamp": chunk.get("timestamp", ""),
                                "agent": chunk.get("agent", ""),
                                "details": chunk.get("details", None)
                            }
                        }
                        yield f"data: {json.dumps(reasoning_chunk)}\n\n".encode("utf-8")
                    else:
                        ai_agents_logger.warning(f"=== UNHANDLED CHUNK TYPE ===")
                        ai_agents_logger.warning(
                            f"Chunk success: {chunk.get('success')}"
                        )
                        ai_agents_logger.warning(f"Has answer: {'answer' in chunk}")
                        ai_agents_logger.warning(f"Has status: {'status' in chunk}")

                ai_agents_logger.info(
                    f"=== AGENT LOOP FINISHED: {chunk_count} chunks processed ==="
                )

                # Streaming implementation complete - content streamed in real-time above

            except Exception as e:
                # Send error as content chunk like daily mode
                ai_agents_logger.error(f"=== EXCEPTION IN AGENT SYSTEM ===")
                ai_agents_logger.error(f"Exception: {str(e)}")
                ai_agents_logger.error(f"Exception type: {type(e)}")
                import traceback

                ai_agents_logger.error(f"Traceback: {traceback.format_exc()}")
                error_msg = f"The Agent System is currently unavailable. Please try again later.\n\nTechnical details: {str(e)}"
                yield f"data: {json.dumps({'content': error_msg})}\n\n".encode("utf-8")

        else:
            # Send error as content chunk like daily mode
            error_msg = f"Unknown mode '{mode}'. Please select 'daily' for Daily mode or 'rag' for Problem Solving mode."
            yield f"data: {json.dumps({'content': error_msg})}\n\n".encode("utf-8")

    # Log to ai_agents for Problem-Solving mode
    if mode == "rag":
        ai_agents_logger.info(f"=== RETURNING STREAMING RESPONSE ===")
        ai_agents_logger.info(f"Mode: {mode}")
    else:
        print(f"=== RETURNING STREAMING RESPONSE ===")
        print(f"Mode: {mode}")
    return StreamingResponse(generate_chunks(), media_type="text/event-stream")


def _format_agents_response_with_debug(result: Dict[str, Any]) -> str:
    """Format agents response with optional debug information"""
    answer_data = result.get("answer", {})
    formatted_answer = format_agents_response(answer_data)

    debug_info = result.get("debug_info", {})
    if debug_info:
        debug_summary = f"\n\n**Reasoning Process:**"
        debug_summary += f"\n- Debate Status: {result.get('metadata', {}).get('debate_status', 'unknown')}"
        debug_summary += f"\n- Debate Rounds: {result.get('metadata', {}).get('debate_rounds', 'unknown')}"
        debug_summary += f"\n- Quality Score: {result.get('metadata', {}).get('convergence_score', 'unknown'):.3f}"
        debug_summary += (
            f"\n- Context Items: {debug_info.get('context_items', 'unknown')}"
        )
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
) -> AsyncGenerator[Dict[str, Any], None]:
    """Query the multi-agent system with optional model overrides"""

    print(f"=== QUERY_AGENTS_SYSTEM CALLED ===")
    print(f"Course ID: {course_id}")
    print(f"Query: {query[:100]}")

    try:
        async with httpx.AsyncClient(timeout=TimeoutConfig.RAG_QUERY_TIMEOUT) as client:
            payload = {
                "query": query,
                "course_id": course_id,
                "session_id": conversation_id,
                "metadata": {"source": "chat_interface", "base_model": base_model},
            }
            if rag_model:
                payload["embedding_model"] = rag_model
            if heavy_model:
                payload["heavy_model"] = heavy_model
            if base_model:
                payload["base_model"] = base_model
            if course_prompt:
                payload["course_prompt"] = course_prompt

            print(f"=== CONNECTING TO AGENT SYSTEM ===")
            print(
                f"URL: http://{ServiceConfig.LOCALHOST}:{ServiceConfig.AGENTS_SYSTEM_PORT}/query"
            )
            print(f"Payload: {payload}")

            async with client.stream(
                "POST",
                f"http://{ServiceConfig.LOCALHOST}:{ServiceConfig.AGENTS_SYSTEM_PORT}/query",
                json=payload,
                headers={"Accept": "text/event-stream"},
            ) as response:
                print(f"=== AGENT RESPONSE STATUS: {response.status_code} ===")
                response.raise_for_status()  # Raise an exception for HTTP errors
                print(f"=== STARTING TO READ AGENT CHUNKS ===")
                chunk_count = 0
                async for chunk in response.aiter_bytes():
                    chunk_count += 1
                    print(f"=== RAW AGENT CHUNK {chunk_count} ===")
                    print(f"Raw bytes: {chunk[:100]}")
                    # Decode each chunk and yield as dictionary
                    # Assuming the agent system sends valid JSON chunks as text/event-stream
                    try:
                        decoded_chunk = chunk.decode("utf-8").strip()
                        print(f"Decoded chunk: {decoded_chunk[:200]}")

                        # The agent system sends raw JSON, not SSE format
                        if decoded_chunk:
                            print(f"Parsing raw JSON from agent system")
                            yield json.loads(decoded_chunk)
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error: {e} - Chunk: {decoded_chunk}")
                        logger.error(
                            f"JSON decode error in agent stream: {e} - Chunk: {decoded_chunk}"
                        )
                        # Yield an error chunk or handle as appropriate
                        yield {
                            "success": False,
                            "error": {
                                "type": "parsing_error",
                                "message": f"Failed to parse agent response chunk: {e}",
                            },
                        }

                print(f"=== FINISHED READING AGENT CHUNKS: {chunk_count} total ===")

    except Exception as e:
        logger.error(f"Failed to connect to Agents service: {str(e)}")
        yield {
            "success": False,
            "error": {
                "type": "connection_error",
                "message": f"Failed to connect to Agents service: {str(e)}",
            },
        }


async def query_agents_system_streaming(
    conversation_id: str,
    query: str,
    course_id: str,
    rag_model: Optional[str] = None,
    heavy_model: Optional[str] = None,
    base_model: Optional[str] = None,
    course_prompt: Optional[str] = None,
) -> AsyncGenerator[Dict[str, Any], None]:
    """Query the multi-agent system with Cerebras streaming for Problem-Solving mode"""

    # Create ai_agents logger for proper logging location
    import logging

    ai_agents_logger = logging.getLogger("ai_agents.streaming")
    ai_agents_logger.setLevel(logging.INFO)

    ai_agents_logger.info(f"=== CEREBRAS STREAMING QUERY_AGENTS_SYSTEM CALLED ===")
    ai_agents_logger.info(f"Course ID: {course_id}")
    ai_agents_logger.info(f"Query: {query[:100]}")

    try:
        # Import here to avoid circular imports
        import sys
        import os

        # Add machine_learning directory to Python path
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        machine_learning_path = os.path.join(project_root, "machine_learning")
        if machine_learning_path not in sys.path:
            sys.path.append(machine_learning_path)

        from ai_agents.workflow import MultiAgentWorkflow, create_workflow
        from ai_agents.state import AgentContext
        from ai_agents.config import SpeculativeAIConfig
        from rag_system.llm_clients.cerebras_client import CerebrasClient
        from rag_system.llm_clients.gemini_client import GeminiClient
        from rag_system.llm_clients.openai_client import OpenAIClient
        from rag_system.llm_clients.anthropic_client import AnthropicClient
        from rag_system.app.config import get_settings

        # Send progress updates during agent system setup
        setup_step = {
            "content": "",
            "reasoning": {
                "status": "in_progress",
                "stage": "setup",
                "message": "Initializing multi-agent workflow and RAG system",
                "timestamp": "",
                "agent": "system"
            }
        }
        yield setup_step

        # Initialize workflow with legitimate RAG service
        config = SpeculativeAIConfig()

        # Get RAG settings first
        rag_settings = get_settings()

        # Create appropriate LLM client based on model (same logic as daily mode)
        model_name = base_model or "qwen-3-235b-a22b-instruct-2507"
        custom_api_key = None
        if model_name.startswith("custom-") and course_id:
            custom_api_key = get_custom_model_api_key(course_id, model_name)

        # Initialize LLM client using same logic as daily mode
        if model_name.startswith("gemini"):
            llm_client = GeminiClient(
                api_key=rag_settings.google_api_key,
                model=model_name,
                temperature=0.6,
            )
        elif model_name.startswith("gpt") or (
            model_name.startswith("custom-") and custom_api_key
        ):
            api_key = custom_api_key if custom_api_key else rag_settings.openai_api_key
            actual_model = (
                "gpt-4o-mini" if model_name.startswith("custom-") else model_name
            )
            llm_client = OpenAIClient(
                api_key=api_key,
                model=actual_model,
                temperature=0.6,
                top_p=0.95,
            )
        elif model_name.startswith("claude"):
            llm_client = AnthropicClient(
                api_key=rag_settings.anthropic_api_key,
                model=model_name,
                temperature=0.6,
                top_p=0.95,
            )
        elif model_name.startswith("qwen") or model_name.startswith("cerebras"):
            llm_client = CerebrasClient(
                api_key=rag_settings.cerebras_api_key,
                model=model_name,
                temperature=0.6,
                top_p=0.95,
            )
        else:
            # Default to Gemini
            llm_client = GeminiClient(
                api_key=rag_settings.google_api_key,
                model=model_name,
                temperature=0.6,
            )

        # Progress callback will be passed directly to the workflow and agents

        # Track progress updates to send via SSE
        rag_progress_queue = []


        def rag_progress_sender(progress_data):
            print(f"RAG_PROGRESS_CALLBACK_CALLED: {progress_data}")
            ai_agents_logger.info(f"=== RAG PROGRESS RECEIVED ===")
            ai_agents_logger.info(f"Progress data: {progress_data}")

            # Create reasoning chunk with correct format for outer layer
            reasoning_chunk = {
                "status": "in_progress",  # Top-level status for outer layer
                "stage": progress_data.get("stage", ""),
                "message": progress_data.get("message", ""),
                "timestamp": "",
                "agent": progress_data.get("agent", ""),
                "details": progress_data.get("details", None)
            }

            # Send directly to the stream (store in a list that the streaming function can access)
            if not hasattr(rag_progress_sender, 'immediate_chunks'):
                rag_progress_sender.immediate_chunks = []
            rag_progress_sender.immediate_chunks.append(reasoning_chunk)

            ai_agents_logger.info(f"=== RAG PROGRESS PREPARED FOR IMMEDIATE SEND ===")
            ai_agents_logger.info(f"Details: {progress_data.get('details', 'None')}")


        # Use direct RAG service and rely on progress callback for updates
        rag_service = UnifiedRAGService(logger=ai_agents_logger)

        # Create the workflow using the new architecture with progress callback
        workflow = create_workflow(
            llm_client=llm_client,
            rag_service=rag_service,
            config=config,
            logger=ai_agents_logger.getChild("workflow"),
            progress_callback=rag_progress_sender
        )

        metadata = {
            "source": "chat_interface",
            "base_model": base_model,
            "streaming_mode": True,
        }

        ai_agents_logger.info("=== STARTING CEREBRAS STREAMING WORKFLOW ===")

        # Track streaming chunks for conversion to agent system format
        is_streaming_content = False
        accumulated_content = ""

        # Only use real progress callbacks - no hardcoded reasoning steps
        ai_agents_logger.info("=== ABOUT TO START WORKFLOW LOOP ===")

        async for chunk in workflow.execute_with_content_streaming(
            query=query,
            course_id=course_id,
            session_id=conversation_id,
            metadata=metadata,
            heavy_model=heavy_model,
            course_prompt=course_prompt,
        ):
            ai_agents_logger.info(
                f"=== WORKFLOW CHUNK RECEIVED: {chunk.get('status', 'unknown')} ==="
            )
            ai_agents_logger.info(f"=== WORKFLOW CHUNK KEYS: {list(chunk.keys())} ===")
            ai_agents_logger.info(f"=== RAG QUEUE SIZE: {len(rag_progress_queue)} ===")

            # Send any immediate RAG progress chunks
            if hasattr(rag_progress_sender, 'immediate_chunks') and rag_progress_sender.immediate_chunks:
                while rag_progress_sender.immediate_chunks:
                    immediate_chunk = rag_progress_sender.immediate_chunks.pop(0)
                    ai_agents_logger.info(f"=== SENDING IMMEDIATE RAG CHUNK ===")
                    ai_agents_logger.info(f"Chunk details: {immediate_chunk.get('details', 'None')}")
                    yield immediate_chunk

            if chunk.get("status") == "streaming" and chunk.get("content"):
                # This is actual Cerebras streaming content
                if not is_streaming_content:
                    is_streaming_content = True
                    ai_agents_logger.info("=== CEREBRAS CONTENT STREAMING STARTED ===")

                content = chunk["content"]
                accumulated_content += content
                ai_agents_logger.debug(f"Streaming chunk: {repr(content[:50])}...")

                # Create a structured answer format that frontend expects (matching non-streaming format)
                streaming_answer = {
                    "introduction": "",
                    "step_by_step_solution": content,  # Stream the actual content
                    "key_takeaways": "",
                    "important_notes": "",
                }

                # Yield the streaming content in the same format as the final response
                yield {
                    "success": True,
                    "answer": streaming_answer,
                    "is_streaming": True,  # Flag to indicate this is streaming content
                }

            elif chunk.get("status") == "complete":
                # Final completion - format as successful agent response
                ai_agents_logger.info(
                    f"=== STREAMING COMPLETE: {len(accumulated_content)} chars ==="
                )

                # Send any remaining queued RAG progress chunks before completion
                if hasattr(rag_progress_sender, 'immediate_chunks') and rag_progress_sender.immediate_chunks:
                    while rag_progress_sender.immediate_chunks:
                        immediate_chunk = rag_progress_sender.immediate_chunks.pop(0)
                        ai_agents_logger.info(f"=== SENDING FINAL QUEUED RAG CHUNK ===")
                        ai_agents_logger.info(f"Chunk details: {immediate_chunk.get('details', 'None')}")
                        yield immediate_chunk

                # Send completion signal to reasoning panel
                yield {
                    "status": "complete",
                    "stage": "complete",
                    "message": "Response complete",
                    "agent": "system",
                    "details": None
                }

                # Get the full response from the workflow
                response = chunk.get("response", {})
                final_answer = response.get("answer", {})

                # If we streamed content, use that as the complete answer
                if accumulated_content:
                    # Parse the streamed content to extract sections
                    final_answer = _parse_streamed_content(accumulated_content)

                yield {
                    "success": True,
                    "answer": final_answer,
                    "metadata": response.get("metadata", {}),
                    "processing_time": response.get("metadata", {}).get(
                        "total_processing_time", 0
                    ),
                }
                break

            elif chunk.get("status") == "in_progress":
                # Forward progress updates
                yield chunk

            elif chunk.get("status") == "error":
                # Handle errors
                yield {
                    "success": False,
                    "error": {
                        "type": "processing_error",
                        "message": chunk.get("error", "Unknown error")
                    }
                }
                break

        # Send any remaining immediate chunks after workflow completes
        if hasattr(rag_progress_sender, 'immediate_chunks') and rag_progress_sender.immediate_chunks:
            ai_agents_logger.info(f"=== SENDING REMAINING {len(rag_progress_sender.immediate_chunks)} CHUNKS ===")
            while rag_progress_sender.immediate_chunks:
                immediate_chunk = rag_progress_sender.immediate_chunks.pop(0)
                ai_agents_logger.info(f"=== SENDING REMAINING RAG CHUNK ===")
                ai_agents_logger.info(f"Chunk details: {immediate_chunk.get('details', 'None')}")
                yield immediate_chunk

    except Exception as e:
        # Create ai_agents logger for error logging
        import logging

        ai_agents_logger = logging.getLogger("ai_agents.streaming")

        ai_agents_logger.error(f"=== STREAMING WORKFLOW ERROR ===")
        ai_agents_logger.error(f"Exception: {str(e)}")
        import traceback

        ai_agents_logger.error(f"Traceback: {traceback.format_exc()}")

        yield {
            "success": False,
            "error": {
                "type": "streaming_error",
                "message": f"Failed to query streaming workflow: {str(e)}",
            },
        }


def _parse_streamed_content(content: str) -> dict:
    """Parse streamed content into structured sections"""
    sections = {
        "introduction": "",
        "step_by_step_solution": "",
        "key_takeaways": "",
        "important_notes": ""
    }
    
    # Split content by section headers
    current_section = None
    lines = content.split('\n')
    current_content = []
    
    for line in lines:
        # Check for section headers
        if line.strip().startswith('## Introduction'):
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = 'introduction'
            current_content = []
        elif line.strip().startswith('## Step-by-Step Solution'):
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = 'step_by_step_solution'
            current_content = []
        elif line.strip().startswith('## Key Takeaways'):
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = 'key_takeaways'
            current_content = []
        elif line.strip().startswith('## Important Notes'):
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = 'important_notes'
            current_content = []
        elif current_section:
            # Add content to current section
            current_content.append(line)
        elif not current_section and line.strip():
            # No section header found yet, treat as step_by_step_solution
            current_section = 'step_by_step_solution'
            current_content.append(line)
    
    # Save the last section
    if current_section and current_content:
        sections[current_section] = '\n'.join(current_content).strip()
    
    # If no sections were found, put everything in step_by_step_solution
    if not any(sections.values()):
        sections['step_by_step_solution'] = content
    
    return sections


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
            formatted_sections.append(
                answer_data["recommendations_for_further_exploration"]
            )

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

    return (
        "\n".join(formatted_sections)
        if formatted_sections
        else "No structured content available."
    )


# File Processing Services


async def process_files_for_chat(
    files: List[UploadFile], conversation_id: str, user_id: str
) -> List[Dict[str, Any]]:
    """Process files for chat context (not sent to RAG)"""
    results = []

    for file in files:
        filename = file.filename or "unknown_file"
        file_content = await file.read()

        if filename.lower().endswith(".pdf"):
            result = await _process_pdf_for_chat(file_content, filename)
        elif filename.lower().endswith((".txt", ".md", ".mdx")):
            result = await _process_text_for_chat(file_content, filename)
        elif filename.lower().endswith((".tex", ".latex")):
            result = await _process_latex_for_chat(file_content, filename)
        else:
            result = _create_unsupported_file_result(filename)

        results.append(result)

    return results


async def process_files_for_rag(
    files: List[UploadFile],
    course_id: str,
    user_id: str,
    rag_model: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Process files for RAG knowledge base"""
    results = []

    for file in files:
        filename = file.filename or "unknown_file"
        file_content = await file.read()

        if filename.lower().endswith(".pdf"):
            result = await _process_pdf_for_rag(
                file_content, filename, course_id, rag_model
            )
        elif filename.lower().endswith((".txt", ".md", ".mdx")):
            result = await _process_text_for_rag(
                file_content, filename, course_id, rag_model
            )
        elif filename.lower().endswith((".tex", ".latex")):
            result = await _process_latex_for_rag(
                file_content, filename, course_id, rag_model
            )
        else:
            result = _create_unsupported_file_result(filename)

        results.append(result)

    return results


async def _process_pdf_for_chat(file_content: bytes, filename: str) -> Dict[str, Any]:
    """Process PDF for chat context"""
    pdf_result = await _process_pdf_file(file_content, filename)

    if pdf_result.get("success"):
        markdown_content = pdf_result.get("markdown_content", "")
        return {
            "filename": filename,
            "type": "pdf",
            "markdown_content": markdown_content,
            "content_length": len(markdown_content),
            "status": "completed",
        }
    else:
        return {
            "filename": filename,
            "type": "pdf",
            "error": pdf_result.get("error_message", "PDF processing failed"),
            "status": "failed",
        }


async def _process_text_for_chat(file_content: bytes, filename: str) -> Dict[str, Any]:
    """Process text file for chat context"""
    text_content = file_content.decode("utf-8")
    return {
        "filename": filename,
        "type": "text",
        "text_content": text_content,
        "content_length": len(text_content),
        "status": "completed",
    }


async def _process_latex_for_chat(file_content: bytes, filename: str) -> Dict[str, Any]:
    """Process LaTeX file for chat context"""
    try:
        latex_content = file_content.decode("utf-8")
        processed_content = _convert_latex_to_text(latex_content)
        return {
            "filename": filename,
            "type": "latex",
            "text_content": processed_content,
            "content_length": len(processed_content),
            "status": "completed",
        }
    except Exception as e:
        logger.error(f"Error processing LaTeX file {filename} for chat: {str(e)}")
        return {
            "filename": filename,
            "type": "latex",
            "error": f"LaTeX processing failed: {str(e)}",
            "status": "failed",
        }


async def _process_pdf_for_rag(
    file_content: bytes, filename: str, course_id: str, rag_model: Optional[str]
) -> Dict[str, Any]:
    """Process PDF for RAG knowledge base"""
    pdf_result = await _process_pdf_file(file_content, filename)

    if pdf_result.get("success"):
        rag_result = await _process_document_with_rag(
            course_id, pdf_result.get("markdown_content", ""), filename, rag_model
        )

        if rag_result.get("success"):
            document_id = rag_result.get("document_id", filename)
            markdown_content = pdf_result.get("markdown_content", "")
            _store_document_metadata(
                document_id, course_id, filename, "pdf", markdown_content
            )
            return {
                "filename": filename,
                "type": "pdf",
                "pdf_processing": pdf_result,
                "rag_processing": rag_result,
                "status": "completed",
            }
        else:
            return {
                "filename": filename,
                "type": "pdf",
                "pdf_processing": pdf_result,
                "rag_processing": rag_result,
                "error": rag_result.get("error_message", "RAG processing failed"),
                "status": "failed",
            }
    else:
        return {
            "filename": filename,
            "type": "pdf",
            "error": pdf_result.get("error_message", "PDF processing failed"),
            "status": "failed",
        }


async def _process_text_for_rag(
    file_content: bytes, filename: str, course_id: str, rag_model: Optional[str]
) -> Dict[str, Any]:
    """Process text file for RAG knowledge base"""
    text_content = file_content.decode("utf-8")
    rag_result = await _process_document_with_rag(
        course_id, text_content, filename, rag_model
    )

    if rag_result.get("success"):
        document_id = rag_result.get("document_id", filename)
        _store_document_metadata(document_id, course_id, filename, "text", text_content)

    return {
        "filename": filename,
        "type": "text",
        "rag_processing": rag_result,
        "status": "completed",
    }


async def _process_latex_for_rag(
    file_content: bytes, filename: str, course_id: str, rag_model: Optional[str]
) -> Dict[str, Any]:
    """Process LaTeX file for RAG knowledge base"""
    try:
        latex_content = file_content.decode("utf-8")

        # Convert LaTeX to readable text by removing LaTeX commands and formatting
        processed_content = _convert_latex_to_text(latex_content)

        rag_result = await _process_document_with_rag(
            course_id, processed_content, filename, rag_model
        )

        if rag_result.get("success"):
            document_id = rag_result.get("document_id", filename)
            _store_document_metadata(
                document_id, course_id, filename, "latex", processed_content
            )

        return {
            "filename": filename,
            "type": "latex",
            "rag_processing": rag_result,
            "processed_content_length": len(processed_content),
            "status": "completed",
        }
    except Exception as e:
        logger.error(f"Error processing LaTeX file {filename}: {str(e)}")
        return {
            "filename": filename,
            "type": "latex",
            "error": f"LaTeX processing failed: {str(e)}",
            "status": "failed",
        }


def _create_unsupported_file_result(filename: str) -> Dict[str, Any]:
    """Create result for unsupported file type"""
    return {
        "filename": filename,
        "type": "unsupported",
        "error": "Unsupported file type. Please upload PDF, TXT, MD, MDX, or LaTeX (.tex, .latex) files.",
        "status": "failed",
    }


async def _process_pdf_file(file_content: bytes, filename: str) -> Dict[str, Any]:
    """Send PDF file to the PDF processor service"""
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(file_content)
            tmp_file_path = tmp_file.name

        try:
            async with httpx.AsyncClient(
                timeout=TimeoutConfig.PDF_PROCESSING_TIMEOUT
            ) as client:
                with open(tmp_file_path, "rb") as f:
                    files = {"file": (filename, f, "application/pdf")}
                    response = await client.post(
                        f"http://{ServiceConfig.LOCALHOST}:{ServiceConfig.PDF_PROCESSOR_PORT}/convert",
                        files=files,
                    )

                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        "success": False,
                        "error_message": f"PDF processor service returned {response.status_code}: {response.text}",
                    }
        finally:
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    except Exception as e:
        return {"success": False, "error_message": f"PDF processing failed: {str(e)}"}


async def _process_document_with_rag(
    course_id: str, content: str, filename: str, rag_model: Optional[str] = None
) -> Dict[str, Any]:
    """Send processed document content to the RAG system"""
    try:
        async with httpx.AsyncClient(
            timeout=TimeoutConfig.RAG_PROCESSING_TIMEOUT
        ) as client:
            rag_payload = {"course_id": course_id, "content": content}
            if rag_model:
                rag_payload["embedding_model"] = rag_model

            response = await client.post(
                f"http://{ServiceConfig.LOCALHOST}:{ServiceConfig.RAG_SYSTEM_PORT}/process_document",
                json=rag_payload,
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "success": False,
                    "error": f"RAG system returned {response.status_code}: {response.text}",
                }

    except Exception as e:
        return {"success": False, "error": f"RAG processing failed: {str(e)}"}


def _store_document_metadata(
    document_id: str,
    course_id: str,
    filename: str,
    file_type: str,
    markdown_content: str = None,
):
    """Store document metadata in the documents table with full markdown content"""
    try:
        from src.supabaseClient import supabase

        # Use the full markdown content instead of placeholder text
        content = (
            markdown_content
            if markdown_content
            else f"Uploaded {file_type} file: {filename}"
        )

        supabase.table("documents").insert(
            {
                "document_id": document_id,
                "course_id": course_id,
                "title": filename,
                "content": content,
                "term": None,
            }
        ).execute()
    except Exception as e:
        logger.error(f"Failed to store document metadata: {e}")


def _convert_latex_to_text(latex_content: str) -> str:
    """Convert LaTeX content to readable text by removing LaTeX commands and formatting"""
    import re

    # Remove LaTeX comments
    text = re.sub(r"%.*$", "", latex_content, flags=re.MULTILINE)

    # Remove document class and package declarations
    text = re.sub(r"\\documentclass.*?\{.*?\}", "", text)
    text = re.sub(r"\\usepackage.*?\{.*?\}", "", text)

    # Remove begin/end document
    text = re.sub(r"\\begin\{document\}", "", text)
    text = re.sub(r"\\end\{document\}", "", text)

    # Remove common LaTeX commands
    text = re.sub(r"\\title\{([^}]*)\}", r"Title: \1", text)
    text = re.sub(r"\\author\{([^}]*)\}", r"Author: \1", text)
    text = re.sub(r"\\date\{([^}]*)\}", r"Date: \1", text)
    text = re.sub(r"\\section\{([^}]*)\}", r"\n\n\1\n", text)
    text = re.sub(r"\\subsection\{([^}]*)\}", r"\n\n\1\n", text)
    text = re.sub(r"\\subsubsection\{([^}]*)\}", r"\n\n\1\n", text)
    text = re.sub(r"\\paragraph\{([^}]*)\}", r"\n\1\n", text)

    # Preserve math content: keep inline/block math as-is
    # Just ensure we don't break math by touching inner content here.

    # Unwrap common text environments while preserving their content
    text = re.sub(
        r"\\begin\{itemize\}(.*?)\\end\{itemize\}", r"\1", text, flags=re.DOTALL
    )
    text = re.sub(
        r"\\begin\{enumerate\}(.*?)\\end\{enumerate\}", r"\1", text, flags=re.DOTALL
    )
    text = re.sub(r"\\begin\{quote\}(.*?)\\end\{quote\}", r"\1", text, flags=re.DOTALL)
    text = re.sub(
        r"\\begin\{abstract\}(.*?)\\end\{abstract\}",
        r"Abstract: \1",
        text,
        flags=re.DOTALL,
    )

    # Remove item commands
    text = re.sub(r"\\item\s*", "• ", text)

    # Remove text formatting commands
    text = re.sub(r"\\textbf\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\textit\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\emph\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\underline\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\texttt\{([^}]*)\}", r"\1", text)

    # Remove citation and reference commands
    text = re.sub(r"\\cite\{[^}]*\}", "[CITATION]", text)
    text = re.sub(r"\\ref\{[^}]*\}", "[REFERENCE]", text)
    text = re.sub(r"\\label\{[^}]*\}", "", text)

    # Remove figure and table environments
    text = re.sub(r"\\begin\{figure\}.*?\\end\{figure\}", "", text, flags=re.DOTALL)
    text = re.sub(r"\\begin\{table\}.*?\\end\{table\}", "", text, flags=re.DOTALL)

    # Relaxed cleanup: unwrap single-arg commands by keeping their content; leave others intact
    text = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", text)
    # Do NOT strip bare commands like \alpha to avoid losing LaTeX semantics

    # Clean up whitespace
    text = re.sub(r"\n\s*\n\s*\n", "\n\n", text)  # Remove excessive newlines
    text = re.sub(r"^\s+", "", text, flags=re.MULTILINE)  # Remove leading whitespace
    text = re.sub(r"\s+$", "", text, flags=re.MULTILINE)  # Remove trailing whitespace

    return text.strip()
