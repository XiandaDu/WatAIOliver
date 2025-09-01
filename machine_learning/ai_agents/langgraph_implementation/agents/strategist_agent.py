"""
Strategist Agent - LangChain Implementation

Generates draft solutions with Chain-of-Thought reasoning using LangChain.
"""

import time
import uuid
from typing import List, Dict, Any
from datetime import datetime
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from ..state import WorkflowState, DraftContent, ChainOfThought, log_agent_execution


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
        self.llm = context.llm_client
        
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
                Be creative and explore multiple approaches when relevant.
                
                {course_prompt}"""),
                HumanMessage(content="""Query: {query}

Context from retrieved documents:
{context}

Previous feedback (if any): {feedback}

Generate a detailed solution with explicit Chain-of-Thought reasoning.

{format_instructions}

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
                Address the specific issues while maintaining the good parts."""),
                HumanMessage(content="""Original Query: {query}

Previous Draft:
{previous_draft}

Feedback to address:
{feedback}

Context:
{context}

Generate an improved solution that addresses the feedback.

{format_instructions}""")
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
            
            # Prepare context string
            context_str = self._format_context(context)
            
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
                    format_instructions=self.output_parser.get_format_instructions()
                )
            else:
                self.logger.info("Generating initial draft solution")
                
                # Use main generation chain
                response = await self.draft_generation_chain.arun(
                    query=query,
                    context=context_str,
                    feedback=feedback or "No previous feedback",
                    course_prompt=course_prompt,
                    format_instructions=self.output_parser.get_format_instructions()
                )
            
            # Parse structured output
            try:
                parsed_output = self.output_parser.parse(response)
                draft_content = parsed_output.draft_content
                chain_of_thought = [
                    ChainOfThought(
                        step=step.step,
                        thought=step.thought,
                        confidence=step.confidence
                    )
                    for step in parsed_output.chain_of_thought
                ]
            except Exception as e:
                self.logger.warning(f"Failed to parse structured output: {e}")
                # Fallback to simple extraction
                draft_content = response
                chain_of_thought = self._extract_cot_fallback(response)
            
            # Create draft object
            draft = DraftContent(
                draft_id=f"draft_{uuid.uuid4().hex[:8]}",
                content=draft_content,
                chain_of_thought=chain_of_thought,
                timestamp=datetime.now().isoformat()
            )
            
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
            return "No context available."
        
        context_parts = []
        for i, result in enumerate(retrieval_results[:5], 1):
            context_parts.append(
                f"[Source {i}] (Relevance: {result.get('score', 0):.2f})\n"
                f"{result.get('content', '')}\n"
            )
        
        return "\n".join(context_parts)
    
    def _extract_cot_fallback(self, response: str) -> List[ChainOfThought]:
        """Fallback method to extract CoT from unstructured response"""
        cot_steps = []
        
        # Look for numbered steps or bullet points
        lines = response.split("\n")
        step_num = 1
        
        for line in lines:
            line = line.strip()
            if any([
                line.startswith(f"{step_num}."),
                line.startswith(f"Step {step_num}"),
                line.startswith("•"),
                line.startswith("-")
            ]):
                cot_steps.append(ChainOfThought(
                    step=step_num,
                    thought=line.lstrip("•-0123456789. Step:"),
                    confidence=0.7  # Default confidence
                ))
                step_num += 1
        
        # If no steps found, create one from the whole response
        if not cot_steps:
            cot_steps.append(ChainOfThought(
                step=1,
                thought="Complete solution provided",
                confidence=0.7
            ))
        
        return cot_steps
