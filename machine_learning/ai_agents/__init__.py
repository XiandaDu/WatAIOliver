"""
AI Agents Package - LangGraph Multi-Agent System

A fully LangChain/LangGraph integrated multi-agent system for speculative AI.
"""

__version__ = "2.0.0"

# Lazy imports to avoid circular dependencies
def get_workflow():
    from ai_agents.workflow import MultiAgentWorkflow, create_workflow
    return MultiAgentWorkflow, create_workflow

def get_state():
    from ai_agents.state import WorkflowState, AgentContext, initialize_state
    return WorkflowState, AgentContext, initialize_state

def get_config():
    from ai_agents.config import SpeculativeAIConfig
    return SpeculativeAIConfig

def get_app():
    from ai_agents.service import app
    return app
