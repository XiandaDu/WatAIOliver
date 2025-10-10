"""
Utility functions for AI Agents - LangChain Integration
"""

from typing import Any, Dict, List, Optional
from langchain.schema.runnable import Runnable
from langchain_core.messages import HumanMessage
from langchain.schema import BaseMessage
import os
from datetime import datetime


class LLMClientAdapter(Runnable):
    """
    LangChain Runnable adapter for our custom LLM clients.
    
    This adapter allows our GeminiClient, CerebrasClient, etc. to work
    seamlessly with LangChain chains and tools.
    """
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        
        # Check if client has get_llm_client method (like GeminiClient)
        if hasattr(llm_client, 'get_llm_client'):
            self.native_llm = llm_client.get_llm_client()
            self.use_native = True
        else:
            self.native_llm = None
            self.use_native = False
    
    def invoke(self, input: Any, config: Optional[Dict] = None) -> str:
        """Invoke the LLM with input"""
        # Handle different input types
        if isinstance(input, str):
            prompt = input
        elif isinstance(input, dict):
            # Handle prompt template outputs
            if 'text' in input:
                prompt = input['text']
            else:
                prompt = str(input)
        elif isinstance(input, BaseMessage):
            prompt = input.content
        elif isinstance(input, list):
            # Handle list of messages
            prompt = "\n".join([
                msg.content if isinstance(msg, BaseMessage) else str(msg)
                for msg in input
            ])
        else:
            prompt = str(input)
        
        # Use native LangChain LLM if available (like GeminiClient)
        if self.use_native and self.native_llm:
            response = self.native_llm.invoke(prompt)
            return response.content if hasattr(response, 'content') else str(response)
        else:
            # Fallback to our custom generate method
            return self.llm_client.generate(prompt)
    
    async def ainvoke(self, input: Any, config: Optional[Dict] = None) -> str:
        """Async invoke - fallback to sync for now"""
        return self.invoke(input, config)
    
    def batch(self, inputs: List[Any], config: Optional[Dict] = None, **kwargs) -> List[str]:
        """Batch invoke"""
        return [self.invoke(inp, config) for inp in inputs]

    async def abatch(self, inputs: List[Any], config: Optional[Dict] = None, **kwargs) -> List[str]:
        """Async batch invoke - handles return_exceptions parameter"""
        return self.batch(inputs, config)
    
    def stream(self, input: Any, config: Optional[Dict] = None):
        """Stream invoke - not implemented for most clients"""
        result = self.invoke(input, config)
        yield result
    
    async def astream(self, input: Any, config: Optional[Dict] = None):
        """Async stream invoke"""
        result = await self.ainvoke(input, config)
        yield result


def create_langchain_llm(llm_client, temperature: float = None, streaming: bool = False) -> Runnable:
    """
    Create a LangChain-compatible Runnable from our LLM clients.

    Args:
        llm_client: Our custom LLM client (GeminiClient, CerebrasClient, etc.)
        temperature: Override temperature setting (optional)
        streaming: Whether to enable streaming (for compatible clients)

    Returns:
        A LangChain Runnable that can be used in chains
    """
    # Check the class name to determine the correct approach
    client_type = type(llm_client).__name__

    # For OpenAI client, create a proper LangChain ChatOpenAI instance
    if client_type == "OpenAIClient":
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                api_key=llm_client.api_key,
                model=llm_client.model,
                temperature=temperature or llm_client.temperature,
                top_p=llm_client.top_p
            )
        except ImportError:
            # Fallback to adapter if langchain_openai is not available
            pass

    # For GeminiClient and CerebrasClient, try to use native LangChain LLM first
    if hasattr(llm_client, 'get_llm_client'):
        native_llm = llm_client.get_llm_client()
        # Check if it's already a Runnable
        if isinstance(native_llm, Runnable):
            # For temperature override, we might need to reconfigure
            if temperature is not None and hasattr(native_llm, 'temperature'):
                native_llm.temperature = temperature
            # For streaming, LangChain LLMs handle this via astream method
            return native_llm

    # Otherwise, wrap in our adapter
    adapter = LLMClientAdapter(llm_client)
    # Pass temperature to adapter if needed
    if temperature is not None and hasattr(adapter, 'temperature'):
        adapter.temperature = temperature
    return adapter


# Simple file-based debug logging
def _debug_log(message: str, filename: str = "multi_agent_debug.log"):
    """Simple file-based logging for debugging when regular logging fails"""
    try:
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
        log_file = os.path.join(log_dir, filename)
        with open(log_file, "a") as f:
            f.write(f"[{datetime.now().isoformat()}] {message}\n")
    except:
        pass  # Fail silently


async def perform_rag_retrieval(
    rag_service,
    query: str,
    course_id: str,
    logger=None,
    progress_callback=None,
    query_type: str = "original"
) -> Optional[Dict[str, Any]]:
    """
    Perform RAG retrieval using the enhanced service method that preserves scores.

    Uses the new answer_question_with_scores method that directly accesses vector search
    to preserve similarity scores that were being lost in the retriever chain.

    Args:
        rag_service: The RAG service instance
        query: Query string
        course_id: Course identifier
        logger: Optional logger
        progress_callback: Optional function to send progress updates

    Returns:
        RAG result dict with sources and metadata (with preserved scores)
    """
    try:
        _debug_log(f"\n=== PERFORM_RAG_RETRIEVAL CALLED ===")
        _debug_log(f"Query: '{query}'")
        _debug_log(f"Course ID: {course_id}")
        _debug_log(f"RAG Service Type: {type(rag_service).__name__}")
        
        if logger:
            logger.info(f"Performing RAG query: '{query}' for course: {course_id}")

        # Send progress update before RAG operation
        if progress_callback:
            try:
                progress_data = {
                    "status": "in_progress",
                    "stage": "retrieve",
                    "message": f"🔍 Searching: '{query[:60]}{'...' if len(query) > 60 else ''}'",
                    "agent": "retrieve",
                    "details": {
                        "query": query,
                        "type": "search_start",
                        "query_type": query_type
                    }
                }
                _debug_log(f"=== SENDING RAG PROGRESS UPDATE ===")
                _debug_log(f"Progress data: {progress_data}")
                if logger:
                    logger.info(f"RAG: Sending progress update: {progress_data['message']}")
                progress_callback(progress_data)
                _debug_log(f"=== RAG PROGRESS UPDATE SENT ===")
            except Exception as e:
                _debug_log(f"=== RAG PROGRESS UPDATE FAILED: {e} ===")
                if logger:
                    logger.error(f"Failed to send progress update: {e}")
        else:
            _debug_log(f"=== NO PROGRESS CALLBACK PROVIDED ===")
            if logger:
                logger.warning("RAG: No progress callback provided")

        # Use the enhanced method that preserves similarity scores
        _debug_log(f"Calling answer_question_with_scores...")
        result = rag_service.answer_question_with_scores(course_id, query)
        _debug_log(f"Result: success={result.get('success') if result else 'None'}")

        if logger and result:
            sources = result.get('sources', [])
            logger.info(f"RAG completed - found {len(sources)} sources")
            _debug_log(f"Sources found: {len(sources)}")

            # Always log the actual RAG results to debug log for extraction
            for i, source in enumerate(sources[:3]):
                content = source.get('content', '')
                score = source.get('score', 'N/A')
                score_type = type(score).__name__
                # Log to both logger and debug log
                logger.info(f"  {i+1}. Score={score} ({score_type}), Content='{content[:100]}...'")
                _debug_log(f"  Source {i+1}: Score={score} ({score_type}), Content='{content[:50]}...'")

            if len(sources) > 3:
                logger.info(f"  ... and {len(sources) - 3} more sources")
                _debug_log(f"  ... and {len(sources) - 3} more sources")

            # Send progress update with detailed results
            if progress_callback:
                try:
                    if sources:
                        scores = [f"{s.get('score', 0):.3f}" for s in sources[:3]]
                        completion_data = {
                            "status": "in_progress",
                            "stage": "retrieve_complete",
                            "message": f"✅ Found {len(sources)} documents (top scores: {', '.join(scores)})",
                            "agent": "retrieve",
                            "details": {
                                "query": query,
                                "type": "search_complete",
                                "query_type": query_type,
                                "total_sources": len(sources),
                                "top_sources": [
                                    {
                                        "score": float(s.get('score', 0)),
                                        "content_preview": s.get('content', '')[:100] + ('...' if len(s.get('content', '')) > 100 else ''),
                                        "metadata": s.get('metadata', {})
                                    }
                                    for s in sources[:3]
                                ],
                                "all_scores": [float(s.get('score', 0)) for s in sources]
                            }
                        }
                        _debug_log(f"=== SENDING RAG COMPLETION UPDATE ===")
                        _debug_log(f"Completion data: {completion_data}")
                        if logger:
                            logger.info(f"RAG: Sending completion update: {completion_data['message']}")
                        progress_callback(completion_data)
                        _debug_log(f"=== RAG COMPLETION UPDATE SENT ===")
                    else:
                        no_results_data = {
                            "status": "in_progress",
                            "stage": "retrieve_complete",
                            "message": "⚠️ No relevant documents found",
                            "agent": "retrieve"
                        }
                        _debug_log(f"=== SENDING RAG NO RESULTS UPDATE ===")
                        progress_callback(no_results_data)
                        _debug_log(f"=== RAG NO RESULTS UPDATE SENT ===")
                except Exception as e:
                    _debug_log(f"=== RAG COMPLETION UPDATE FAILED: {e} ===")
                    if logger:
                        logger.error(f"Failed to send completion progress: {e}")
            else:
                _debug_log(f"=== NO PROGRESS CALLBACK FOR COMPLETION ===")
                if logger:
                    logger.warning("RAG: No progress callback for completion")
        
        # Enhance the result with structured RAG info for easy access
        if result and result.get('success'):
            sources = result.get('sources', [])
            if sources:
                result['rag_info'] = {
                    'query': query,
                    'query_type': query_type,
                    'document_count': len(sources),
                    'top_scores': [float(s.get('score', 0)) for s in sources[:3]],
                    'all_scores': [float(s.get('score', 0)) for s in sources],
                    'formatted_message': f"Retrieved {len(sources)} documents with scores: {', '.join([f'{s.get('score', 0):.3f}' for s in sources[:3]])}"
                }

        return result
        
    except Exception as e:
        _debug_log(f"ERROR in perform_rag_retrieval: {e}")
        _debug_log(f"Exception type: {type(e).__name__}")
        import traceback
        _debug_log(f"Traceback: {traceback.format_exc()}")
        
        if logger:
            logger.error(f"RAG query failed: {e}")
        return None


async def debug_course_chunks(
    rag_service,
    course_id: str, 
    query: str = None,
    logger=None
):
    """
    Debug function to show chunks from a course, adapted for LangChain native approach.
    
    This replicates the legacy _debug_course_chunks functionality but works with
    our LangChain-integrated system.
    """
    try:
        if not rag_service:
            if logger:
                logger.info(f"DEBUG: No RAG service available for course {course_id}")
            return
        
        if logger:
            logger.info(f"DEBUG: Checking chunks for course {course_id}")
        
        # Get the vector client from RAG service
        vector_client = getattr(rag_service, 'vector_client', None)
        if not vector_client:
            if logger:
                logger.info(f"DEBUG: No vector client available for course {course_id}")
            return
        
        # First, get any chunks to show they exist
        try:
            raw_results = vector_client.similarity_search(
                query="course content", 
                k=3, 
                filter={"course_id": course_id}
            )
            
            if raw_results:
                if logger:
                    logger.info(f"DEBUG: Found {len(raw_results)} chunks in course {course_id}")
                
                # If we have the actual query, show similarity scores
                if query:
                    try:
                        scored_results = vector_client.similarity_search_with_score(
                            query=query,
                            k=3,
                            filter={"course_id": course_id}
                        )
                        
                        if logger:
                            logger.info(f"DEBUG: Similarity scores for query '{query[:50]}...':")
                            for i, (doc, score) in enumerate(scored_results, 1):
                                content_preview = doc.page_content[:80] + '...' if len(doc.page_content) > 80 else doc.page_content
                                metadata = doc.metadata or {}
                                chunk_id = metadata.get('chunk_index', 'unknown')
                                logger.info(f"   {i}. Chunk {chunk_id} | Score: {score:.4f} | {content_preview}")
                    
                    except Exception as score_error:
                        if logger:
                            logger.error(f"DEBUG: Error getting similarity scores: {score_error}")
                            # Fallback to showing chunks without scores
                            for i, doc in enumerate(raw_results, 1):
                                content_preview = doc.page_content[:80] + '...' if len(doc.page_content) > 80 else doc.page_content
                                metadata = doc.metadata or {}
                                chunk_id = metadata.get('chunk_index', 'unknown')
                                logger.info(f"   {i}. Chunk {chunk_id}: {content_preview}")
                else:
                    # Just show the chunks without scores
                    if logger:
                        for i, doc in enumerate(raw_results, 1):
                            content_preview = doc.page_content[:80] + '...' if len(doc.page_content) > 80 else doc.page_content
                            metadata = doc.metadata or {}
                            chunk_id = metadata.get('chunk_index', 'unknown')
                            logger.info(f"   {i}. Chunk {chunk_id}: {content_preview}")
            else:
                if logger:
                    logger.info(f"DEBUG: No chunks found in course {course_id} database")
        
        except Exception as search_error:
            if logger:
                logger.error(f"DEBUG: Error searching course {course_id}: {search_error}")
    
    except Exception as e:
        if logger:
            logger.error(f"DEBUG: Failed to debug course chunks: {e}")


def format_rag_results_for_agents(rag_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Format RAG results for agent consumption, matching legacy format.
    
    Args:
        rag_result: Raw RAG service result
        
    Returns:
        List of formatted result dictionaries
    """
    if not rag_result or not rag_result.get('success'):
        return []
    
    sources = rag_result.get('sources', [])
    formatted_results = []
    
    for i, source in enumerate(sources):
        formatted_item = {
            "index": i,
            "content": source.get('content', ''),
            "score": source.get('score', 0.0),
            "source": source.get('metadata', {})
        }
        formatted_results.append(formatted_item)
    
    return formatted_results

