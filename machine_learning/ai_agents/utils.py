"""
Utility functions for AI Agents - LangChain Integration
"""

from typing import Any, Dict, List, Optional
from langchain.schema.runnable import Runnable
from langchain_core.messages import HumanMessage
from langchain.schema import BaseMessage


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
    
    def batch(self, inputs: List[Any], config: Optional[Dict] = None) -> List[str]:
        """Batch invoke"""
        return [self.invoke(inp, config) for inp in inputs]
    
    async def abatch(self, inputs: List[Any], config: Optional[Dict] = None) -> List[str]:
        """Async batch invoke"""
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


async def perform_rag_retrieval(
    rag_service, 
    query: str, 
    course_id: str, 
    logger=None
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
        
    Returns:
        RAG result dict with sources and metadata (with preserved scores)
    """
    try:
        if logger:
            logger.info(f"Performing RAG query: '{query}' for course: {course_id}")
        
        # Use the enhanced method that preserves similarity scores
        if hasattr(rag_service, 'answer_question_with_scores'):
            result = rag_service.answer_question_with_scores(course_id, query)
        else:
            # Fallback to legacy method if enhanced method not available
            if logger:
                logger.warning("Enhanced method not available, falling back to legacy method (scores may be lost)")
            result = rag_service.answer_question(course_id, query)
        
        if logger and result:
            sources = result.get('sources', [])
            logger.info(f"RAG completed - found {len(sources)} sources")
            
            # Log first few sources for debugging
            for i, source in enumerate(sources[:3]):
                content = source.get('content', '')
                score = source.get('score', 'N/A')
                # Show score type for debugging
                score_type = type(score).__name__
                logger.info(f"  {i+1}. Score={score} ({score_type}), Content='{content[:100]}...'")
            
            if len(sources) > 3:
                logger.info(f"  ... and {len(sources) - 3} more sources")
        
        return result
        
    except Exception as e:
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


def enhance_prompt_with_tools(prompt: str, query: str) -> tuple[str, list]:
    """
    Enhance prompt with tool calling capabilities using LangChain native tools.
    
    Args:
        prompt: Original prompt 
        query: User query to analyze for tool needs
        
    Returns:
        Tuple of (enhanced_prompt, relevant_tools)
    """
    from .tools import get_tools_for_query, create_tool_calling_prompt_template
    
    # Get relevant tools for this query
    relevant_tools = get_tools_for_query(query)
    
    if not relevant_tools:
        return prompt, []
    
    # Create tool calling instructions
    tool_instructions = create_tool_calling_prompt_template()
    
    # Enhance the original prompt
    enhanced_prompt = f"""{tool_instructions}

{prompt}

TOOL USAGE FOR THIS QUERY:
The following tools are available and relevant for your response:
{', '.join([tool.name for tool in relevant_tools])}

Use tools when they would improve the accuracy or completeness of your answer."""
    
    return enhanced_prompt, relevant_tools


def create_tool_aware_agent(context, agent_class):
    """
    Create a tool-aware version of any agent class.
    
    This is a factory function that wraps existing agents with tool capabilities
    while maintaining full LangChain/LangGraph compatibility.
    """
    class ToolAwareAgent(agent_class):
        def __init__(self, context):
            super().__init__(context)
            self.tool_aware = True
        
        async def __call__(self, state):
            # Get the query from state
            query = state.get("query", "")
            
            # Check if tools would be useful
            from .tools import get_tools_for_query
            relevant_tools = get_tools_for_query(query)
            
            if relevant_tools:
                # Enhance the state with tool information
                state["available_tools"] = [tool.name for tool in relevant_tools]
                state["tool_objects"] = relevant_tools
                
                # Log tool detection
                if hasattr(self, 'logger'):
                    self.logger.info(f"Detected relevant tools: {[tool.name for tool in relevant_tools]}")
            
            # Call the original agent
            return await super().__call__(state)
    
    return ToolAwareAgent


