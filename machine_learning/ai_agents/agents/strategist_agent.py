"""
Strategist Agent - Strategy Proposer

This agent generates well-structured, insightful initial draft solutions with detailed 
Chain-of-Thought (CoT) reasoning based on retrieved context.
"""

from typing import List, Dict, Any
from ai_agents.agents.base_agent import BaseAgent, AgentInput, AgentOutput, AgentRole


class StrategistAgent(BaseAgent):
    """
    Strategist Agent - Strategy Proposer
    
    Responsible for:
    1. Analyzing retrieved context and user query
    2. Generating step-by-step Chain-of-Thought (CoT)
    3. Producing an initial draft solution
    4. Encouraging divergent thinking and exploration
    """
    
    def __init__(self, config, llm_client=None, logger=None):
        super().__init__(AgentRole.STRATEGIST, config, llm_client, logger)
        
        # Strategist-specific prompts
        self.system_prompt = self._build_system_prompt()
        
    def _build_system_prompt(self) -> str:
        """Build the system prompt for the strategist"""
        return """
        You are an expert academic strategist and problem-solving assistant. Your role is to:

        1. ANALYZE the provided context and question thoroughly
        2. GENERATE a detailed Chain-of-Thought (CoT) breaking down your approach
        3. PRODUCE a comprehensive draft solution

        Key principles:
        - Think step-by-step and show your reasoning process
        - Use the provided context as your primary source of truth
        - Be creative and explore multiple solution paths when appropriate
        - Focus on educational value and clarity
        - Don't aim for perfection - this is a draft for further refinement
        - Take a moment to reflect deeply before responding

        Your output should be structured and detailed, suitable for critical review.
        """
    
    async def process(self, agent_input: AgentInput) -> AgentOutput:
        """
        Generate draft solution with Chain-of-Thought reasoning
        
        Args:
            agent_input: Contains query, retrieved context, and metadata
            
        Returns:
            AgentOutput: Draft solution with CoT and metadata
        """
        try:
            query = agent_input.query
            context = agent_input.context
            
            self.logger.info(f"Strategist analyzing query: '{query[:100]}...'")
            self.logger.info(f"Working with {len(context)} context items")
            
            # Build the complete prompt with context and course-specific guidance
            metadata = agent_input.metadata or {}
            strategist_prompt = self._build_strategist_prompt(query, context, metadata)
            
            # Generate the draft with CoT
            response = await self._generate_draft_solution(strategist_prompt)
            
            if not response:
                raise Exception("Failed to generate draft solution from LLM")
            
            # Parse the response into CoT and draft
            parsed_response = self._parse_llm_response(response)
            
            # Validate the output quality
            quality_score = self._assess_draft_quality(parsed_response, context)
            
            return AgentOutput(
                success=True,
                content={
                    "draft_id": f"draft_{agent_input.session_id[:8]}",
                    "draft_content": parsed_response["draft_content"],
                    "chain_of_thought": parsed_response["chain_of_thought"],
                    "quality_assessment": {
                        "score": quality_score,
                        "reasoning_steps": len(parsed_response["chain_of_thought"]),
                        "context_utilization": parsed_response["context_references"]
                    }
                },
                metadata={
                    "query": query,
                    "context_count": len(context),
                    "temperature_used": self.get_temperature(),
                    "strategy": "creative_exploration"
                },
                processing_time=0.0,  # Set by parent class
                agent_role=self.agent_role
            )
            
        except Exception as e:
            self.logger.error(f"Strategist failed: {str(e)}")
            raise e
    
    def _build_strategist_prompt(self, query: str, context: List[Dict[str, Any]], metadata: Dict[str, Any] = None) -> str:
        """Build comprehensive prompt with context and query"""
        
        # Format context information
        context_text = self._format_context_for_prompt(context)
        
        # Get course-specific prompt if available
        course_prompt = metadata.get('course_prompt') if metadata else None
        system_guidance = course_prompt or "You are a helpful educational assistant."
        
        # Check for previous feedback from Critic (for revision rounds)
        previous_feedback = metadata.get('previous_feedback') if metadata else None
        round_num = metadata.get('round', 1) if metadata else 1
        
        # Build revision instructions if this is a follow-up round
        revision_section = ""
        if previous_feedback and round_num > 1:
            revision_section = f"""
        
️  CRITICAL: REVISION ROUND {round_num}
        Your previous draft had issues that need correction. The Critic found:
        
        FEEDBACK FROM PREVIOUS ROUND:
        {previous_feedback}
        
REQUIRED ACTION: 
        You MUST address these specific issues in your new draft. Don't just repeat the same content - 
        actively fix the logical flaws, factual errors, and missing details identified above.
        """
        
        prompt = f"""
        {self.system_prompt}
        
        COURSE-SPECIFIC GUIDANCE:
        {system_guidance}
        {revision_section}
        
        CONTEXT INFORMATION:
        {context_text}
        
        USER QUERY:
        {query}
        
        Please provide your response in the following structured format:
        
        ## CHAIN OF THOUGHT
        
        Step 1: [Your first reasoning step]
        - [Detailed explanation of this step]
        - [Why this step is necessary]
        
        Step 2: [Your second reasoning step]
        - [Detailed explanation]
        - [Connection to previous step]
        
        [Continue with additional steps as needed]
        
        ## DRAFT SOLUTION
        
        [Your comprehensive draft answer to the query, incorporating insights from your Chain of Thought and the provided context]
        
        ## CONTEXT REFERENCES
        
        [List the specific context items you referenced and how they informed your solution]
        
        Remember: This is a draft meant for critical review. Focus on clear reasoning and thorough analysis rather than perfect polish.
        """
        
        return prompt
    
    def _format_context_for_prompt(self, context: List[Dict[str, Any]]) -> str:
        """Format retrieved context for inclusion in prompt"""
        if not context:
            return "No additional context provided."
        
        formatted_contexts = []
        
        for i, ctx_item in enumerate(context[:8]):  # Limit to prevent prompt overflow
            text = ctx_item.get('text', ctx_item.get('content', ''))
            score = ctx_item.get('score', 'N/A')
            source = ctx_item.get('source', {})
            
            formatted_context = f"""
=== CONTEXT SOURCE {i+1} (Relevance: {score}) ===
{text}
=== END CONTEXT SOURCE {i+1} ===
Source: {source}
            """
            
            formatted_contexts.append(formatted_context)
        
        return "\n".join(formatted_contexts)
    
    async def _generate_draft_solution(self, prompt: str) -> str:
        """Generate draft solution using LLM"""
        try:
            if not self.llm_client:
                raise Exception("No LLM client available")
            
            temperature = self.get_temperature()
            self.logger.info("=" * 250)
            self.logger.info("STRATEGIST LLM GENERATION")
            self.logger.info("=" * 250)
            self.logger.info(f"Temperature: {temperature}")
            self.logger.info("-" * 250)
            self.logger.info("PROMPT:")
            self.logger.info(prompt)
            self.logger.info("-" * 250)
            
            # Call LLM with creative temperature for exploration
            response = await self._call_llm(prompt, temperature)
            
            self.logger.info("LLM RESPONSE:")
            self.logger.info(response)
            self.logger.info("=" * 250)
            
            if len(response) < 100:  # Sanity check for reasonable response length
                raise Exception(f"Response too short ({len(response)} chars), likely generation failure")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Draft generation failed: {str(e)}")
            raise e
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured components"""
        
        result = {
            "draft_content": "",
            "chain_of_thought": [],
            "context_references": 0
        }
        
        self.logger.info("=" * 250)
        self.logger.info("STRATEGIST RESPONSE PARSING")
        self.logger.info("=" * 250)
        
        try:
            # Split response into sections
            sections = {}
            current_section = None
            current_content = []
            
            for line in response.split('\n'):
                line = line.strip()
                
                if line.startswith('## '):
                    # Save previous section
                    if current_section:
                        sections[current_section] = '\n'.join(current_content)
                    
                    # Start new section
                    current_section = line[3:].strip().lower()
                    current_content = []
                    
                elif current_section and line:
                    current_content.append(line)
            
            # Save last section
            if current_section:
                sections[current_section] = '\n'.join(current_content)
            
            self.logger.info(f"PARSED SECTIONS: {list(sections.keys())}")
            
            # Extract Chain of Thought
            cot_text = sections.get('chain of thought', '')
            self.logger.info("-" * 250)
            self.logger.info("CHAIN OF THOUGHT RAW TEXT:")
            self.logger.info(f"'{cot_text}'")
            self.logger.info("-" * 250)
            
            result["chain_of_thought"] = self._parse_chain_of_thought(cot_text)
            
            self.logger.info("PARSED COT STEPS:")
            for i, step in enumerate(result["chain_of_thought"]):
                self.logger.info(f"  Step {i+1}: {step}")
            self.logger.info("-" * 250)
            
            # Extract Draft Solution
            result["draft_content"] = sections.get('draft solution', response)  # Fallback to full response
            
            # Count context references
            context_refs = sections.get('context references', '')
            result["context_references"] = len([line for line in context_refs.split('\n') if 'context' in line.lower()])
            
        except Exception as e:
            self.logger.warning(f"️ Response parsing failed, using raw response: {str(e)}")
            
            # Fallback: use raw response as draft
            result["draft_content"] = response
            result["chain_of_thought"] = [{"step": 1, "thought": "Raw response provided due to parsing issues"}]
        
        self.logger.info("=" * 250)
        return result
    
    def _parse_chain_of_thought(self, cot_text: str) -> List[Dict[str, Any]]:
        """Parse Chain of Thought text into structured steps"""
        steps = []
        current_step = None
        step_number = 0
        
        for line in cot_text.split('\n'):
            line = line.strip()
            
            if line.startswith('Step '):
                # Save previous step
                if current_step:
                    steps.append(current_step)
                
                # Start new step
                step_number += 1
                step_text = line[line.find(':') + 1:].strip() if ':' in line else line[5:].strip()
                current_step = {
                    "step": step_number,
                    "thought": step_text,
                    "details": []
                }
                
            elif current_step and line.startswith('-'):
                # Add detail to current step
                detail = line[1:].strip()
                current_step["details"].append(detail)
            
            elif current_step and line and not line.startswith('Step'):
                # Add general content to current step
                current_step["thought"] += " " + line
        
        # Save last step
        if current_step:
            steps.append(current_step)
        
        # If no structured steps found, create a single step
        if not steps and cot_text.strip():
            steps.append({
                "step": 1,
                "thought": cot_text.strip(),
                "details": []
            })
        
        return steps
    
    def _assess_draft_quality(self, parsed_response: Dict[str, Any], context: List[Dict[str, Any]]) -> float:
        """Assess the quality of the generated draft"""
        
        score = 0.0
        max_score = 1.0
        
        # Check draft content length and substance
        draft_content = parsed_response.get("draft_content", "")
        if len(draft_content) > 200:
            score += 0.3
        elif len(draft_content) > 100:
            score += 0.15
        
        # Check Chain of Thought quality
        cot_steps = parsed_response.get("chain_of_thought", [])
        if len(cot_steps) >= 3:
            score += 0.3
        elif len(cot_steps) >= 2:
            score += 0.2
        elif len(cot_steps) >= 1:
            score += 0.1
        
        # Check context utilization
        context_refs = parsed_response.get("context_references", 0)
        if context_refs > 0 and context:
            context_utilization = min(context_refs / len(context), 1.0)
            score += 0.4 * context_utilization
        
        self.logger.debug(f"Draft quality assessment: {score:.3f}/{max_score}")
        
        return min(score / max_score, 1.0)
    
    async def _call_llm(self, prompt: str, temperature: float) -> str:
        """
        Call LLM with error handling, retry logic, and proper async interface support.
        
        Handles different LLM client types:
        - LangChain clients with ainvoke method (Cerebras, Gemini)
        - OpenAI client with generate_async method
        - Other clients with synchronous generate method
        
        Includes retry logic for server-side errors (up to 3 attempts).
        """
        async def _llm_operation():
            if hasattr(self.llm_client, 'get_llm_client'):
                llm = self.llm_client.get_llm_client()
                # Check if the underlying client has ainvoke (LangChain compatibility)
                if hasattr(llm, 'ainvoke'):
                    response = await llm.ainvoke(prompt, temperature=temperature)
                    return response.content if hasattr(response, 'content') else str(response)
                else:
                    # For raw clients (like OpenAI), use the wrapper's async method
                    if hasattr(self.llm_client, 'generate_async'):
                        response = await self.llm_client.generate_async(prompt, temperature=temperature)
                        return str(response)
                    else:
                        # Last resort: synchronous generate
                        response = self.llm_client.generate(prompt, temperature=temperature)
                        return str(response)
            else:
                # Direct client interface - check for async support first
                if hasattr(self.llm_client, 'generate_async'):
                    response = await self.llm_client.generate_async(prompt, temperature=temperature)
                    return str(response)
                else:
                    # Fallback to synchronous generate (should not be called with await, but handle gracefully)
                    response = self.llm_client.generate(prompt, temperature=temperature)
                    return str(response)
        
        try:
            # Use retry mechanism for server-side errors
            return await self._retry_with_backoff(_llm_operation, max_retries=3, base_delay=1.0)
        except Exception as e:
            self.logger.error(f"LLM call failed in strategist agent after all retries: {str(e)}")
            raise e 