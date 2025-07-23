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

        Key principles:
        - Write in the tone of a seasoned, knowledgeable teacher
        - Organize content logically: introduction, steps, key takeaways
        - Be transparent about knowledge boundaries and limitations
        - Provide clear, actionable insights
        - Ensure content is suitable for educational contexts

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
        """Call LLM with error handling"""
        try:
            if hasattr(self.llm_client, 'get_llm_client'):
                llm = self.llm_client.get_llm_client()
                response = await llm.ainvoke(prompt, temperature=temperature)
                return response.content if hasattr(response, 'content') else str(response)
            else:
                # Fallback for different LLM client interfaces
                response = await self.llm_client.generate(prompt, temperature=temperature)
                return str(response)
        except Exception as e:
            self.logger.error(f"LLM call failed: {str(e)}")
            return "" 