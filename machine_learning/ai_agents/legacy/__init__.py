"""
LangGraph Multi-Agent System Implementation

A fully LangChain/LangGraph integrated multi-agent system for speculative AI.
"""

from .workflow import MultiAgentWorkflow, create_workflow
from .state import WorkflowState, AgentContext, initialize_state
from .service import app

__all__ = [
    "MultiAgentWorkflow",
    "create_workflow",
    "WorkflowState",
    "AgentContext",
    "initialize_state",
    "app"
]
