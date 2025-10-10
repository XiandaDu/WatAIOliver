import re
import json
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ReasoningExtractor:
    """
    Extracts safe reasoning information from agent logs and formats for frontend.
    Maps internal agent activity to user-safe reasoning steps.
    """

    AGENT_DESCRIPTIONS = {
        'retrieve': 'Searching knowledge base for relevant information',
        'strategist': 'Analyzing problem and forming initial solution approach',
        'critic': 'Reviewing and critiquing the proposed solution',
        'moderator': 'Evaluating feedback and deciding next steps',
        'reporter': 'Synthesizing findings into comprehensive answer',
        'tutor': 'Adding educational context and guidance'
    }

    def __init__(self):
        self.current_agent = None
        self.step_counter = 0

    def extract_reasoning_from_chunk(self, chunk: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract reasoning information from agent system chunk.
        Returns sanitized reasoning metadata or None.
        """
        reasoning_data = {}

        # Detect agent transitions from chunk status
        if chunk.get('status') == 'in_progress':
            stage = chunk.get('stage', '')
            message = chunk.get('message', '')

            # Map stage to agent name
            agent = self._extract_agent_from_stage(stage)
            if agent and agent != self.current_agent:
                self.current_agent = agent
                reasoning_data['current_agent'] = agent

            # Create reasoning step
            if agent:
                self.step_counter += 1
                reasoning_data['agent'] = agent
                reasoning_data['step'] = {
                    'stage': stage,
                    'description': self.AGENT_DESCRIPTIONS.get(agent, 'Processing...'),
                    'summary': self._sanitize_message(message),
                    'timestamp': chunk.get('timestamp', ''),
                    'step_id': self.step_counter
                }

        return reasoning_data if reasoning_data else None

    def _extract_agent_from_stage(self, stage: str) -> Optional[str]:
        """Extract agent name from stage description."""
        stage_lower = stage.lower()

        if 'retrieve' in stage_lower or 'search' in stage_lower:
            return 'retrieve'
        elif 'strategist' in stage_lower or 'strategy' in stage_lower:
            return 'strategist'
        elif 'critic' in stage_lower or 'critique' in stage_lower:
            return 'critic'
        elif 'moderator' in stage_lower or 'moderate' in stage_lower:
            return 'moderator'
        elif 'reporter' in stage_lower or 'report' in stage_lower:
            return 'reporter'
        elif 'tutor' in stage_lower or 'tutorial' in stage_lower:
            return 'tutor'

        return None

    def _sanitize_message(self, message: str) -> str:
        """Sanitize message content for frontend display."""
        if not message:
            return ""

        # Remove sensitive patterns
        sanitized = re.sub(r'(api[_-]?key|token|password|secret)', '[REDACTED]', message, flags=re.IGNORECASE)

        # Truncate long messages
        if len(sanitized) > 100:
            sanitized = sanitized[:97] + "..."

        return sanitized

    def enhance_sse_chunk(self, original_chunk: Dict[str, Any]) -> str:
        """
        Enhance SSE chunk with reasoning metadata.
        Returns formatted SSE data string.
        """
        enhanced_chunk = original_chunk.copy()

        # Extract reasoning information
        reasoning = self.extract_reasoning_from_chunk(original_chunk)
        if reasoning:
            enhanced_chunk.update(reasoning)

        return f"data: {json.dumps(enhanced_chunk)}\n\n"

def create_reasoning_extractor() -> ReasoningExtractor:
    """Factory function to create reasoning extractor."""
    return ReasoningExtractor()