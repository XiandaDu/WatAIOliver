import random
from typing import List, Tuple
from enum import Enum

class PromptVariant(Enum):
    DETAILED = "detailed"
    CONCISE = "concise"

class PromptGenerator:
    def generate_variants(self, base_query: str, context: str = "") -> Tuple[str, 
str]:
        """Generate two prompt variants for A/B testing"""

        variant_a = self._generate_detailed_prompt(base_query, context)
        variant_b = self._generate_concise_prompt(base_query, context)

        return variant_a, variant_b

    def _generate_detailed_prompt(self, query: str, context: str) -> str:
        return f"""
        Context: {context}
        
        Please provide a comprehensive and detailed response to the following 
question.
        Include relevant examples, explanations, and step-by-step guidance where 
appropriate.
        
        Question: {query}
        """

    def _generate_concise_prompt(self, query: str, context: str) -> str:
        return f"""
        Context: {context}
        
        Provide a clear, direct answer to this question. Be concise but complete.
        
        Question: {query}
        """