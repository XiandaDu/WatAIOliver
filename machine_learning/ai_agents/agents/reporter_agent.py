"""
Reporter Agent - Report Writer

This agent synthesizes the final answer after debate convergence, creating
polished, refined, and pedagogically valuable responses.
"""

from typing import List, Dict, Any
from ai_agents.agents.base_agent import BaseAgent, AgentInput, AgentOutput, AgentRole


class ReporterAgent(BaseAgent):
    """
    Reporter Agent - Final Answer Synthesizer
    
    Responsible for:
    1. Synthesizing verified draft into final polished answer
    2. Handling both converged and deadlock scenarios
    3. Formatting answers for educational value
    4. Providing source attribution and citations
    """
    
    def __init__(self, config, llm_client=None, logger=None):
        super().__init__(AgentRole.REPORTER, config, llm_client, logger)
        
        # Reporter-specific prompts
        self.system_prompt = self._build_system_prompt()
        
    def _build_system_prompt(self) -> str:
        """Build the system prompt for the reporter"""
        return """
        You are an expert educational content writer and report synthesizer. Your role is to:

        1. SYNTHESIZE verified content into polished, final answers
        2. STRUCTURE responses for maximum educational value
        3. INTEGRATE remaining minor issues seamlessly
        4. ATTRIBUTE sources clearly and transparently
        5. MAINTAIN academic rigor while ensuring accessibility
        6. **CLEAN AND FIX** all retrieved content formatting issues

        Key principles:
        - Write in the tone of a seasoned, knowledgeable teacher
        - Organize content logically: introduction, steps, key takeaways
        - **Fix all document parsing artifacts**: broken sentences, missing punctuation, fragmented text
        - **Transform raw retrieval text** into coherent, well-structured explanations
        - **Ensure proper grammar and flow** - don't copy-paste raw retrieved content
        - **Present information naturally** - don't mention "Document 1", "sources", or "retrieved materials"
        - Be transparent about knowledge boundaries and limitations
        - Provide clear, actionable insights
        - Ensure content is suitable for educational contexts
        - Reflect carefully on the debate outcome before finalizing

        CRITICAL: The retrieved content may have formatting issues, incomplete sentences, broken mathematical expressions, or parsing errors. 
        Your job is to understand the meaning and rewrite it as clear, professional educational content that flows naturally without referencing sources.
        
        **SPECIAL ATTENTION TO MATH**: Fix incomplete formulas (e.g., "f(x) = x^" → "f(x) = x^n"), integrate scattered mathematical symbols, and ensure all equations are properly formatted and complete.

        Your output should be the definitive, high-quality answer to the user's question.
        """
    
    async def process(self, agent_input: AgentInput) -> AgentOutput:
        """
        Synthesize final answer from debate results
        
        Args:
            agent_input: Contains draft, critique results, and convergence status
            
        Returns:
            AgentOutput: Final polished answer ready for user
        """
        try:
            # Extract debate results
            draft_content = agent_input.metadata.get('draft_content', '')
            chain_of_thought = agent_input.metadata.get('chain_of_thought', [])
            final_draft_status = agent_input.metadata.get('final_draft_status', {})
            remaining_critiques = agent_input.metadata.get('remaining_critiques', [])
            context = agent_input.context
            original_query = agent_input.query
            
            debate_status = final_draft_status.get('status', 'approved')
            quality_score = final_draft_status.get('quality_score', 0.8)
            
            self.logger.info(f"Reporter synthesizing final answer...")
            self.logger.info(f"Debate status: {debate_status}, Quality: {quality_score:.3f}")
            
            # Generate final answer based on debate outcome
            if debate_status == "approved":
                final_answer = await self._synthesize_approved_answer(
                    original_query, draft_content, chain_of_thought, remaining_critiques, context
                )
            elif debate_status == "deadlock":
                final_answer = await self._synthesize_deadlock_answer(
                    original_query, draft_content, remaining_critiques, context
                )
            else:
                # Fallback for unexpected status
                final_answer = await self._synthesize_fallback_answer(
                    original_query, draft_content, context
                )
            
            # Enhance with metadata and sources
            enhanced_answer = self._enhance_with_metadata(
                final_answer, context, quality_score, debate_status
            )
            
            return AgentOutput(
                success=True,
                content={
                    "final_answer": enhanced_answer,
                    "synthesis_metadata": {
                        "debate_status": debate_status,
                        "quality_score": quality_score,
                        "remaining_issues": len(remaining_critiques or []),
                        "context_sources": len(context),
                        "answer_structure": {
                            "has_introduction": "introduction" in enhanced_answer,
                            "has_step_by_step": "step_by_step_solution" in enhanced_answer,
                            "has_takeaways": "key_takeaways" in enhanced_answer,
                            "has_sources": "sources" in enhanced_answer
                        }
                    }
                },
                metadata={
                    "original_query": original_query,
                    "synthesis_approach": debate_status,
                    "educational_format": True
                },
                processing_time=0.0,  # Set by parent class
                agent_role=self.agent_role
            )
            
        except Exception as e:
            self.logger.error(f"Reporter failed: {str(e)}")
            raise e
    
    async def _synthesize_approved_answer(
        self, 
        query: str, 
        draft_content: str, 
        chain_of_thought: List[Dict[str, Any]], 
        remaining_critiques: List[Dict[str, Any]], 
        context: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Synthesize final answer from approved draft"""
        
        try:
            # Build comprehensive synthesis prompt
            cot_summary = self._format_chain_of_thought_summary(chain_of_thought)
            minor_issues = self._format_minor_issues(remaining_critiques)
            context_summary = self._format_context_summary(context)
            
            prompt = f"""
            {self.system_prompt}
            
            ORIGINAL QUERY:
            {query}
            
            VERIFIED DRAFT CONTENT:
            {draft_content}
            
            REASONING PROCESS:
            {cot_summary}
            
            MINOR REMAINING ISSUES TO ADDRESS:
            {minor_issues}
            
            SUPPORTING CONTEXT:
            {context_summary}
            
            Please synthesize this into a final, polished answer using this structure:
            
            ## INTRODUCTION
            [Brief context-setting introduction that acknowledges the question and previews the approach]
            
            ## STEP-BY-STEP SOLUTION
            [Clear, logical progression through the solution, incorporating insights from the reasoning process]
            
            ## KEY TAKEAWAYS
            [Important concepts, principles, or insights that generalize beyond this specific question]
            
            ## IMPORTANT NOTES
            [Any limitations, assumptions, or areas requiring caution - address minor issues transparently]
            
            Requirements:
            - **CLEAN UP FORMATTING ISSUES**: Fix broken sentences, missing punctuation, fragmented text from document parsing
            - **FORMAT MATH FOR KATEX**: Use proper LaTeX syntax - inline math: $f(x) = x^2$, display math: $$f(x) = x^2$$
            - **FIX MATHEMATICAL EXPRESSIONS ONLY**: Complete broken formulas (e.g., "f(x) = x^" → "$f(x) = x^2$"), integrate scattered math symbols with $ delimiters
            - **NO LONE MATH SYMBOLS**: Never leave symbols like π on separate lines - integrate them into complete sentences or expressions
            - **COMPLETE ALL BROKEN FORMULAS**: Fix incomplete expressions and fragmented mathematical content
            - **FIX SENTENCE FRAGMENTS**: Combine broken text pieces into complete, flowing sentences, remove trailing "and" or incomplete endings
            - **SYNTHESIZE CONCISELY**: Transform raw retrieved content into coherent explanations without unnecessary expansion
            - **FIX DOCUMENT PARSING ARTIFACTS**: Remove formatting errors, incomplete sentences, and garbled text
            - **CREATE PROPER FLOW**: Ensure logical transitions between concepts and ideas
            - **USE ACADEMIC WRITING STYLE**: Clear, professional, and educational tone
            - **NO DOCUMENT REFERENCES**: Don't mention "Document 1", "according to sources", or "based on provided materials" - present information naturally
            - **KEEP ORIGINAL SCOPE**: Don't expand beyond the original content's scope unless necessary for clarity
            - Integrate minor issues seamlessly (don't ignore them, but address them naturally)
            - Maintain educational value and clear explanations
            - Use a confident but honest tone
            - Ensure accuracy and logical flow
            """
            
            response = await self._call_llm(prompt, temperature=0.3)
            
            if response:
                return self._parse_structured_answer(response)
            else:
                raise Exception("No response from LLM for answer synthesis")
                
        except Exception as e:
            self.logger.error(f"Approved answer synthesis failed: {str(e)}")
            # Fallback to basic structure
            return self._create_fallback_structure(draft_content, query)
    
    async def _synthesize_deadlock_answer(
        self, 
        query: str, 
        draft_content: str, 
        unresolved_critiques: List[Dict[str, Any]], 
        context: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Synthesize answer for deadlock situation with transparency"""
        
        try:
            unresolved_summary = self._format_unresolved_issues(unresolved_critiques)
            context_summary = self._format_context_summary(context)
            
            prompt = f"""
            {self.system_prompt}
            
            SITUATION: The debate process reached a deadlock without full convergence. You need to provide the best possible answer while being transparent about limitations.
            
            ORIGINAL QUERY:
            {query}
            
            BEST AVAILABLE DRAFT:
            {draft_content}
            
            UNRESOLVED ISSUES:
            {unresolved_summary}
            
            SUPPORTING CONTEXT:
            {context_summary}
            
            Please create a transparent, educational response using this structure:
            
            ## PARTIAL SOLUTION
            [Present the best available information and reasoning, clearly indicating confidence levels]
            
            ## AREAS OF UNCERTAINTY
            [Honestly discuss unresolved aspects, conflicting information, or gaps in knowledge]
            
            ## WHAT WE CAN CONCLUDE
            [Clearly state what can be confidently concluded from available information]
            
            ## RECOMMENDATIONS FOR FURTHER EXPLORATION
            [Suggest specific areas for additional research or verification]
            
            Requirements:
            - Be completely honest about limitations
            - Still provide maximum educational value
            - Maintain academic integrity
            - Guide user toward reliable sources for unclear areas
            """
            
            response = await self._call_llm(prompt, temperature=0.2)
            
            if response:
                return self._parse_structured_answer(response, deadlock_mode=True)
            else:
                raise Exception("No response from LLM for deadlock synthesis")
                
        except Exception as e:
            self.logger.error(f"Deadlock answer synthesis failed: {str(e)}")
            # Fallback with transparency message
            return {
                "partial_solution": draft_content or "Unable to provide complete solution due to unresolved issues.",
                "areas_of_uncertainty": "Multiple technical issues prevented full verification of this response.",
                "recommendations": "Please consult additional authoritative sources for verification."
            }
    
    async def _synthesize_fallback_answer(
        self, 
        query: str, 
        draft_content: str, 
        context: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Synthesize basic answer as fallback"""
        
        return {
            "introduction": f"In response to your query: {query}",
            "step_by_step_solution": draft_content or "Unable to generate complete solution.",
            "key_takeaways": "Additional analysis would be needed for complete insights.",
            "important_notes": "This response may require further verification."
        }
    
    def _format_chain_of_thought_summary(self, chain_of_thought: List[Dict[str, Any]]) -> str:
        """Format Chain of Thought for synthesis prompt"""
        
        if not chain_of_thought:
            return "No detailed reasoning process available."
        
        formatted_steps = []
        for step in chain_of_thought:
            step_num = step.get('step', 'N/A')
            thought = step.get('thought', '')
            details = step.get('details', [])
            
            formatted_step = f"Step {step_num}: {thought}"
            if details:
                formatted_step += f"\n  - {'; '.join(details[:3])}"  # Limit details
            
            formatted_steps.append(formatted_step)
        
        return "\n".join(formatted_steps)
    
    def _format_minor_issues(self, critiques: List[Dict[str, Any]]) -> str:
        """Format minor remaining issues for synthesis"""
        
        if not critiques:
            return "No minor issues to address."
        
        issue_descriptions = []
        for critique in critiques[:5]:  # Limit to most important
            severity = critique.get('severity', 'unknown')
            description = critique.get('description', 'No description')
            issue_type = critique.get('type', 'unknown')
            
            issue_descriptions.append(f"• ({severity}) {description}")
        
        return f"Minor issues to integrate naturally:\n" + "\n".join(issue_descriptions)
    
    def _format_unresolved_issues(self, critiques: List[Dict[str, Any]]) -> str:
        """Format unresolved issues for deadlock transparency"""
        
        if not critiques:
            return "No specific unresolved issues documented."
        
        # Group by severity for clear presentation
        by_severity = {}
        for critique in critiques:
            severity = critique.get('severity', 'medium')
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(critique.get('description', 'No description'))
        
        formatted_issues = []
        for severity in ['critical', 'high', 'medium', 'low']:
            if severity in by_severity:
                issues = by_severity[severity][:3]  # Limit per severity
                formatted_issues.append(f"{severity.upper()} ISSUES:")
                for issue in issues:
                    formatted_issues.append(f"• {issue}")
        
        return "\n".join(formatted_issues)
    
    def _format_context_summary(self, context: List[Dict[str, Any]]) -> str:
        """Format context sources for synthesis"""
        
        if not context:
            return "No additional context sources available."
        
        summaries = []
        for i, ctx_item in enumerate(context[:3]):  # Limit to top sources
            text = ctx_item.get('text', ctx_item.get('content', ''))
            score = ctx_item.get('score', 'N/A')
            source = ctx_item.get('source', {})
            
            summary = f"Source {i+1} (Relevance: {score}):\n{text[:300]}..."
            summaries.append(summary)
        
        return "\n\n".join(summaries)
    
    def _parse_structured_answer(self, response: str, deadlock_mode: bool = False) -> Dict[str, Any]:
        """Parse LLM response into structured answer format"""
        
        answer = {}
        
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
                    current_section = line[3:].strip().lower().replace(' ', '_')
                    current_content = []
                    
                elif current_section and line:
                    current_content.append(line)
            
            # Save last section
            if current_section:
                sections[current_section] = '\n'.join(current_content)
            
            # Map sections to answer structure
            if deadlock_mode:
                answer["partial_solution"] = sections.get('partial_solution', response)
                answer["areas_of_uncertainty"] = sections.get('areas_of_uncertainty', '')
                answer["what_we_can_conclude"] = sections.get('what_we_can_conclude', '')
                answer["recommendations_for_further_exploration"] = sections.get('recommendations_for_further_exploration', '')
            else:
                answer["introduction"] = sections.get('introduction', '')
                answer["step_by_step_solution"] = sections.get('step-by-step_solution', sections.get('step_by_step_solution', response))
                answer["key_takeaways"] = sections.get('key_takeaways', '')
                answer["important_notes"] = sections.get('important_notes', '')
            
        except Exception as e:
            self.logger.warning(f"️ Answer parsing failed, using raw response: {str(e)}")
            # Fallback to raw response
            if deadlock_mode:
                answer["partial_solution"] = response
            else:
                answer["step_by_step_solution"] = response
        
        return answer
    
    def _create_fallback_structure(self, content: str, query: str) -> Dict[str, Any]:
        """Create basic fallback structure"""
        return {
            "introduction": f"Addressing your question: {query}",
            "step_by_step_solution": content or "Unable to generate complete solution.",
            "key_takeaways": "This response was generated with limited verification.",
            "important_notes": "Please verify this information with additional sources."
        }
    
    def _enhance_with_metadata(
        self, 
        answer: Dict[str, Any], 
        context: List[Dict[str, Any]], 
        quality_score: float, 
        debate_status: str
    ) -> Dict[str, Any]:
        """Enhance answer with confidence score, sources, and metadata"""
        
        enhanced = answer.copy()
        
        # Add confidence score
        enhanced["confidence_score"] = quality_score
        
        # Add source attribution
        sources = []
        for ctx_item in context[:5]:  # Limit sources
            source_info = ctx_item.get('source', {})
            score = ctx_item.get('score', 'N/A')
            
            if isinstance(source_info, dict):
                # Extract meaningful source information
                source_id = source_info.get('document_id', source_info.get('course_id', 'Unknown'))
                sources.append(f"{source_id} (relevance: {score})")
            else:
                sources.append(str(source_info))
        
        enhanced["sources"] = sources
        
        # Add quality indicators
        enhanced["quality_indicators"] = {
            "debate_status": debate_status,
            "verification_level": "high" if quality_score > 0.8 else "medium" if quality_score > 0.5 else "limited",
            "context_support": "strong" if len(context) >= 3 else "moderate" if len(context) >= 1 else "limited"
        }
        
        return enhanced
    
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
                    content = response.content if hasattr(response, 'content') else str(response)
                    
                    # DEBUG: Log what the agents system generates
                    print("=== DEBUG AGENT SYSTEM OUTPUT (ainvoke) ===")
                    print("AGENT LLM RESPONSE:", repr(content[:1000]))  # First 1000 chars
                    print("==========================================")
                    
                    return content
                else:
                    # For raw clients (like OpenAI), use the wrapper's async method
                    if hasattr(self.llm_client, 'generate_async'):
                        response = await self.llm_client.generate_async(prompt, temperature=temperature)
                        content_str = str(response)
                        
                        # DEBUG: Log what the agents system generates
                        print("=== DEBUG AGENT SYSTEM OUTPUT (generate_async) ===")
                        print("AGENT LLM RESPONSE:", repr(content_str[:1000]))  # First 1000 chars
                        print("==================================================")
                        
                        return content_str
                    else:
                        # Last resort: synchronous generate
                        response = self.llm_client.generate(prompt, temperature=temperature)
                        return str(response)
            else:
                # Direct client interface - check for async support first
                if hasattr(self.llm_client, 'generate_async'):
                    response = await self.llm_client.generate_async(prompt, temperature=temperature)
                    content_str = str(response)
                    
                    # DEBUG: Log what the agents system generates
                    print("=== DEBUG AGENT SYSTEM OUTPUT (direct generate_async) ===")
                    print("AGENT LLM RESPONSE:", repr(content_str[:1000]))  # First 1000 chars
                    print("=========================================================")
                    
                    return content_str
                else:
                    # Fallback to synchronous generate (should not be called with await, but handle gracefully)
                    response = self.llm_client.generate(prompt, temperature=temperature)
                    return str(response)
        
        try:
            # Use retry mechanism for server-side errors
            return await self._retry_with_backoff(_llm_operation, max_retries=3, base_delay=1.0)
        except Exception as e:
            self.logger.error(f"LLM call failed after all retries: {str(e)}")
            return ""

    async def _call_llm_stream(self, prompt: str, temperature: float):
        """
        Call LLM with streaming support for all model types.
        
        Supports Cerebras, OpenAI GPT, and Gemini models with faster streaming.
        Includes retry logic for server-side errors.
        """
        import asyncio
        
        async def _stream_operation():
            if hasattr(self.llm_client, 'generate_stream'):
                print("=== STARTING CEREBRAS STREAMING ===")
                chunk_count = 0
                
                # All clients now support temperature parameter in generate_stream
                async for chunk in self.llm_client.generate_stream(prompt, temperature=temperature):
                    if chunk:
                        chunk_count += 1
                        yield chunk
                        # Reduced delay for faster streaming - only yield control periodically
                        if chunk_count % 3 == 0:  # Every 3rd chunk
                            await asyncio.sleep(0.01)  # 10ms delay (reduced from 50ms)
                print("=== CEREBRAS STREAMING COMPLETE ===")
            else:
                # Fallback to non-streaming if streaming not available
                response = await self._call_llm(prompt, temperature)
                # Simulate streaming by chunking the response with faster delivery
                chunk_size = 15  # Smaller chunks for smoother appearance
                for i in range(0, len(response), chunk_size):
                    yield response[i:i+chunk_size]
                    # Faster simulated streaming
                    await asyncio.sleep(0.02)  # 20ms delay per chunk
        
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            try:
                async for chunk in _stream_operation():
                    yield chunk
                return  # Success, exit retry loop
            except Exception as e:
                retry_count += 1
                
                # Only retry for server-side errors
                if not self._is_server_side_error(e):
                    self.logger.error(f"Non-retryable streaming error: {str(e)}")
                    yield f"Error: {str(e)}"
                    return
                
                if retry_count < max_retries:
                    delay = 1.0 * (2 ** (retry_count - 1))  # Exponential backoff
                    self.logger.warning(
                        f"Streaming error (attempt {retry_count}/{max_retries}): {str(e)}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    yield f"[Connection error, retrying in {delay:.0f}s...]\n"
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(f"All {max_retries} streaming retry attempts failed: {str(e)}")
                    yield f"Error after {max_retries} attempts: {str(e)}"

    async def process_streaming(self, agent_input: AgentInput):
        """
        Stream the final answer synthesis for Cerebras in Problem-Solving mode.
        
        This method streams the final reporter response directly to the frontend
        instead of collecting the full response first.
        """
        try:
            # Extract debate results (same as non-streaming version)
            draft_content = agent_input.metadata.get('draft_content', '')
            chain_of_thought = agent_input.metadata.get('chain_of_thought', [])
            final_draft_status = agent_input.metadata.get('final_draft_status', {})
            remaining_critiques = agent_input.metadata.get('remaining_critiques', [])
            context = agent_input.context
            original_query = agent_input.query
            
            debate_status = final_draft_status.get('status', 'approved')
            
            self.logger.info(f"Reporter streaming final answer for debate status: {debate_status}")
            
            # Stream based on debate outcome
            if debate_status == "approved":
                async for chunk in self._stream_approved_answer(
                    original_query, draft_content, chain_of_thought, remaining_critiques, context
                ):
                    yield chunk
            else:
                # For deadlock or other cases, fall back to non-streaming for now
                result = await self.process(agent_input)
                answer = result.content.get('final_answer', {})
                
                # Stream the pre-formatted response
                full_text = self._format_answer_for_streaming(answer)
                chunk_size = 20
                for i in range(0, len(full_text), chunk_size):
                    yield full_text[i:i+chunk_size]
                    
        except Exception as e:
            self.logger.error(f"Streaming reporter failed: {str(e)}")
            yield f"Error generating response: {str(e)}"

    async def _stream_approved_answer(
        self, 
        query: str, 
        draft_content: str, 
        chain_of_thought: List[Dict[str, Any]], 
        remaining_critiques: List[Dict[str, Any]], 
        context: List[Dict[str, Any]]
    ):
        """Stream the synthesis of an approved answer"""
        try:
            # Build the same prompt as non-streaming version
            cot_summary = self._format_chain_of_thought_summary(chain_of_thought)
            minor_issues = self._format_minor_issues(remaining_critiques)
            context_summary = self._format_context_summary(context)
            
            prompt = f"""
            {self.system_prompt}
            
            ORIGINAL QUERY:
            {query}
            
            VERIFIED DRAFT CONTENT:
            {draft_content}
            
            REASONING PROCESS:
            {cot_summary}
            
            MINOR REMAINING ISSUES TO ADDRESS:
            {minor_issues}
            
            SUPPORTING CONTEXT:
            {context_summary}
            
            Please synthesize this into a final, polished answer using this structure:
            
            ## INTRODUCTION
            [Brief context-setting introduction that acknowledges the question and previews the approach]
            
            ## STEP-BY-STEP SOLUTION
            [Clear, logical progression through the solution, incorporating insights from the reasoning process]
            
            ## KEY TAKEAWAYS
            [Important concepts, principles, or insights that generalize beyond this specific question]
            
            ## IMPORTANT NOTES
            [Any limitations, assumptions, or areas requiring caution - address minor issues transparently]
            
            Requirements:
            - **CLEAN UP FORMATTING ISSUES**: Fix broken sentences, missing punctuation, fragmented text from document parsing
            - **FORMAT MATH FOR KATEX**: Use proper LaTeX syntax - inline math: $f(x) = x^2$, display math: $$f(x) = x^2$$
            - **FIX MATHEMATICAL EXPRESSIONS ONLY**: Complete broken formulas (e.g., "f(x) = x^" → "$f(x) = x^2$"), integrate scattered math symbols with $ delimiters
            - **NO LONE MATH SYMBOLS**: Never leave symbols like π on separate lines - integrate them into complete sentences or expressions
            - **COMPLETE ALL BROKEN FORMULAS**: Fix incomplete expressions and fragmented mathematical content
            - **FIX SENTENCE FRAGMENTS**: Combine broken text pieces into complete, flowing sentences, remove trailing "and" or incomplete endings
            - **SYNTHESIZE CONCISELY**: Transform raw retrieved content into coherent explanations without unnecessary expansion
            - **FIX DOCUMENT PARSING ARTIFACTS**: Remove formatting errors, incomplete sentences, and garbled text
            - **CREATE PROPER FLOW**: Ensure logical transitions between concepts and ideas
            - **USE ACADEMIC WRITING STYLE**: Clear, professional, and educational tone
            - **NO DOCUMENT REFERENCES**: Don't mention "Document 1", "according to sources", or "based on provided materials" - present information naturally
            - **KEEP ORIGINAL SCOPE**: Don't expand beyond the original content's scope unless necessary for clarity
            - Integrate minor issues seamlessly (don't ignore them, but address them naturally)
            - Maintain educational value and clear explanations
            - Use a confident but honest tone
            - Ensure accuracy and logical flow
            """
            
            # Stream the LLM response directly
            async for chunk in self._call_llm_stream(prompt, temperature=0.3):
                yield chunk
                
        except Exception as e:
            self.logger.error(f"Streaming approved answer failed: {str(e)}")
            yield f"Error: {str(e)}"

    def _format_answer_for_streaming(self, answer: Dict[str, Any]) -> str:
        """Format a structured answer into a single text for streaming"""
        parts = []
        
        if answer.get('introduction'):
            parts.append(f"## Introduction\n{answer['introduction']}\n")
        
        if answer.get('step_by_step_solution'):
            parts.append(f"## Step-by-Step Solution\n{answer['step_by_step_solution']}\n")
        
        if answer.get('key_takeaways'):
            parts.append(f"## Key Takeaways\n{answer['key_takeaways']}\n")
        
        if answer.get('important_notes'):
            parts.append(f"## Important Notes\n{answer['important_notes']}\n")
        
        return "\n".join(parts)