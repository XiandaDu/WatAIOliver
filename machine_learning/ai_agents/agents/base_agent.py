"""
Base Agent Class for Speculative AI Multi-Agent System

Simplified base class without over-engineered registry system.
"""

import time
import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from ai_agents.config import SpeculativeAIConfig


class AgentRole(Enum):
    """Agent roles in the speculative AI system"""
    RETRIEVE = "retrieve" 
    STRATEGIST = "strategist"
    CRITIC = "critic"
    MODERATOR = "moderator"
    REPORTER = "reporter"
    TUTOR = "tutor"


@dataclass
class AgentInput:
    """Standardized input format for all agents"""
    query: str
    context: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    session_id: str


@dataclass 
class AgentOutput:
    """Standardized output format for all agents"""
    success: bool
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    processing_time: float
    agent_role: AgentRole
    error_message: Optional[str] = None


class BaseAgent(ABC):
    """Simplified base class for all agents"""
    
    def __init__(
        self,
        agent_role: AgentRole,
        config: SpeculativeAIConfig,
        llm_client=None,
        logger: Optional[logging.Logger] = None
    ):
        self.agent_role = agent_role
        self.config = config
        self.llm_client = llm_client
        self.logger = logger or logging.getLogger(f"ai_agents.{agent_role.value}")
        
        # Simple performance tracking
        self.execution_count = 0
        self.total_processing_time = 0.0
        self.error_count = 0
    
    def get_temperature(self) -> float:
        """Get appropriate temperature setting for this agent"""
        if self.agent_role == AgentRole.STRATEGIST:
            return self.config.strategist_temperature
        elif self.agent_role == AgentRole.CRITIC:
            return self.config.critic_temperature
        else:
            return 0.3  # Default conservative temperature
    
    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        """Execute the agent with error handling and metrics tracking"""
        start_time = time.time()
        self.execution_count += 1
        
        try:
            result = await self.process(agent_input)
            processing_time = time.time() - start_time
            self.total_processing_time += processing_time
            
            if result.success and self.config.enable_debug_logging:
                self.logger.info(f"{self.agent_role.value.title()} completed in {processing_time:.3f}s")
            
            return result
            
        except Exception as e:
            self.error_count += 1
            processing_time = time.time() - start_time
            error_msg = f"{self.agent_role.value} error: {str(e)}"
            
            self.logger.error(f"{error_msg}")
            
            return AgentOutput(
                success=False,
                content={},
                metadata={"error_type": type(e).__name__},
                processing_time=processing_time,
                agent_role=self.agent_role,
                error_message=error_msg
            )
    
    @abstractmethod
    async def process(self, agent_input: AgentInput) -> AgentOutput:
        """Process the agent input and return output"""
        pass
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get simple performance metrics"""
        avg_time = self.total_processing_time / max(self.execution_count, 1)
        return {
            "executions": self.execution_count,
            "total_time": self.total_processing_time,
            "average_time": avg_time,
            "error_count": self.error_count,
            "success_rate": (self.execution_count - self.error_count) / max(self.execution_count, 1)
        }
    
    def _is_server_side_error(self, error: Exception) -> bool:
        """Determine if an error is server-side and should be retried"""
        error_str = str(error).lower()
        
        # Rate limits and quota errors should NOT be retried - they're billing/quota issues
        rate_limit_errors = ["rate limit", "quota", "quota exceeded", "billing"]
        if any(err_type in error_str for err_type in rate_limit_errors):
            return False
            
        # Server errors that should be retried
        retryable_errors = [
            # Network and connection errors
            "connection", "timeout", "network", "socket", "dns",
            # Server errors
            "500", "502", "503", "504", "internal server error", "bad gateway", 
            "service unavailable", "gateway timeout", "server error",
            # Temporary server issues
            "overloaded", "temporarily unavailable", "service temporarily unavailable", 
            "try again later",
            # LLM provider specific server errors
            "model overloaded", "inference timeout", "model unavailable"
        ]
        
        # Check error message
        if any(err_type in error_str for err_type in retryable_errors):
            return True
            
        # Check specific exception types
        return isinstance(error, (
            ConnectionError, TimeoutError, OSError
        ))
    
    async def _retry_with_backoff(self, operation, max_retries: int = 3, base_delay: float = 1.0):
        """Retry an operation with exponential backoff for server-side errors"""
        last_error = None
        
        for attempt in range(max_retries):
            try:
                if asyncio.iscoroutinefunction(operation):
                    return await operation()
                else:
                    return operation()
            except Exception as e:
                last_error = e
                
                # Only retry for server-side errors
                if not self._is_server_side_error(e):
                    self.logger.warning(f"Non-retryable error in {self.agent_role.value}: {str(e)}")
                    raise e
                
                # Log retry attempt
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    self.logger.warning(
                        f"Server error in {self.agent_role.value} (attempt {attempt + 1}/{max_retries}): {str(e)}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(
                        f"All {max_retries} retry attempts failed for {self.agent_role.value}: {str(e)}"
                    )
        
        # If we get here, all retries failed
        raise last_error 