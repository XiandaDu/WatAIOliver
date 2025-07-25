"""
Configuration for Speculative AI Multi-Agent System
"""

from typing import Dict, Optional
from pydantic import BaseModel, Field


class SpeculativeAIConfig(BaseModel):
    """Simplified configuration for the Speculative AI system"""
    
    # Core system settings
    max_debate_rounds: int = Field(default=3, description="Maximum number of debate iterations")
    convergence_threshold: float = Field(default=0.7, description="Score threshold for debate convergence")
    
    # Retrieval settings
    retrieval_k: int = Field(default=10, description="Number of documents to retrieve")
    
    # Agent temperatures (only what we actually use)
    strategist_temperature: float = Field(default=0.8, description="Creativity level for strategist")
    critic_temperature: float = Field(default=0.1, description="Conservative temperature for critic")
    
    # Debug
    enable_debug_logging: bool = Field(default=True, description="Enable debug output")
    
    class Config:
        extra = "forbid"  # Prevent unused config options 