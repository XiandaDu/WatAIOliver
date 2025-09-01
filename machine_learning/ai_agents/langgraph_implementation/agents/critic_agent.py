"""
Critic Agent - LangChain Implementation

Critical verifier that performs ruthless, evidence-based review of drafts.
"""

import time
from typing import List, Dict, Any
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain.tools import Tool
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from ..state import WorkflowState, Critique, log_agent_execution


class CritiqueOutput(BaseModel):
    """Structured critique output"""
    critiques: List[Dict[str, Any]] = Field(description="List of identified issues")
    overall_assessment: str = Field(description="Overall quality assessment")
    severity_score: float = Field(description="Overall severity score 0-1")


class CriticAgent:
    """
    Critical Verifier using LangChain chains and tools.
    
    Performs three types of verification:
    1. Logical flow verification
    2. Factual accuracy checking
    3. Hallucination detection
    """
    
    def __init__(self, context):
        self.context = context
        self.logger = context.logger.getChild("critic")
        self.llm = context.llm_client
        
        # Setup verification chains
        self._setup_chains()
        
        # Create verification tools
        self._setup_tools()
    
    def _setup_chains(self):
        """Setup LangChain chains for different verification tasks"""
        
        # Logic verification chain
        self.logic_verification_chain = LLMChain(
            llm=self.llm,
            prompt=ChatPromptTemplate.from_messages([
                SystemMessage(content="""You are a logic verifier. 
                Examine the logical flow between steps in the solution.
                Identify logical leaps, contradictions, or inconsistent reasoning."""),
                HumanMessage(content="""Query: {query}

Solution Draft:
{draft}

Chain of Thought:
{cot}

Identify ALL logical issues. For each issue provide:
- Step reference (if applicable)
- Issue type: logic_flaw
- Severity: low/medium/high/critical
- Clear description

Format each issue as:
ISSUE: [step_ref] | [severity] | [description]""")
            ])
        )
        
        # Fact checking chain
        self.fact_checking_chain = LLMChain(
            llm=self.llm,
            prompt=ChatPromptTemplate.from_messages([
                SystemMessage(content="""You are a fact checker.
                Verify all claims, formulas, and statements against the provided context.
                Flag any unsupported or contradicted claims."""),
                HumanMessage(content="""Query: {query}

Solution Draft:
{draft}

Context from sources:
{context}

Check EVERY factual claim. For each issue provide:
- The specific claim
- Issue type: fact_contradiction
- Severity: low/medium/high/critical  
- Description with evidence

Format each issue as:
ISSUE: [claim] | [severity] | [description]""")
            ])
        )
        
        # Hallucination detection chain
        self.hallucination_chain = LLMChain(
            llm=self.llm,
            prompt=ChatPromptTemplate.from_messages([
                SystemMessage(content="""You are a hallucination detector.
                Identify any content that is completely unsupported by context or irrelevant to the query."""),
                HumanMessage(content="""Query: {query}

Solution Draft:
{draft}

Context:
{context}

Identify hallucinated or irrelevant content. For each issue:
- Issue type: hallucination
- Severity: low/medium/high/critical
- Description

Format each issue as:
ISSUE: hallucination | [severity] | [description]""")
            ])
        )
        
        # Overall assessment chain
        self.assessment_chain = LLMChain(
            llm=self.llm,
            prompt=ChatPromptTemplate.from_messages([
                SystemMessage(content="""Provide an overall assessment of the draft quality."""),
                HumanMessage(content="""Based on these critiques:
{critiques}

Provide:
1. Overall assessment (one sentence)
2. Severity score (0-1, where 1 is perfect)

Format:
ASSESSMENT: [text]
SCORE: [0.XX]""")
            ])
        )
    
    def _setup_tools(self):
        """Setup LangChain tools for verification tasks"""
        
        self.verification_tools = [
            Tool(
                name="verify_calculation",
                func=self._verify_calculation,
                description="Verify mathematical calculations"
            ),
            Tool(
                name="check_formula",
                func=self._check_formula,
                description="Check if a formula is correctly stated"
            ),
            Tool(
                name="verify_reference",
                func=self._verify_reference,
                description="Verify a reference or citation"
            )
        ]
    
    async def __call__(self, state: WorkflowState) -> WorkflowState:
        """Perform critical verification of the draft"""
        start_time = time.time()
        
        try:
            self.logger.info("="*250)
            self.logger.info(f"CRITIC AGENT - ROUND {state['current_round']}")
            self.logger.info("="*250)
            
            draft = state["draft"]
            query = state["query"]
            context = state["retrieval_results"]
            
            if not draft:
                raise ValueError("No draft to critique")
            
            self.logger.info(f"Critiquing draft: {draft['draft_id']}")
            
            # Prepare inputs
            draft_content = draft["content"]
            cot_str = self._format_cot(draft["chain_of_thought"])
            context_str = self._format_context(context)
            
            # Run parallel verification chains
            critiques = []
            
            # 1. Logic verification
            self.logger.info("Performing logic verification...")
            logic_response = await self.logic_verification_chain.arun(
                query=query,
                draft=draft_content,
                cot=cot_str
            )
            logic_issues = self._parse_issues(logic_response, "logic_flaw")
            critiques.extend(logic_issues)
            
            # 2. Fact checking
            self.logger.info("Performing fact checking...")
            fact_response = await self.fact_checking_chain.arun(
                query=query,
                draft=draft_content,
                context=context_str
            )
            fact_issues = self._parse_issues(fact_response, "fact_contradiction")
            critiques.extend(fact_issues)
            
            # 3. Hallucination detection
            self.logger.info("Performing hallucination detection...")
            hallucination_response = await self.hallucination_chain.arun(
                query=query,
                draft=draft_content,
                context=context_str
            )
            hallucination_issues = self._parse_issues(hallucination_response, "hallucination")
            critiques.extend(hallucination_issues)
            
            # Get overall assessment
            critiques_str = self._format_critiques(critiques)
            assessment_response = await self.assessment_chain.arun(
                critiques=critiques_str
            )
            
            overall_assessment, severity_score = self._parse_assessment(assessment_response)
            
            # Update state
            state["critiques"] = critiques
            state["workflow_status"] = "debating"
            
            # Log execution
            processing_time = time.time() - start_time
            log_agent_execution(
                state=state,
                agent_name="Critic",
                input_summary=f"Draft: {draft['draft_id']}, Round: {state['current_round']}",
                output_summary=f"Found {len(critiques)} issues, severity: {severity_score:.2f}",
                processing_time=processing_time,
                success=True
            )
            
            self.logger.info(f"Critique completed:")
            self.logger.info(f"  - Total issues: {len(critiques)}")
            self.logger.info(f"  - Overall assessment: {overall_assessment}")
            self.logger.info(f"  - Severity score: {severity_score:.2f}")
            
            # Log critical issues
            critical_issues = [c for c in critiques if c.get("severity") == "critical"]
            if critical_issues:
                self.logger.warning(f"  - CRITICAL issues: {len(critical_issues)}")
                for issue in critical_issues[:2]:
                    self.logger.warning(f"    • {issue['description'][:100]}...")
            
        except Exception as e:
            self.logger.error(f"Critique failed: {str(e)}")
            state["error_messages"].append(f"Critic agent error: {str(e)}")
            state["workflow_status"] = "failed"
            
            log_agent_execution(
                state=state,
                agent_name="Critic",
                input_summary=f"Draft critique attempt",
                output_summary=f"Error: {str(e)}",
                processing_time=time.time() - start_time,
                success=False
            )
        
        return state
    
    def _parse_issues(self, response: str, default_type: str) -> List[Critique]:
        """Parse issues from chain response"""
        critiques = []
        
        for line in response.split("\n"):
            if line.startswith("ISSUE:"):
                parts = line.replace("ISSUE:", "").split("|")
                if len(parts) >= 2:
                    # Parse components
                    severity = "medium"  # default
                    description = ""
                    step_ref = None
                    claim = None
                    
                    if len(parts) >= 3:
                        # Full format
                        ref_or_claim = parts[0].strip()
                        severity = parts[1].strip().lower()
                        description = parts[2].strip()
                        
                        # Determine if it's a step ref or claim
                        if ref_or_claim.isdigit():
                            step_ref = int(ref_or_claim)
                        elif default_type == "fact_contradiction":
                            claim = ref_or_claim
                    else:
                        # Partial format
                        description = " | ".join(parts).strip()
                    
                    # Validate severity
                    if severity not in ["low", "medium", "high", "critical"]:
                        severity = "medium"
                    
                    critiques.append(Critique(
                        type=default_type,
                        severity=severity,
                        description=description,
                        step_ref=step_ref,
                        claim=claim
                    ))
        
        return critiques
    
    def _parse_assessment(self, response: str) -> tuple:
        """Parse overall assessment from response"""
        assessment = "Draft requires revision"
        score = 0.5
        
        for line in response.split("\n"):
            if line.startswith("ASSESSMENT:"):
                assessment = line.replace("ASSESSMENT:", "").strip()
            elif line.startswith("SCORE:"):
                try:
                    score = float(line.replace("SCORE:", "").strip())
                except:
                    pass
        
        return assessment, score
    
    def _format_cot(self, chain_of_thought: List[Dict]) -> str:
        """Format Chain of Thought for critique"""
        if not chain_of_thought:
            return "No explicit chain of thought provided"
        
        lines = []
        for step in chain_of_thought:
            lines.append(f"Step {step['step']}: {step['thought']}")
        
        return "\n".join(lines)
    
    def _format_context(self, retrieval_results: List[Dict]) -> str:
        """Format context for fact checking"""
        if not retrieval_results:
            return "No context available"
        
        context_parts = []
        for i, result in enumerate(retrieval_results[:5], 1):
            context_parts.append(
                f"[Source {i}]: {result.get('content', '')[:500]}..."
            )
        
        return "\n\n".join(context_parts)
    
    def _format_critiques(self, critiques: List[Critique]) -> str:
        """Format critiques for assessment"""
        if not critiques:
            return "No issues found"
        
        lines = []
        for c in critiques:
            lines.append(f"- [{c['severity'].upper()}] {c['type']}: {c['description']}")
        
        return "\n".join(lines)
    
    # Tool implementations
    def _verify_calculation(self, calculation: str) -> str:
        """Verify a mathematical calculation"""
        try:
            # Simple eval for basic calculations (in production, use safer methods)
            result = eval(calculation)
            return f"Calculation verified: {calculation} = {result}"
        except:
            return f"Cannot verify calculation: {calculation}"
    
    def _check_formula(self, formula: str) -> str:
        """Check if a formula is correctly stated"""
        # In production, this would check against a formula database
        return f"Formula check: {formula} - needs manual verification"
    
    def _verify_reference(self, reference: str) -> str:
        """Verify a reference or citation"""
        # In production, this would check against source documents
        return f"Reference check: {reference} - needs context verification"
