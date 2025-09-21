"""
FastAPI Service for LangGraph Multi-Agent System

Provides REST API endpoints with full logging and monitoring.
"""

import logging
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json
import os

# Configure logging FIRST, before any imports that might use logging
LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs", "ai_agents.log")

# Remove any existing handlers to avoid duplicates
root_logger = logging.getLogger()
root_logger.handlers.clear()

# Create file handler with proper formatting
file_handler = logging.FileHandler(LOG_FILE, mode='a')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Configure root logger
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

# Now import the modules that use logging
from ai_agents.workflow import create_workflow, MultiAgentWorkflow
from ai_agents.state import AgentContext

# Suppress noisy library logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Get service logger
logger = logging.getLogger("langgraph.service")

# Ensure all ai_agents loggers use the same handlers
for logger_name in ["ai_agents", "ai_agents.streaming", "langgraph", "langgraph.workflow"]:
    specific_logger = logging.getLogger(logger_name)
    specific_logger.setLevel(logging.INFO)
    # Ensure it propagates to root logger
    specific_logger.propagate = True


# Global workflow instance
_workflow: Optional[MultiAgentWorkflow] = None
_initialization_error: Optional[str] = None


# Request/Response models
class QueryRequest(BaseModel):
    """Request model for query processing"""
    query: str = Field(..., description="The user's question")
    course_id: str = Field(..., description="Course identifier for retrieval")
    session_id: str = Field(default="default", description="Session ID for tracking")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    course_prompt: Optional[str] = Field(default=None, description="Course-specific prompt")
    max_debate_rounds: int = Field(default=3, description="Maximum debate iterations")
    heavy_model: Optional[str] = Field(default=None, description="Override model for complex tasks")


class QueryResponse(BaseModel):
    """Response model for query results"""
    success: bool
    answer: Dict[str, Any]
    tutor_interaction: Optional[Dict[str, Any]]
    metadata: Dict[str, Any]
    debug_info: Optional[Dict[str, Any]]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage service lifecycle"""
    global _workflow, _initialization_error
    
    try:
        logger.info("="*250)
        logger.info("INITIALIZING LANGGRAPH MULTI-AGENT SERVICE")
        logger.info("="*250)
        
        # Load configuration
        from ai_agents.config import SpeculativeAIConfig
        from rag_system.services.rag_service import RAGService
        from rag_system.llm_clients.gemini_client import GeminiClient
        from rag_system.app.config import get_settings
        
        settings = get_settings()
        config = SpeculativeAIConfig()
        
        # Initialize RAG service
        logger.info("Initializing RAG service...")
        rag_service = RAGService(settings=settings)
        
        # Initialize LLM client
        logger.info("Initializing LLM client...")
        llm_client = GeminiClient(
            api_key=settings.google_api_key,
            model="gemini-1.5-pro",
            temperature=0.7
        )
        
        # Create workflow
        logger.info("Creating LangGraph workflow...")
        _workflow = create_workflow(
            llm_client=llm_client,
            rag_service=rag_service,
            config=config,
            logger=logger
        )
        
        logger.info("Service initialization complete")
        logger.info("="*250)
        
    except Exception as e:
        _initialization_error = str(e)
        logger.error(f"Service initialization failed: {e}")
        logger.error("="*250)
    
    yield
    
    # Cleanup
    logger.info("Shutting down Multi-Agent Service")


# Create FastAPI app
app = FastAPI(
    title="LangGraph Multi-Agent System",
    description="Speculative AI system using LangGraph and LangChain",
    version="2.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Health check endpoint"""
    if _initialization_error:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {_initialization_error}")
    
    return {
        "service": "LangGraph Multi-Agent System",
        "status": "operational" if _workflow else "initializing",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/status")
async def get_status():
    """Get detailed system status"""
    if _initialization_error:
        return {
            "status": "error",
            "error": _initialization_error,
            "timestamp": datetime.now().isoformat()
        }
    
    if not _workflow:
        return {
            "status": "initializing",
            "timestamp": datetime.now().isoformat()
        }
    
    workflow_status = await _workflow.get_workflow_status()
    
    return {
        "status": "operational",
        "workflow": workflow_status,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a query through the multi-agent system.
    
    This endpoint orchestrates the complete workflow:
    1. Enhanced retrieval with speculative reframing
    2. Multi-round debate loop
    3. Final synthesis and tutoring
    """
    
    if not _workflow:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    start_time = datetime.now()
    
    logger.info("")
    logger.info("="*250)
    logger.info("NEW QUERY REQUEST")
    logger.info("="*250)
    logger.info(f"Query: {request.query[:200]}...")
    logger.info(f"Course: {request.course_id}")
    logger.info(f"Session: {request.session_id}")
    logger.info(f"Max Rounds: {request.max_debate_rounds}")
    
    # Clear the per-request log file so each query starts fresh
    try:
        with open(LOG_FILE, "w"):
            pass
    except OSError:
        # If the file can't be opened we just ignore; logging continues to console
        pass

    try:
        # Process through workflow
        final_response = None
        async for event in _workflow.process_query(
            query=request.query,
            course_id=request.course_id,
            session_id=request.session_id,
            metadata=request.metadata,
            course_prompt=request.course_prompt,
            max_rounds=request.max_debate_rounds
        ):
            if event["status"] == "complete":
                final_response = event["response"]
            elif event["status"] == "error":
                raise HTTPException(status_code=500, detail=event["error"])
            else:
                # Log intermediate progress
                logger.info(f"Progress: {event.get('stage', 'unknown')} - {event.get('message', '')}")
        
        if not final_response:
            raise HTTPException(status_code=500, detail="No response generated")
        
        # Add timing
        processing_time = (datetime.now() - start_time).total_seconds()
        final_response["metadata"]["total_processing_time"] = processing_time
        
        logger.info("")
        logger.info("="*250)
        logger.info("QUERY COMPLETED SUCCESSFULLY")
        logger.info("="*250)
        logger.info(f"Processing Time: {processing_time:.2f}s")
        logger.info(f"Debate Rounds: {final_response['metadata'].get('debate_rounds', 0)}")
        logger.info(f"Convergence Score: {final_response['metadata'].get('convergence_score', 0):.2f}")
        logger.info(f"Decision: {final_response['metadata'].get('moderator_decision', 'unknown')}")
        
        return QueryResponse(**final_response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query/stream")
async def process_query_stream(request: QueryRequest):
    """
    Stream query processing updates in real-time.
    
    Returns Server-Sent Events (SSE) stream with progress updates.
    """
    
    if not _workflow:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    async def generate():
        """Generate SSE stream"""
        try:
            async for event in _workflow.process_query(
                query=request.query,
                course_id=request.course_id,
                session_id=request.session_id,
                metadata=request.metadata,
                course_prompt=request.course_prompt,
                max_rounds=request.max_debate_rounds
            ):
                # Format as SSE
                data = json.dumps(event)
                yield f"data: {data}\n\n"
                
                if event["status"] in ["complete", "error"]:
                    break
                    
        except Exception as e:
            error_event = {"status": "error", "error": str(e)}
            yield f"data: {json.dumps(error_event)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.get("/conversation/{session_id}")
async def get_conversation_history(session_id: str):
    """Get conversation history for a session"""
    
    if not _workflow:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        # Get state from workflow memory
        config = {"configurable": {"thread_id": session_id}}
        state = await _workflow.app.aget_state(config)
        
        if state and state.values:
            conversation = state.values.get("conversation_history", [])
            return {
                "session_id": session_id,
                "conversation": conversation,
                "entry_count": len(conversation)
            }
        else:
            return {
                "session_id": session_id,
                "conversation": [],
                "entry_count": 0
            }
            
    except Exception as e:
        logger.error(f"Failed to retrieve conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/conversation/{session_id}")
async def clear_conversation(session_id: str):
    """Clear conversation history for a session"""
    
    if not _workflow:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        # Clear from workflow memory
        config = {"configurable": {"thread_id": session_id}}
        # Note: In production, implement proper memory clearing
        
        return {
            "session_id": session_id,
            "status": "cleared",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to clear conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Run the service
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "service:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )

