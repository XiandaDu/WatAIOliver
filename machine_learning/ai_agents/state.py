"""
LangGraph State Management for Multi-Agent System

Defines the shared state that flows through the agent graph.
"""

from typing import TypedDict, List, Dict, Any, Optional, Literal
from dataclasses import dataclass, field
from datetime import datetime


class ChainOfThought(TypedDict):
    """Chain of thought step structure"""
    step: int
    thought: str
    confidence: float


class Critique(TypedDict):
    """Critique structure from Critic agent"""
    type: Literal["logic_flaw", "fact_contradiction", "hallucination", "calculation_error"]
    severity: Literal["low", "medium", "high", "critical"]
    description: str
    step_ref: Optional[int]
    claim: Optional[str]


class RetrievalResult(TypedDict):
    """Structure for retrieval results"""
    content: str
    score: float
    source: str
    metadata: Dict[str, Any]


class DraftContent(TypedDict):
    """Draft content from Strategist"""
    draft_id: str
    content: str
    chain_of_thought: List[ChainOfThought]
    timestamp: str


class WorkflowState(TypedDict):
    """
    Main state object that flows through the LangGraph workflow.
    All agents read from and write to this shared state.
    """
    # Input fields
    query: str
    course_id: str
    session_id: str
    course_prompt: Optional[str]
    metadata: Dict[str, Any]
    
    # Retrieval stage
    retrieval_results: List[RetrievalResult]
    retrieval_quality_score: float
    retrieval_strategy: str
    speculative_queries: List[str]
    formatted_retrieval_output: Optional[Any]  # JSON-formatted retrieval output
    
    # Debate loop fields
    current_round: int
    max_rounds: int
    draft: Optional[DraftContent]
    critiques: List[Critique]
    moderator_decision: Literal["converged", "iterate", "abort_deadlock", "escalate_with_warning", "pending"]
    moderator_feedback: Optional[str]
    convergence_score: float
    
    # Final output fields
    final_answer: Optional[Dict[str, Any]]
    tutor_interaction: Optional[Dict[str, Any]]
    
    # Tracking and logging
    conversation_history: List[Dict[str, Any]]
    execution_stats: Dict[str, Any]
    processing_times: Dict[str, float]
    error_messages: List[str]
    
    # Control flow
    workflow_status: Literal["initializing", "retrieving", "debating", "synthesizing", "tutoring", "completed", "failed"]
    should_continue: bool


@dataclass
class AgentContext:
    """
    Context object for individual agent execution.
    Provides access to external services and configuration.
    """
    llm_client: Any
    rag_service: Any
    config: Any
    logger: Any
    
    # Model routing based on task complexity
    model_routing: Dict[str, str] = field(default_factory=lambda: {
        "retrieve_rerank": "gemini-1.5-flash",
        "strategist": "gemini-1.5-pro",
        "critic": "gemini-1.5-pro",
        "moderator": "gemini-1.5-flash",
        "reporter": "gemini-1.5-pro",
        "tutor": "gemini-1.5-flash"
    })
    
    def get_model_for_task(self, task: str) -> str:
        """Get appropriate model for a given task"""
        return self.model_routing.get(task, "gemini-1.5-flash")


def initialize_state(
    query: str,
    course_id: str,
    session_id: str,
    metadata: Optional[Dict[str, Any]] = None,
    course_prompt: Optional[str] = None,
    max_rounds: int = 3
) -> WorkflowState:
    """Initialize a new workflow state"""
    return WorkflowState(
        # Input
        query=query,
        course_id=course_id,
        session_id=session_id,
        course_prompt=course_prompt,
        metadata=metadata or {},
        
        # Retrieval
        retrieval_results=[],
        retrieval_quality_score=0.0,
        retrieval_strategy="initial",
        speculative_queries=[],
        
        # Debate
        current_round=0,
        max_rounds=max_rounds,
        draft=None,
        critiques=[],
        moderator_decision="pending",
        moderator_feedback=None,
        convergence_score=0.0,
        
        # Output
        final_answer=None,
        tutor_interaction=None,
        
        # Tracking
        conversation_history=[],
        execution_stats={
            "start_time": datetime.now().isoformat(),
            "total_queries": 1
        },
        processing_times={},
        error_messages=[],
        
        # Control
        workflow_status="initializing",
        should_continue=True
    )


def log_agent_execution(
    state: WorkflowState,
    agent_name: str,
    input_summary: str,
    output_summary: str,
    processing_time: float,
    success: bool = True
) -> None:
    """Helper to log agent execution to conversation history"""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "agent": agent_name,
        "round": state.get("current_round", 0),
        "input": input_summary,
        "output": output_summary,
        "processing_time": processing_time,
        "success": success
    }
    
    if "conversation_history" not in state:
        state["conversation_history"] = []
    state["conversation_history"].append(entry)
    
    # Update processing times
    if "processing_times" not in state:
        state["processing_times"] = {}
    state["processing_times"][agent_name] = state["processing_times"].get(agent_name, 0) + processing_time
