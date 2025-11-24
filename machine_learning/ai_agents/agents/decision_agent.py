class MiniDecisionAgent:

    def __init__(self, llm_client):
        self.llm = llm_client

    async def evaluate_retrieval_quality(self, query, retrieval_results):
        """
        Evaluate if the retrieved results are sufficient to answer the query.

        Args:
            query: The user's question
            retrieval_results: List of retrieved documents with scores

        Returns:
            Dict with decision ('use_current' or 'expand_query'), reason, and confidence
        """
        # Validate we have results
        if not retrieval_results:
            return {
                "decision": "expand_query",
                "reason": "No results retrieved",
                "confidence": 1.0
            }

        # Build prompt with query and top 5 results (or fewer if less than 5 available)
        prompt = self.format_evaluation_prompt(
            query=query,
            results=retrieval_results[:5],
            scores=[r.score for r in retrieval_results[:5]]
        )

        # Ask LLM to evaluate the quality of the retrieved documents
        response = await self.llm.generate(prompt)

        # Parse LLM response to understand its decision
        decision = self.parse_decision(response)

        return {
            "decision": decision["action"],  # Action is either 'use_current' OR 'expand_query' exactly
            "reason": decision["reasoning"],
            "confidence": decision["confidence_score"]
        }

    def format_evaluation_prompt(self, query, results, scores):
        """Build the evaluation prompt with query and retrieved documents."""
        # Build the documents list dynamically
        docs_text = ""
        for i, (result, score) in enumerate(zip(results, scores), 1):
            content_preview = result.content[:200] if hasattr(result, 'content') else str(result)[:200]
            docs_text += f"        {i}. Score: {score:.3f} - {content_preview}\n"

        return f"""
Query: {query}

Top {len(results)} retrieved documents with similarity scores:
{docs_text}
Evaluate if these results are relevant to answer the query.

Respond in this format:
DECISION: [use_current OR expand_query]
====END====
REASON: [Brief explanation]
====END====
CONFIDENCE: [0.0-1.0]
====END====
"""
    
    @staticmethod
    def extract_field(text, field_name):
        """
        Extract a field value from text in the format 'FIELD_NAME: value\n====END===='.

        Args:
            text: String to search through (full LLM response)
            field_name: The field name to extract (e.g., "DECISION", "REASON", "CONFIDENCE")

        Returns:
            The value between the field name and ====END====, or empty string if not found
        """
        field_marker = f"{field_name}:"
        end_marker = "====END===="

        # Find where the field starts
        field_start = text.find(field_marker)
        if field_start == -1:
            return ""

        # Extract content after field marker
        content_start = field_start + len(field_marker)

        # Find the end marker after the field
        end_pos = text.find(end_marker, content_start)
        if end_pos == -1:
            # If no end marker, take everything until end of text
            return text[content_start:].strip()

        # Extract and return the value between field and end marker
        return text[content_start:end_pos].strip()

    def parse_decision(self, llm_response):
        """
        Parse the LLM response to extract decision, reason, and confidence.

        Args:
            llm_response: The raw LLM response text

        Returns:
            Dict with action, reasoning, and confidence_score
        """
        # Extract decision, reason, confidence from LLM response
        decision = self.extract_field(llm_response, "DECISION")
        reason = self.extract_field(llm_response, "REASON")

        # Try to parse confidence, default to 0.5 if parsing fails
        confidence_str = self.extract_field(llm_response, "CONFIDENCE")
        try:
            confidence = float(confidence_str)
            # Clamp confidence to [0.0, 1.0]
            confidence = max(0.0, min(1.0, confidence))
        except (ValueError, TypeError):
            confidence = 0.5

        return {
            "action": decision,
            "reasoning": reason,
            "confidence_score": confidence
        }



