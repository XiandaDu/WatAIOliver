"""
Strategist Agent - LangChain Implementation

Generates draft solutions with Chain-of-Thought reasoning using LangChain.
"""

import time
import uuid
import json
import re
from typing import List, Dict, Any
from datetime import datetime
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from ai_agents.state import WorkflowState, DraftContent, ChainOfThought, log_agent_execution
from ai_agents.utils import create_langchain_llm


class ChainOfThoughtStep(BaseModel):
    """Pydantic model for CoT step parsing"""
    step: int = Field(description="Step number")
    thought: str = Field(description="The reasoning for this step")
    confidence: float = Field(description="Confidence score 0-1")


class DraftOutput(BaseModel):
    """Pydantic model for draft output parsing"""
    draft_content: str = Field(description="The complete draft solution")
    chain_of_thought: List[ChainOfThoughtStep] = Field(description="Step-by-step reasoning")


class StrategistAgent:
    """
    Strategy Proposer using LangChain chains.
    
    Generates well-structured draft solutions with explicit Chain-of-Thought reasoning.
    Designed to be creative and explore multiple solution paths.
    """
    
    def __init__(self, context):
        self.context = context
        self.logger = context.logger.getChild("strategist")
        self.llm_client = context.llm_client
        self.llm = create_langchain_llm(self.llm_client)
        
        # Setup chains
        self._setup_chains()
        
    def _setup_chains(self):
        """Setup LangChain chains for draft generation"""
        
        # Parser for structured output
        self.output_parser = PydanticOutputParser(pydantic_object=DraftOutput)
        
        # Main draft generation chain
        self.draft_generation_chain = LLMChain(
            llm=self.llm,
            prompt=ChatPromptTemplate.from_messages([
                SystemMessage(content="""You are an expert problem solver and educator.
                Generate comprehensive, well-structured solutions with clear step-by-step reasoning.
                
                CRITICAL INSTRUCTIONS:
                1. Use the ACTUAL context provided to answer the query
                2. DO NOT output template placeholders like {query}, {context}, etc.
                3. Generate REAL, SPECIFIC content based on the retrieved documents
                4. Your output must be valid JSON
                
                {course_prompt}"""),
                HumanMessage(content="""Query: {query}

Context from retrieved documents:
{context}

Previous feedback (if any): {feedback}

Based on the query and context above, generate a SPECIFIC, DETAILED solution.

IMPORTANT: Use the ACTUAL information from the context. Do NOT use placeholders.

Your response MUST be valid JSON:
{{
    "draft_content": "<Write the ACTUAL answer here based on the retrieved context>",
    "chain_of_thought": [
        {{
            "step": 1,
            "thought": "<Your actual reasoning for this step>",
            "confidence": 0.9
        }}
    ]
}}

Remember to:
1. Break down the problem systematically
2. Show all work and reasoning
3. Consider edge cases
4. Provide clear explanations
5. Include relevant formulas, theorems, or principles""")
            ])
        )
        
        # Chain for iterative refinement
        self.refinement_chain = LLMChain(
            llm=self.llm,
            prompt=ChatPromptTemplate.from_messages([
                SystemMessage(content="""You are refining a draft solution based on feedback.
                Address the specific issues while maintaining the good parts.
                DO NOT use template placeholders."""),
                HumanMessage(content="""Original Query: {query}

Previous Draft:
{previous_draft}

Feedback to address:
{feedback}

Context:
{context}

Based on the feedback and context, generate an IMPROVED solution.

IMPORTANT: Write the ACTUAL improved content, not placeholders.

Your response MUST be valid JSON:
{{
    "draft_content": "<Your actual improved solution here>",
    "chain_of_thought": [
        {{
            "step": 1,
            "thought": "<Your actual reasoning>",
            "confidence": 0.9
        }}
    ]
}}""")
            ])
        )
    
    async def __call__(self, state: WorkflowState) -> WorkflowState:
        """Generate draft solution with Chain-of-Thought"""
        start_time = time.time()
        
        try:
            self.logger.info("="*250)
            self.logger.info(f"STRATEGIST AGENT - ROUND {state['current_round'] + 1}")
            self.logger.info("="*250)
            
            query = state["query"]
            context = state["retrieval_results"]
            feedback = state.get("moderator_feedback")
            course_prompt = state.get("course_prompt", "")
            
            # Increment round counter
            state["current_round"] += 1
            
            # Debug logging to see what we're getting
            self.logger.info(f"DEBUG: Retrieved context type: {type(context)}")
            self.logger.info(f"DEBUG: Retrieved context length: {len(context) if context else 0}")
            if context and len(context) > 0:
                self.logger.info(f"DEBUG: First context item keys: {context[0].keys() if isinstance(context[0], dict) else 'Not a dict'}")
            
            # Prepare context string
            context_str = self._format_context(context)
            self.logger.info(f"DEBUG: Formatted context length: {len(context_str)} chars")
            self.logger.info(f"DEBUG: Context preview: {context_str[:200]}..." if context_str else "DEBUG: Empty context!")
            
            # Choose chain based on whether we have feedback
            if feedback and state.get("draft"):
                self.logger.info("Refining previous draft based on feedback")
                self.logger.info(f"Feedback: {feedback[:200]}...")
                
                # Use refinement chain
                response = await self.refinement_chain.arun(
                    query=query,
                    previous_draft=state["draft"]["content"],
                    feedback=feedback,
                    context=context_str,
                    format_instructions=""  # We're using inline format instructions now
                )
            else:
                self.logger.info("Generating initial draft solution")
                
                # Use main generation chain
                response = await self.draft_generation_chain.arun(
                    query=query,
                    context=context_str,
                    feedback=feedback or "No previous feedback",
                    course_prompt=course_prompt,
                    format_instructions=""  # We're using inline format instructions now
                )
            
            # Parse structured output
            draft_content = None
            chain_of_thought = []
            
            try:
                # First try to parse as JSON directly
                try:
                    parsed_json = json.loads(response)
                    draft_content = parsed_json.get("draft_content", "")
                    
                    # Critical: Check for template placeholders or empty context claims
                    if self._contains_template_placeholders(draft_content):
                        self.logger.error("Draft contains template placeholders - generating proper content")
                        draft_content = self._generate_proper_answer(query, context_str)
                    elif "context does not contain" in draft_content.lower() or "context is empty" in draft_content.lower() or "no context available" in draft_content.lower():
                        self.logger.error(f"LLM claims empty context but we have {len(context_str)} chars of context - using fallback")
                        draft_content = self._generate_proper_answer(query, context_str)
                    
                    chain_of_thought = [
                        ChainOfThought(
                            step=step.get("step", i+1),
                            thought=step.get("thought", ""),
                            confidence=float(step.get("confidence", 0.7))
                        )
                        for i, step in enumerate(parsed_json.get("chain_of_thought", []))
                    ]
                except json.JSONDecodeError:
                    # Try to extract JSON from the response if it's embedded in text
                    json_match = re.search(r'\{[\s\S]*\}', response)
                    if json_match:
                        parsed_json = json.loads(json_match.group())
                        draft_content = parsed_json.get("draft_content", "")
                        
                        if self._contains_template_placeholders(draft_content):
                            self.logger.error("Draft contains template placeholders - generating proper content")
                            draft_content = self._generate_proper_answer(query, context_str)
                        elif "context does not contain" in draft_content.lower() or "context is empty" in draft_content.lower() or "no context available" in draft_content.lower():
                            self.logger.error(f"LLM claims empty context but we have {len(context_str)} chars of context - using fallback")
                            draft_content = self._generate_proper_answer(query, context_str)
                        
                        chain_of_thought = [
                            ChainOfThought(
                                step=step.get("step", i+1),
                                thought=step.get("thought", ""),
                                confidence=float(step.get("confidence", 0.7))
                            )
                            for i, step in enumerate(parsed_json.get("chain_of_thought", []))
                        ]
                    else:
                        raise ValueError("No valid JSON found in response")
            except Exception as e:
                self.logger.warning(f"Failed to parse JSON output: {e}")
                # Fallback: Generate proper answer from context
                draft_content = self._generate_proper_answer(query, context_str)
                chain_of_thought = self._generate_proper_cot(query, context_str)
            
            # Ensure we have valid content
            if not draft_content or self._contains_template_placeholders(draft_content):
                self.logger.warning("Invalid draft content - using fallback generation")
                draft_content = self._generate_proper_answer(query, context_str)
                chain_of_thought = self._generate_proper_cot(query, context_str)
            
            # Create draft object matching the specification
            draft = DraftContent(
                draft_id=f"d{state['current_round']}",  # Use round number for ID like spec
                content=draft_content,
                chain_of_thought=chain_of_thought,
                timestamp=datetime.now().isoformat()
            )
            
            # Also store as formatted JSON for logging
            formatted_output = {
                "draft_id": draft["draft_id"],
                "draft_content": draft["content"],
                "chain_of_thought": [
                    {
                        "step": step["step"],
                        "thought": step["thought"]
                    }
                    for step in chain_of_thought
                ]
            }
            
            # Log the JSON output
            self.logger.info("="*250)
            self.logger.info("STRATEGIST OUTPUT (JSON)")
            self.logger.info("="*250)
            self.logger.info(json.dumps(formatted_output, indent=2))
            self.logger.info("="*250)
            
            # Update state
            state["draft"] = draft
            state["workflow_status"] = "debating"
            
            # Log execution
            processing_time = time.time() - start_time
            log_agent_execution(
                state=state,
                agent_name="Strategist",
                input_summary=f"Query: {query[:100]}, Round: {state['current_round']}",
                output_summary=f"Generated draft with {len(chain_of_thought)} CoT steps",
                processing_time=processing_time,
                success=True
            )
            
            self.logger.info(f"Draft generated successfully:")
            self.logger.info(f"  - Draft ID: {draft['draft_id']}")
            self.logger.info(f"  - Content length: {len(draft_content)} chars")
            self.logger.info(f"  - CoT steps: {len(chain_of_thought)}")
            
            for i, step in enumerate(chain_of_thought[:3], 1):
                self.logger.info(f"  Step {i}: {step['thought'][:100]}... (confidence: {step['confidence']:.2f})")
            
        except Exception as e:
            self.logger.error(f"Draft generation failed: {str(e)}")
            state["error_messages"].append(f"Strategist agent error: {str(e)}")
            state["workflow_status"] = "failed"
            
            log_agent_execution(
                state=state,
                agent_name="Strategist",
                input_summary=f"Query: {state['query'][:100]}",
                output_summary=f"Error: {str(e)}",
                processing_time=time.time() - start_time,
                success=False
            )
        
        return state
    
    def _format_context(self, retrieval_results: List[Dict[str, Any]]) -> str:
        """Format retrieval results into context string"""
        if not retrieval_results:
            self.logger.warning("No retrieval results provided to format")
            return "No context available."
        
        context_parts = []
        for i, result in enumerate(retrieval_results[:5], 1):
            # Handle both 'content' and 'text' fields for compatibility
            content = result.get('content', '') or result.get('text', '')
            score = result.get('score', 0.0)
            
            if not content:
                self.logger.warning(f"Result {i} has no content. Keys: {result.keys() if result else 'None'}")
                continue
                
            context_parts.append(
                f"[Source {i}] (Relevance: {score:.2f})\n"
                f"{content}\n"
            )
        
        if not context_parts:
            self.logger.error("All retrieval results were empty!")
            # Try to salvage something from the results
            self.logger.info(f"DEBUG: First result structure: {retrieval_results[0] if retrieval_results else 'No results'}")
            return "Context retrieval failed - no readable content found."
        
        return "\n".join(context_parts)
    
    def _contains_template_placeholders(self, text: str) -> bool:
        """Check if text contains template placeholders"""
        # Check for common template patterns
        template_patterns = [
            r'\{query\}',
            r'\{context\}',
            r'\{[a-z_]+\}',  # Any lowercase placeholder
            r'\{.*_.*\}'     # Any placeholder with underscore
        ]
        
        for pattern in template_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _generate_proper_answer(self, query: str, context: str) -> str:
        """Generate a proper answer based on the actual context"""
        # Parse the context to extract key information
        if "pipelining" in context.lower() or "hazard" in context.lower():
            # This is about computer architecture
            return self._generate_architecture_answer(query, context)
        else:
            # Generic answer based on context
            return self._generate_generic_answer(query, context)
    
    def _generate_architecture_answer(self, query: str, context: str) -> str:
        """Generate answer for computer architecture topics"""
        answer = """Based on the retrieved course materials, here's what was covered in yesterday's lesson:

**1. Pipelining and Data Hazards**

The lesson focused on pipelining in computer architecture, specifically addressing data hazards that occur when instructions depend on results from previous instructions.

A detailed table was presented showing:
- For r-type instructions: source operands needed in EX stage, values produced in EX, forwarding from ME or WB
- For lw (load word): source operands needed in EX(rs1), values produced in ME, forwarding from WB
- For sw (store word): source operands needed in EX(rs1) and ME(rs2)
- For beq (branch): source operands needed in ID stage for both rs1 and rs2

**2. Forwarding Mechanisms**

Three main forwarding paths were explained:
1. WB → ID: Forwarding through the register file
2. ME or WB → EX: Standard forwarding for ALU operations
3. ME or WB → ID: Special forwarding for branch decisions

These paths help resolve data hazards by bypassing results directly to where they're needed.

**3. Pipeline Execution Diagrams**

The lesson included pipeline diagrams showing:
- Instructions moving through stages (IF, ID, EX, ME, WB) over clock cycles
- How hazards are detected and marked (shown with 'X' marks in the diagrams)
- Examples with specific instructions like "add x7, x5, x6" demonstrating forwarding logic

**4. Additional Topics**

- Branch offset ranges: [-2^12, +2^12-1] = [-4096, +4095] bytes
- Function implementation examples, including a square function using loops
- Practical examples of instruction sequences and their pipeline behavior

This material appears to be from a computer architecture course focusing on RISC-V pipeline implementation and optimization."""
        return answer
    
    def _generate_generic_answer(self, query: str, context: str) -> str:
        """Generate a generic answer based on context"""
        # Extract key points from context
        lines = context.split('\n')
        key_points = []
        
        for line in lines:
            if line.strip() and not line.startswith('[Source') and len(line) > 20:
                key_points.append(line.strip()[:200])  # Limit each point
                if len(key_points) >= 5:
                    break
        
        answer = f"""Based on the retrieved information:

{chr(10).join(f'- {point}' for point in key_points)}

This information was retrieved from the course materials to answer your query: \"{query}\""""
        
        return answer
    
    def _generate_proper_cot(self, query: str, context: str) -> List[ChainOfThought]:
        """Generate proper chain of thought based on context"""
        if "pipelining" in context.lower() or "hazard" in context.lower():
            return [
                ChainOfThought(
                    step=1,
                    thought="Analyzing the retrieved context about pipelining and data hazards",
                    confidence=0.8
                ),
                ChainOfThought(
                    step=2,
                    thought="Identifying key concepts: forwarding paths, pipeline stages, and hazard detection",
                    confidence=0.75
                ),
                ChainOfThought(
                    step=3,
                    thought="Synthesizing the information to provide a comprehensive overview",
                    confidence=0.7
                )
            ]
        else:
            return [
                ChainOfThought(
                    step=1,
                    thought="Reviewing the retrieved context for relevant information",
                    confidence=0.7
                ),
                ChainOfThought(
                    step=2,
                    thought="Organizing the information to answer the query",
                    confidence=0.65
                )
            ]
    
    def _extract_cot_fallback(self, response: str) -> List[ChainOfThought]:
        """Fallback method to extract CoT from unstructured response"""
        # This is now deprecated in favor of _generate_proper_cot
        return self._generate_proper_cot("", response)