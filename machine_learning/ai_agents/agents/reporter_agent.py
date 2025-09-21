"""
Reporter Agent - LangChain Implementation

Synthesizes verified debate results into polished final answers.
"""

import time
import json
from typing import Dict, Any, List, AsyncGenerator
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from pydantic import BaseModel, Field

from ai_agents.state import WorkflowState, log_agent_execution
from ai_agents.utils import create_langchain_llm

# Import simple logger for backup logging
try:
    from ai_agents.simple_logger import simple_log
except:
    class SimpleLogFallback:
        def info(self, msg, data=None): pass
        def error(self, msg, data=None): pass
    simple_log = SimpleLogFallback()


class FinalAnswer(BaseModel):
    """Structured final answer"""
    introduction: str = Field(description="Brief introduction to the problem")
    step_by_step_solution: str = Field(description="Detailed solution with steps")
    key_takeaways: str = Field(description="Important points to remember")
    confidence_score: float = Field(description="Answer confidence 0-1")
    sources: List[str] = Field(description="Source references")


class ReporterAgent:
    """
    Report Writer using LangChain chains.
    
    Synthesizes debate results into:
    1. Polished, pedagogically valuable answers
    2. Clear structure and formatting
    3. Transparent handling of uncertainties
    """
    
    def __init__(self, context):
        self.context = context
        self.logger = context.logger.getChild("reporter")
        self.llm_client = context.llm_client
        self.llm = create_langchain_llm(self.llm_client)
        
        # Setup chains
        self._setup_chains()
    
    def _setup_chains(self):
        """Setup LangChain chains for answer synthesis"""
        
        # Main synthesis chain for converged results
        self.synthesis_chain = LLMChain(
            llm=self.llm,
            prompt=ChatPromptTemplate.from_messages([
                ("system", """You are an expert educator synthesizing verified solutions.
                Create clear, pedagogically valuable final answers.
                Write in a professional, educational tone."""),
                ("human", """Query: {query}

Verified Draft:
{draft}

Chain of Thought:
{cot}

Remaining Minor Issues (if any):
{minor_issues}

Debate Status: {status}
Quality Score: {quality_score}

Create a polished final answer with:
1. INTRODUCTION: Brief problem overview
2. STEP_BY_STEP_SOLUTION: Clear, detailed solution
3. KEY_TAKEAWAYS: Important concepts to remember
4. SOURCES: Relevant source citations

Ensure the answer is:
- Clearly structured
- Easy to understand
- Educationally valuable
- Accurate and complete

- Critical Instructions:
Your output should follow this format: Express your logic using mathematical language and logical symbols whenever possible, especially in mathematics and physics; (use abbreviations like s.t. frequently)
Provide concise explanations in natural English (note: use only English under all circumstances); however, do not place explanations within the same paragraph as equations.
Avoid unnecessarily complicating the problem. If you believe this question could be posed to a high school student or freshman, solve it using methods accessible to those students. For complex problems, use ample line breaks and expand your explanations.""")
            ])
        )
        
        # Chain for handling deadlock/escalation cases
        self.fallback_chain = LLMChain(
            llm=self.llm,
            prompt=ChatPromptTemplate.from_messages([
                ("system", """You are handling an incomplete or problematic solution.

CRITICAL INSTRUCTIONS:
1. Write actual, concrete content - NOT template placeholders
2. Do NOT use variables like {{query}}, {{reason}}, {{issues}}, {{draft}}
3. Use the actual query, reason, issues, and draft provided below
4. Be transparent about limitations while providing a real answer
5. Write in complete sentences without placeholder text

You must provide a real, readable answer."""),
                ("human", """Query: {query}

Best Available Draft:
{draft}

Unresolved Issues:
{issues}

Status: {status}
Reason: {reason}

IMPORTANT: Write a real answer using the actual information above. Do NOT use placeholder variables.

Create a transparent answer that:
1. Provides the verified portions of the solution based on the actual draft
2. Clearly indicates areas of uncertainty based on the actual issues
3. Explains what couldn't be fully resolved using the actual status and reason
4. Suggests how to get better answers

Format as:
INTRODUCTION: [Write actual context about the query and limitations]
PARTIAL_SOLUTION: [Write what you can actually provide from the draft]
UNRESOLVED_AREAS: [Write what actually remains uncertain from the issues]
RECOMMENDATIONS: [Write actual next steps for the user]

Remember: Use the actual content provided, not placeholder variables!""")
            ])
        )
        
        # Chain for quality indicators
        self.quality_assessment_chain = LLMChain(
            llm=self.llm,
            prompt=ChatPromptTemplate.from_messages([
                ("system", """Assess the quality indicators of the final answer."""),
                ("human", """Answer Content:
{answer}

Debate Metrics:
- Rounds: {rounds}
- Convergence Score: {convergence_score}
- Issues Resolved: {issues_resolved}

Provide quality indicators:
1. COMPLETENESS: [0-1 score]
2. CLARITY: [0-1 score]
3. ACCURACY: [0-1 score]
4. PEDAGOGICAL_VALUE: [0-1 score]""")
            ])
        )
    
    async def __call__(self, state: WorkflowState) -> WorkflowState:
        """Synthesize final answer from debate results"""
        start_time = time.time()
        
        try:
            self.logger.info("="*250)
            simple_log.info("="*250)
            self.logger.info("REPORTER AGENT - FINAL SYNTHESIS")
            simple_log.info("REPORTER AGENT - FINAL SYNTHESIS")
            self.logger.info("="*250)
            simple_log.info("="*250)
            
            query = state["query"]
            draft = state["draft"]
            critiques = state["critiques"]
            decision = state["moderator_decision"]
            convergence_score = state["convergence_score"]
            debate_rounds = state["current_round"]
            
            self.logger.info(f"Synthesizing answer:")
            simple_log.info(f"Synthesizing answer:")
            self.logger.info(f"  - Debate status: {decision}")
            simple_log.info(f"  - Debate status: {decision}")
            self.logger.info(f"  - Rounds: {debate_rounds}")
            simple_log.info(f"  - Rounds: {debate_rounds}")
            self.logger.info(f"  - Convergence: {convergence_score:.2f}")
            simple_log.info(f"  - Convergence: {convergence_score:.2f}")
            
            # Determine synthesis approach based on decision
            if decision == "converged":
                final_answer = await self._synthesize_converged(
                    query, draft, critiques, convergence_score
                )
            elif decision in ["abort_deadlock", "escalate_with_warning"]:
                final_answer = await self._synthesize_incomplete(
                    query, draft, critiques, decision, convergence_score
                )
            else:
                # Shouldn't reach here, but handle gracefully
                final_answer = await self._synthesize_incomplete(
                    query, draft, critiques, "unexpected_state", convergence_score
                )
            
            # Add quality indicators
            quality_indicators = await self._assess_quality(
                final_answer, debate_rounds, convergence_score, critiques
            )
            final_answer["quality_indicators"] = quality_indicators
            
            # Add source attributions
            sources = self._extract_sources(state["retrieval_results"])
            final_answer["sources"] = sources
            
            # Create formatted JSON output according to specification
            formatted_output = {
                "final_answer": {
                    "introduction": final_answer.get("introduction", ""),
                    "step_by_step_solution": final_answer.get("step_by_step_solution", ""),
                    "key_takeaways": final_answer.get("key_takeaways", ""),
                    "further_reading": sources[:3] if sources else []  # Top 3 sources
                },
                "confidence_score": final_answer.get("confidence_score", convergence_score),
                "sources": sources
            }
            
            # Log the JSON output
            self.logger.info("="*250)
            simple_log.info("="*250)
            self.logger.info("REPORTER OUTPUT (JSON)")
            simple_log.info("REPORTER OUTPUT (JSON)")
            self.logger.info("="*250)
            simple_log.info("="*250)
            self.logger.info(json.dumps(formatted_output, indent=2))
            simple_log.info(json.dumps(formatted_output, indent=2))
            self.logger.info("="*250)
            simple_log.info("="*250)
            
            # Update state
            state["final_answer"] = final_answer
            state["workflow_status"] = "synthesizing"
            
            # Log execution
            processing_time = time.time() - start_time
            log_agent_execution(
                state=state,
                agent_name="Reporter",
                input_summary=f"Status: {decision}, Draft: {draft['draft_id'] if draft else 'none'}",
                output_summary=f"Synthesized final answer with confidence {final_answer.get('confidence_score', 0):.2f}",
                processing_time=processing_time,
                success=True
            )
            
            self.logger.info(f"Synthesis completed:")
            simple_log.info(f"Synthesis completed:")
            self.logger.info(f"  - Answer type: {final_answer.get('type', 'standard')}")
            simple_log.info(f"  - Answer type: {final_answer.get('type', 'standard')}")
            self.logger.info(f"  - Confidence: {final_answer.get('confidence_score', 0):.2f}")
            simple_log.info(f"  - Confidence: {final_answer.get('confidence_score', 0):.2f}")
            self.logger.info(f"  - Sources: {len(final_answer.get('sources', []))}")
            simple_log.info(f"  - Sources: {len(final_answer.get('sources', []))}")
            
        except Exception as e:
            self.logger.error(f"Synthesis failed: {str(e)}")
            state["error_messages"].append(f"Reporter agent error: {str(e)}")
            state["workflow_status"] = "failed"
            
            # Provide fallback answer
            state["final_answer"] = {
                "introduction": "I apologize, but I encountered an error while preparing your answer.",
                "step_by_step_solution": f"Error details: {str(e)}",
                "key_takeaways": "Please try rephrasing your question or contact support.",
                "confidence_score": 0.0,
                "sources": []
            }
            
            log_agent_execution(
                state=state,
                agent_name="Reporter",
                input_summary=f"Synthesis attempt",
                output_summary=f"Error: {str(e)}",
                processing_time=time.time() - start_time,
                success=False
            )
        
        return state
    
    async def _synthesize_converged(
        self,
        query: str,
        draft: Dict,
        critiques: List[Dict],
        convergence_score: float
    ) -> Dict[str, Any]:
        """Synthesize answer for converged debate"""
        
        # Filter for only low-severity issues
        minor_issues = [c for c in critiques if c.get("severity") == "low"]
        minor_issues_str = self._format_issues(minor_issues) if minor_issues else "None"
        
        # Format CoT
        cot_str = self._format_cot(draft["chain_of_thought"])
        
        # Generate synthesis
        synthesis_inputs = {
            'query': query,
            'draft': draft["content"],
            'cot': cot_str,
            'minor_issues': minor_issues_str,
            'status': "converged",
            'quality_score': convergence_score
        }
        
        # Log the ACTUAL synthesis prompt
        try:
            prompt_value = self.synthesis_chain.prompt.format_prompt(**synthesis_inputs)
            messages = prompt_value.to_messages()
            self.logger.info(">>> ACTUAL REPORTER SYNTHESIS PROMPT <<<")
            simple_log.info(">>> ACTUAL REPORTER SYNTHESIS PROMPT <<<")
            self.logger.info("START_SYNTHESIS_PROMPT" + "="*229)
            simple_log.info("START_SYNTHESIS_PROMPT" + "="*229)
            for i, msg in enumerate(messages):
                self.logger.info(f"Message {i+1}: {msg.content}")
                simple_log.info(f"Message {i+1}: {msg.content}")
            self.logger.info("END_SYNTHESIS_PROMPT" + "="*231)
            simple_log.info("END_SYNTHESIS_PROMPT" + "="*231)
            self.logger.info(f"Total prompt length: {sum(len(msg.content) for msg in messages)} characters")
            simple_log.info(f"Total prompt length: {sum(len(msg.content) for msg in messages)} characters")
        except Exception as e:
            self.logger.error(f"Could not log synthesis prompt: {e}")
        
        # Use arun for proper variable substitution
        response = await self.synthesis_chain.arun(**synthesis_inputs)
        
        # Parse response into structured format
        answer = self._parse_synthesis(response)
        answer["type"] = "complete"
        answer["confidence_score"] = convergence_score
        
        return answer
    
    async def _synthesize_incomplete(
        self,
        query: str,
        draft: Dict,
        critiques: List[Dict],
        status: str,
        convergence_score: float
    ) -> Dict[str, Any]:
        """Synthesize answer for incomplete/problematic debate"""
        
        # Format unresolved issues
        unresolved = [c for c in critiques if c.get("severity") in ["critical", "high"]]
        issues_str = self._format_issues(unresolved)
        
        # Determine reason
        reason_map = {
            "abort_deadlock": "Could not resolve all issues within iteration limit",
            "escalate_with_warning": "Quality concerns require additional review",
            "unexpected_state": "Unexpected termination of debate process"
        }
        reason = reason_map.get(status, "Unknown termination reason")
        
        # Generate fallback synthesis
        fallback_inputs = {
            'query': query,
            'draft': draft["content"] if draft else "No draft available",
            'issues': issues_str,
            'status': status,
            'reason': reason
        }
        
        # Log the ACTUAL fallback prompt
        try:
            prompt_value = self.fallback_chain.prompt.format_prompt(**fallback_inputs)
            messages = prompt_value.to_messages()
            self.logger.info(">>> ACTUAL REPORTER FALLBACK PROMPT <<<")
            simple_log.info(">>> ACTUAL REPORTER FALLBACK PROMPT <<<")
            self.logger.info("START_FALLBACK_PROMPT" + "="*229)
            simple_log.info("START_FALLBACK_PROMPT" + "="*229)
            for i, msg in enumerate(messages):
                self.logger.info(f"Message {i+1}: {msg.content}")
                simple_log.info(f"Message {i+1}: {msg.content}")
            self.logger.info("END_FALLBACK_PROMPT" + "="*231)
            simple_log.info("END_FALLBACK_PROMPT" + "="*231)
        except Exception as e:
            self.logger.error(f"Could not log fallback prompt: {e}")
        
        # Use arun for proper substitution
        response = await self.fallback_chain.arun(**fallback_inputs)
        
        # Parse response
        answer = self._parse_fallback(response)
        answer["type"] = "partial"
        answer["confidence_score"] = min(convergence_score, 0.7)  # Cap confidence
        answer["warning"] = reason
        
        return answer
    
    async def _assess_quality(
        self,
        answer: Dict,
        rounds: int,
        convergence_score: float,
        critiques: List[Dict]
    ) -> Dict[str, float]:
        """Assess quality indicators of the final answer"""
        
        try:
            # Calculate issues resolved
            total_issues = len(critiques)
            resolved_issues = len([c for c in critiques if c.get("severity") == "low"])
            issues_resolved = f"{resolved_issues}/{total_issues}"
            
            # Get quality assessment
            quality_inputs = {
                'answer': str(answer),
                'rounds': rounds,
                'convergence_score': convergence_score,
                'issues_resolved': issues_resolved
            }
            
            # Log the ACTUAL quality assessment prompt
            try:
                prompt_value = self.quality_assessment_chain.prompt.format_prompt(**quality_inputs)
                messages = prompt_value.to_messages()
                self.logger.info(">>> ACTUAL QUALITY ASSESSMENT PROMPT <<<")
                simple_log.info(">>> ACTUAL QUALITY ASSESSMENT PROMPT <<<")
                self.logger.info("START_QUALITY_PROMPT" + "="*229)
                simple_log.info("START_QUALITY_PROMPT" + "="*229)
                for i, msg in enumerate(messages):
                    self.logger.info(f"Message {i+1}: {msg.content}")
                    simple_log.info(f"Message {i+1}: {msg.content}")
                self.logger.info("END_QUALITY_PROMPT" + "="*231)
                simple_log.info("END_QUALITY_PROMPT" + "="*231)
            except Exception as e:
                self.logger.error(f"Could not log quality prompt: {e}")
            
            # Use arun for proper substitution
            response = await self.quality_assessment_chain.arun(**quality_inputs)
            
            # Parse indicators
            indicators = {}
            for line in response.split("\n"):
                for metric in ["COMPLETENESS", "CLARITY", "ACCURACY", "PEDAGOGICAL_VALUE"]:
                    if metric in line:
                        try:
                            score = float(line.split(":")[-1].strip())
                            indicators[metric.lower()] = score
                        except:
                            pass
            
            # Ensure all metrics present
            for metric in ["completeness", "clarity", "accuracy", "pedagogical_value"]:
                if metric not in indicators:
                    indicators[metric] = 0.5  # Default
            
            return indicators
            
        except Exception as e:
            self.logger.error(f"Quality assessment failed: {e}")
            return {
                "completeness": convergence_score,
                "clarity": 0.7,
                "accuracy": convergence_score,
                "pedagogical_value": 0.7
            }
    
    def _parse_synthesis(self, response: str) -> Dict[str, Any]:
        """Parse structured synthesis response"""
        answer = {
            "introduction": "",
            "step_by_step_solution": "",
            "key_takeaways": "",
            "important_notes": ""
        }
        
        current_section = None
        current_content = []
        
        for line in response.split("\n"):
            # Check for section headers
            if line.startswith("INTRODUCTION:"):
                current_section = "introduction"
                current_content = [line.replace("INTRODUCTION:", "").strip()]
            elif line.startswith("STEP_BY_STEP_SOLUTION:"):
                if current_section and current_content:
                    answer[current_section] = "\n".join(current_content)
                current_section = "step_by_step_solution"
                current_content = [line.replace("STEP_BY_STEP_SOLUTION:", "").strip()]
            elif line.startswith("KEY_TAKEAWAYS:"):
                if current_section and current_content:
                    answer[current_section] = "\n".join(current_content)
                current_section = "key_takeaways"
                current_content = [line.replace("KEY_TAKEAWAYS:", "").strip()]
            elif line.startswith("SOURCES:"):
                if current_section and current_content:
                    answer[current_section] = "\n".join(current_content)
                current_section = None
            elif current_section:
                current_content.append(line)
        
        # Save last section
        if current_section and current_content:
            answer[current_section] = "\n".join(current_content)
        
        # Fallback if parsing fails
        if not answer["step_by_step_solution"]:
            answer["step_by_step_solution"] = response
        
        return answer
    
    def _parse_fallback(self, response: str) -> Dict[str, Any]:
        """Parse fallback synthesis response"""
        answer = {
            "introduction": "",
            "step_by_step_solution": "",
            "key_takeaways": "",
            "unresolved_areas": "",
            "recommendations": ""
        }
        
        # Similar parsing logic for fallback format
        sections = ["INTRODUCTION", "PARTIAL_SOLUTION", "UNRESOLVED_AREAS", "RECOMMENDATIONS"]
        current_section = None
        current_content = []
        
        for line in response.split("\n"):
            found_section = False
            for section in sections:
                if line.startswith(f"{section}:"):
                    if current_section and current_content:
                        key = current_section.lower().replace("partial_solution", "step_by_step_solution")
                        answer[key] = "\n".join(current_content)
                    current_section = section
                    current_content = [line.replace(f"{section}:", "").strip()]
                    found_section = True
                    break
            
            if not found_section and current_section:
                current_content.append(line)
        
        # Save last section
        if current_section and current_content:
            key = current_section.lower().replace("partial_solution", "step_by_step_solution")
            answer[key] = "\n".join(current_content)
        
        return answer
    
    def _format_issues(self, issues: List[Dict]) -> str:
        """Format issues for display"""
        if not issues:
            return "None"
        
        lines = []
        for issue in issues:  # All issues
            severity = issue.get("severity", "").upper()
            desc = issue.get("description", "")  # Keep full description - no truncation
            lines.append(f"- [{severity}] {desc}")
        
        # Remove arbitrary limit - show all issues
        
        return "\n".join(lines)
    
    def _format_cot(self, chain_of_thought: List[Dict]) -> str:
        """Format Chain of Thought"""
        if not chain_of_thought:
            return "Direct solution provided"
        
        lines = []
        for step in chain_of_thought:
            lines.append(f"Step {step['step']}: {step['thought']}")
        
        return "\n".join(lines)
    
    def _extract_sources(self, retrieval_results: List[Dict]) -> List[str]:
        """Extract unique sources from retrieval results"""
        sources = set()
        
        for result in retrieval_results[:10]:  # Top 10 results
            source = result.get("source", "")
            if source:
                sources.add(source)
        
        return list(sources)
    
    async def process_streaming(self, state: WorkflowState) -> Any:
        """
        Stream the final answer synthesis for Cerebras in Problem-Solving mode.
        
        This method streams the final reporter response directly to the frontend
        instead of collecting the full response first.
        """
        import asyncio
        from typing import AsyncGenerator
        
        try:
            # Extract debate results from state
            draft = state.get("draft", {})
            draft_content = draft.get("content", "")
            chain_of_thought = state.get("chain_of_thought", [])
            critiques = state.get("critiques", [])
            retrieval_results = state.get("retrieval_results", [])
            original_query = state.get("query", "")
            moderator_decision = state.get("moderator_decision", "approved")
            
            self.logger.info(f"Reporter streaming final answer for debate status: {moderator_decision}")
            simple_log.info(f"Reporter streaming final answer for debate status: {moderator_decision}")
            
            # Stream based on debate outcome
            if moderator_decision in ["approved", "conditionally_approved"]:
                async for chunk in self._stream_approved_answer(
                    original_query, draft_content, chain_of_thought, critiques, retrieval_results
                ):
                    yield chunk
            else:
                # For deadlock or other cases, use non-streaming synthesis
                # Call the main __call__ method to get the final answer
                result = await self.__call__(state)
                answer = result.get("final_answer", {})
                
                # Stream the pre-formatted response
                full_text = self._format_answer_for_streaming(answer)
                chunk_size = 20
                for i in range(0, len(full_text), chunk_size):
                    yield full_text[i:i+chunk_size]
                    await asyncio.sleep(0.01)
                    
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
    ) -> AsyncGenerator[str, None]:
        """Stream the synthesis of an approved answer"""
        import asyncio
        
        try:
            # Build prompt for streaming synthesis
            cot_summary = self._format_cot(chain_of_thought)
            minor_issues = self._format_issues(remaining_critiques)
            
            prompt = f"""
            You are a senior academic writer tasked with synthesizing verified debate results into a polished final answer.
            
            ORIGINAL QUERY:
            {query}
            
            VERIFIED DRAFT CONTENT:
            {draft_content}
            
            REASONING PROCESS:
            {cot_summary}
            
            MINOR REMAINING ISSUES TO ADDRESS:
            {minor_issues}
            
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
            - Use proper LaTeX syntax for math - inline: $f(x) = x^2$, display: $$f(x) = x^2$$
            - Create proper flow with logical transitions between concepts
            - Use academic writing style: clear, professional, and educational
            - Don't mention sources or documents - present information naturally
            - Integrate minor issues seamlessly without ignoring them
            - Maintain educational value and clear explanations
            
            Your output should follow this format: Express your logic using mathematical language and logical symbols whenever possible, especially in mathematics and physics; (use abbreviations like s.t. frequently)

            Provide concise explanations in natural English (note: use only English under all circumstances); however, do not place explanations within the same paragraph as equations.

            Avoid unnecessarily complicating the problem. If you believe this question could be posed to a high school student or freshman, solve it using methods accessible to those students. For complex problems, use ample line breaks and expand your explanations.
            """
            
            # Stream the LLM response directly using LangChain's streaming
            llm = create_langchain_llm(self.llm_client, temperature=0.3, streaming=True)
            
            # Use LangChain's async streaming
            async for chunk in llm.astream(prompt):
                if hasattr(chunk, 'content'):
                    yield chunk.content
                else:
                    yield str(chunk)
                
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

