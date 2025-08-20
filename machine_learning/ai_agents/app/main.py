"""
Speculative AI FastAPI Service

Provides REST API endpoints for the multi-agent speculative AI system.
"""

import logging
import sys
import os
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager 
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ai_agents.orchestrator import MultiAgentOrchestrator
from ai_agents.config import SpeculativeAIConfig
from rag_system.services.rag_service import RAGService
from rag_system.llm_clients.gemini_client import GeminiClient
from rag_system.llm_clients.cerebras_client import CerebrasClient
from rag_system.app.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Suppress noisy external library logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("google").setLevel(logging.WARNING)
logging.getLogger("google_genai").setLevel(logging.WARNING)
logging.getLogger("supabase").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

logger = logging.getLogger("ai_agents.service")


# Global service instances
_orchestrator: Optional[MultiAgentOrchestrator] = None
_initialization_error: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage service lifecycle"""
    global _orchestrator, _initialization_error
    
    try:
        logger.info("Initializing Multi-Agent System Service...")
        
        # Initialize dependencies
        rag_settings = get_settings()
        rag_service = RAGService(rag_settings)
        llm_client = CerebrasClient(
            api_key=rag_settings.cerebras_api_key,
            model="qwen-3-235b-a22b-instruct-2507",
        )
        
        # Initialize orchestrator
        config = SpeculativeAIConfig()
        _orchestrator = MultiAgentOrchestrator(
            config=config,
            rag_service=rag_service,
            llm_client=llm_client,
            logger=logger
        )
        
        logger.info("Multi-Agent System Service initialized successfully")
        
    except Exception as e:
        _initialization_error = f"Service initialization failed: {str(e)}"
        logger.error(_initialization_error)
    
    yield
    
    logger.info("Multi-Agent System Service shutting down")


# Create FastAPI app
app = FastAPI(
    title="Multi-Agent System",
    description="Advanced RAG with multi-agent reasoning and debate-based verification",
    version="1.0.0",
    docs_url="/docs",
    lifespan=lifespan
)


# Request/Response Models
class QueryRequest(BaseModel):
    """Request model for multi-agent system queries"""
    query: str = Field(..., description="User's question or query")
    course_id: str = Field(..., description="Course identifier for context retrieval")
    session_id: Optional[str] = Field(default=None, description="Optional session identifier")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    heavy_model: Optional[str] = Field(default=None, description="Optional heavy model for debate agents")
    course_prompt: Optional[str] = Field(default=None, description="Course-specific system prompt")
    config_overrides: Optional[Dict[str, Any]] = Field(default=None, description="Configuration overrides")


class QueryResponse(BaseModel):
    """Response model for multi-agent system queries"""
    success: bool
    answer: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    debug_info: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


class SystemStatusResponse(BaseModel):
    """Response model for system status"""
    status: str
    orchestrator_status: str
    agents_initialized: int
    configuration: Dict[str, Any]
    execution_stats: Dict[str, Any]


def get_orchestrator() -> MultiAgentOrchestrator:
    """Get orchestrator instance with error handling"""
    global _orchestrator, _initialization_error
    
    if _initialization_error:
        raise HTTPException(
            status_code=503,
            detail=f"Multi-Agent System service unavailable: {_initialization_error}"
        )
    
    if _orchestrator is None:
        raise HTTPException(
            status_code=503,
            detail="Multi-Agent System orchestrator not initialized"
        )
    
    return _orchestrator


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "message": "Speculative AI Multi-Agent System",
        "version": "1.0.0",
        "description": "Advanced RAG with multi-agent reasoning and debate-based verification",
        "endpoints": {
            "process_query": "/query",
            "system_status": "/status",
            "health": "/health",
            "docs": "/docs"
        }
    }


@app.post("/test")
async def test_agents():
    """Test endpoint to debug agent execution"""
    try:
        orchestrator = get_orchestrator()
        
        # Test each agent individually
        from ai_agents.agents.base_agent import AgentInput
        
        test_input = AgentInput(
            query="test query",
            context=[],
            metadata={"course_id": "test_course", "test": True},
            session_id="test"
        )
        
        results = {}
        
        # Test retrieve agent
        try:
            retrieve_result = await orchestrator.retrieve_agent.execute(test_input)
            results["retrieve"] = {"success": retrieve_result.success, "error": retrieve_result.error_message}
        except Exception as e:
            results["retrieve"] = {"success": False, "error": str(e)}
        
        return {
            "test_results": results,
            "orchestrator_status": "operational"
        }
        
    except Exception as e:
        return {
            "error": f"Test failed: {str(e)}",
            "orchestrator_status": "failed"
        }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        orchestrator = get_orchestrator()
        system_status = orchestrator.get_system_status()
        
        return {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",  # Would use datetime.now() in production
            "agents_operational": system_status["agents_initialized"],
            "service": "multi_agent_system"
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "service": "multi_agent_system"
        }


@app.get("/status", response_model=SystemStatusResponse)
async def get_system_status():
    """Get comprehensive system status"""
    try:
        orchestrator = get_orchestrator()
        status = orchestrator.get_system_status()
        
        return SystemStatusResponse(
            status="operational",
            **status
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a query through the speculative AI system
    
    This endpoint orchestrates the complete multi-agent workflow:
    1. Enhanced retrieval with query reframing
    2. Multi-round debate between Strategist and Critic
    3. Moderator-controlled convergence
    4. Final answer synthesis by Reporter
    """
    try:
        orchestrator = get_orchestrator()
        
        # Generate session ID if not provided
        import uuid
        session_id = request.session_id or str(uuid.uuid4())[:8]
        
        # Apply configuration overrides if provided
        if request.config_overrides:
            logger.info(f"Applying config overrides: {request.config_overrides}")
            # Note: In production, you'd create a new config with overrides
            # For now, we'll log the request but use default config
        
        # Process the query and collect the final result
        final_result = None
        async for chunk in orchestrator.process_query(
            query=request.query,
            course_id=request.course_id,
            session_id=session_id,
            metadata=request.metadata or {},
            heavy_model=request.heavy_model,
            course_prompt=request.course_prompt,
        ):
            if chunk.get("status") == "complete":
                final_result = chunk.get("final_response")
                break # Stop iterating after receiving the final response
            elif chunk.get("error"):
                # If an error chunk is yielded, raise an HTTPException immediately
                raise HTTPException(status_code=500, detail=f"Agent processing error: {chunk['error']['message']}")
        
        if not final_result:
            raise HTTPException(status_code=500, detail="Agent system did not return a final response.")
        
        return QueryResponse(**final_result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


@app.post("/reset-metrics")
async def reset_system_metrics():
    """Reset system performance metrics"""
    try:
        orchestrator = get_orchestrator()
        orchestrator.reset_system_metrics()
        
        return {
            "success": True,
            "message": "System metrics reset successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metrics reset failed: {str(e)}")


# Health check for specific components
@app.get("/health/agents")
async def agents_health_check():
    """Check health of individual agents"""
    try:
        orchestrator = get_orchestrator()
        system_status = orchestrator.get_system_status()
        
        return {
            "agents_registered": system_status["agents_registered"],
            "agent_metrics": system_status["agent_metrics"],
            "all_agents_operational": system_status["agents_registered"] == 5  # Expected number of agents
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "agents_operational": False
        }


# Development/debugging endpoints (only in debug mode)
@app.get("/debug/config")
async def get_debug_config():
    """Get current configuration (debug only)"""
    try:
        orchestrator = get_orchestrator()
        
        if not orchestrator.config.enable_debug_logging:
            raise HTTPException(status_code=403, detail="Debug mode not enabled")
        
        return {
            "config": {
                "max_debate_rounds": orchestrator.config.max_debate_rounds,
                "retrieval_k": orchestrator.config.retrieval_k,
                "speculation_rounds": orchestrator.config.speculation_rounds,
                "enable_debug_logging": orchestrator.config.enable_debug_logging,
                "model_routing": {k: v.value for k, v in orchestrator.config.model_routing.items()}
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    from backend.constants import ServiceConfig
    
    uvicorn.run(
        "main:app",
        host=ServiceConfig.DEFAULT_HOST,
        port=ServiceConfig.AGENTS_SYSTEM_PORT,
        reload=True,
        log_level="info"
    ) 