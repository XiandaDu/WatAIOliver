"""
Reporter Agent - LangChain Implementation

Synthesizes verified debate results into polished final answers.
"""

import time
import json
from typing import Dict, Any, List
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from pydantic import BaseModel, Field

from ai_agents.state import WorkflowState, log_agent_execution
from ai_agents.utils import create_langchain_llm


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
- Accurate and complete""")
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
            self.logger.info("REPORTER AGENT - FINAL SYNTHESIS")
            self.logger.info("="*250)
            
            query = state["query"]
            draft = state["draft"]
            critiques = state["critiques"]
            decision = state["moderator_decision"]
            convergence_score = state["convergence_score"]
            debate_rounds = state["current_round"]
            
            self.logger.info(f"Synthesizing answer:")
            self.logger.info(f"  - Debate status: {decision}")
            self.logger.info(f"  - Rounds: {debate_rounds}")
            self.logger.info(f"  - Convergence: {convergence_score:.2f}")
            
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
            self.logger.info("REPORTER OUTPUT (JSON)")
            self.logger.info("="*250)
            self.logger.info(json.dumps(formatted_output, indent=2))
            self.logger.info("="*250)
            
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
            self.logger.info(f"  - Answer type: {final_answer.get('type', 'standard')}")
            self.logger.info(f"  - Confidence: {final_answer.get('confidence_score', 0):.2f}")
            self.logger.info(f"  - Sources: {len(final_answer.get('sources', []))}")
            
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
            self.logger.info("START_SYNTHESIS_PROMPT" + "="*229)
            for i, msg in enumerate(messages):
                self.logger.info(f"Message {i+1}: {msg.content}")
            self.logger.info("END_SYNTHESIS_PROMPT" + "="*231)
            self.logger.info(f"Total prompt length: {sum(len(msg.content) for msg in messages)} characters")
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
            self.logger.info("START_FALLBACK_PROMPT" + "="*229)
            for i, msg in enumerate(messages):
                self.logger.info(f"Message {i+1}: {msg.content}")
            self.logger.info("END_FALLBACK_PROMPT" + "="*231)
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
                self.logger.info("START_QUALITY_PROMPT" + "="*229)
                for i, msg in enumerate(messages):
                    self.logger.info(f"Message {i+1}: {msg.content}")
                self.logger.info("END_QUALITY_PROMPT" + "="*231)
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
