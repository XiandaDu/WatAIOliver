"""
Moderator Agent - LangChain Implementation

Arbiter that controls the debate flow and makes convergence decisions.
"""

import time
from typing import List, Dict, Any
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from ..state import WorkflowState, log_agent_execution


class ModeratorDecision(BaseModel):
    """Structured moderator decision"""
    decision: str = Field(description="Decision: converged, iterate, abort_deadlock, or escalate_with_warning")
    reasoning: str = Field(description="Reasoning for the decision")
    feedback_to_strategist: str = Field(description="Specific feedback for next iteration if needed")
    convergence_score: float = Field(description="Convergence score 0-1")


class ModeratorAgent:
    """
    Debate Flow Controller using LangChain chains.
    
    Makes decisions on:
    1. Convergence - draft is good enough
    2. Iteration - needs improvement
    3. Deadlock - cannot converge
    4. Escalation - quality concerns
    """
    
    def __init__(self, context):
        self.context = context
        self.logger = context.logger.getChild("moderator")
        self.llm = context.llm_client
        
        # Decision thresholds
        self.convergence_threshold = 0.8
        self.critical_severity_threshold = 2  # Max critical issues allowed
        
        # Setup chains
        self._setup_chains()
    
    def _setup_chains(self):
        """Setup LangChain chains for moderation decisions"""
        
        # Main decision chain
        self.decision_chain = LLMChain(
            llm=self.llm,
            prompt=ChatPromptTemplate.from_messages([
                SystemMessage(content="""You are a debate moderator controlling the quality assurance process.
                Analyze critiques and make strategic decisions about the debate flow.
                
                Decision options:
                - converged: Draft is acceptable (minor or no issues)
                - iterate: Draft needs revision (fixable issues)
                - abort_deadlock: Cannot converge after max attempts
                - escalate_with_warning: Serious quality concerns"""),
                HumanMessage(content="""Query: {query}

Current Round: {current_round} / {max_rounds}

Draft Summary:
{draft_summary}

Critiques Found:
{critiques}

Critique Statistics:
- Critical issues: {critical_count}
- High severity: {high_count}
- Medium severity: {medium_count}
- Low severity: {low_count}

Previous Iterations: {has_previous}

Make a decision and provide:
1. DECISION: [converged/iterate/abort_deadlock/escalate_with_warning]
2. REASONING: [Your reasoning]
3. FEEDBACK: [Specific feedback for strategist if iterating]
4. CONVERGENCE_SCORE: [0.XX]""")
            ])
        )
        
        # Feedback generation chain
        self.feedback_chain = LLMChain(
            llm=self.llm,
            prompt=ChatPromptTemplate.from_messages([
                SystemMessage(content="""Generate concise, actionable feedback for draft revision."""),
                HumanMessage(content="""Critical issues to address:
{critical_issues}

High priority issues:
{high_issues}

Generate specific, prioritized feedback for the strategist.
Focus on the most important issues that must be fixed.

Format: Clear, numbered action items.""")
            ])
        )
    
    async def __call__(self, state: WorkflowState) -> WorkflowState:
        """Make moderation decision based on critiques"""
        start_time = time.time()
        
        try:
            self.logger.info("="*250)
            self.logger.info(f"MODERATOR AGENT - ROUND {state['current_round']}")
            self.logger.info("="*250)
            
            critiques = state["critiques"]
            current_round = state["current_round"]
            max_rounds = state["max_rounds"]
            draft = state["draft"]
            
            # Analyze critique severity
            severity_counts = self._analyze_severity(critiques)
            
            self.logger.info(f"Critique analysis:")
            self.logger.info(f"  - Critical: {severity_counts['critical']}")
            self.logger.info(f"  - High: {severity_counts['high']}")
            self.logger.info(f"  - Medium: {severity_counts['medium']}")
            self.logger.info(f"  - Low: {severity_counts['low']}")
            
            # Prepare decision inputs
            draft_summary = draft["content"][:500] if draft else "No draft"
            critiques_str = self._format_critiques(critiques)
            has_previous = "Yes" if state.get("moderator_feedback") else "No"
            
            # Make decision
            decision_response = await self.decision_chain.arun(
                query=state["query"],
                current_round=current_round,
                max_rounds=max_rounds,
                draft_summary=draft_summary,
                critiques=critiques_str,
                critical_count=severity_counts["critical"],
                high_count=severity_counts["high"],
                medium_count=severity_counts["medium"],
                low_count=severity_counts["low"],
                has_previous=has_previous
            )
            
            # Parse decision
            decision, reasoning, feedback, convergence_score = self._parse_decision(decision_response)
            
            # Apply decision rules
            decision = self._apply_decision_rules(
                decision, severity_counts, current_round, max_rounds
            )
            
            # Generate detailed feedback if iterating
            if decision == "iterate":
                detailed_feedback = await self._generate_detailed_feedback(critiques)
                feedback = detailed_feedback if detailed_feedback else feedback
            
            # Update state
            state["moderator_decision"] = decision
            state["moderator_feedback"] = feedback if decision == "iterate" else None
            state["convergence_score"] = convergence_score
            
            # Log execution
            processing_time = time.time() - start_time
            log_agent_execution(
                state=state,
                agent_name="Moderator",
                input_summary=f"Round {current_round}/{max_rounds}, {len(critiques)} critiques",
                output_summary=f"Decision: {decision}, Score: {convergence_score:.2f}",
                processing_time=processing_time,
                success=True
            )
            
            self.logger.info(f"Moderation decision:")
            self.logger.info(f"  - Decision: {decision}")
            self.logger.info(f"  - Reasoning: {reasoning[:200]}...")
            self.logger.info(f"  - Convergence score: {convergence_score:.2f}")
            if feedback:
                self.logger.info(f"  - Feedback: {feedback[:200]}...")
            
        except Exception as e:
            self.logger.error(f"Moderation failed: {str(e)}")
            state["error_messages"].append(f"Moderator agent error: {str(e)}")
            state["workflow_status"] = "failed"
            state["moderator_decision"] = "abort_deadlock"
            
            log_agent_execution(
                state=state,
                agent_name="Moderator",
                input_summary=f"Moderation attempt",
                output_summary=f"Error: {str(e)}",
                processing_time=time.time() - start_time,
                success=False
            )
        
        return state
    
    def _analyze_severity(self, critiques: List[Dict]) -> Dict[str, int]:
        """Analyze critique severity distribution"""
        counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0
        }
        
        for critique in critiques:
            severity = critique.get("severity", "medium")
            if severity in counts:
                counts[severity] += 1
        
        return counts
    
    def _parse_decision(self, response: str) -> tuple:
        """Parse decision from chain response"""
        decision = "iterate"  # default
        reasoning = ""
        feedback = ""
        score = 0.5
        
        for line in response.split("\n"):
            if line.startswith("DECISION:"):
                decision_text = line.replace("DECISION:", "").strip().lower()
                if decision_text in ["converged", "iterate", "abort_deadlock", "escalate_with_warning"]:
                    decision = decision_text
            elif line.startswith("REASONING:"):
                reasoning = line.replace("REASONING:", "").strip()
            elif line.startswith("FEEDBACK:"):
                feedback = line.replace("FEEDBACK:", "").strip()
            elif line.startswith("CONVERGENCE_SCORE:"):
                try:
                    score = float(line.replace("CONVERGENCE_SCORE:", "").strip())
                except:
                    pass
        
        return decision, reasoning, feedback, score
    
    def _apply_decision_rules(
        self, 
        decision: str, 
        severity_counts: Dict[str, int],
        current_round: int,
        max_rounds: int
    ) -> str:
        """Apply hard rules to override LLM decision if needed"""
        
        # Rule 1: Force deadlock if at max rounds
        if current_round >= max_rounds:
            self.logger.info(f"Forcing deadlock: reached max rounds ({max_rounds})")
            return "abort_deadlock"
        
        # Rule 2: Cannot converge with critical issues
        if decision == "converged" and severity_counts["critical"] > 0:
            self.logger.warning(f"Overriding convergence: {severity_counts['critical']} critical issues remain")
            return "iterate" if current_round < max_rounds else "escalate_with_warning"
        
        # Rule 3: Escalate if too many critical issues
        if severity_counts["critical"] >= self.critical_severity_threshold:
            self.logger.warning(f"Escalating: {severity_counts['critical']} critical issues exceed threshold")
            return "escalate_with_warning"
        
        # Rule 4: Force convergence if only low severity issues
        if severity_counts["critical"] == 0 and severity_counts["high"] == 0 and severity_counts["medium"] <= 1:
            self.logger.info("Forcing convergence: only minor issues remain")
            return "converged"
        
        return decision
    
    async def _generate_detailed_feedback(self, critiques: List[Dict]) -> str:
        """Generate detailed feedback for iteration"""
        
        # Separate issues by severity
        critical_issues = [c for c in critiques if c.get("severity") == "critical"]
        high_issues = [c for c in critiques if c.get("severity") == "high"]
        
        if not critical_issues and not high_issues:
            # Focus on medium issues
            high_issues = [c for c in critiques if c.get("severity") == "medium"][:3]
        
        # Format issues for feedback generation
        critical_str = self._format_critiques(critical_issues) if critical_issues else "None"
        high_str = self._format_critiques(high_issues) if high_issues else "None"
        
        # Generate feedback
        try:
            feedback = await self.feedback_chain.arun(
                critical_issues=critical_str,
                high_issues=high_str
            )
            return feedback
        except Exception as e:
            self.logger.error(f"Failed to generate detailed feedback: {e}")
            return "Please address the identified critical and high-severity issues."
    
    def _format_critiques(self, critiques: List[Dict]) -> str:
        """Format critiques for display"""
        if not critiques:
            return "No issues"
        
        lines = []
        for i, c in enumerate(critiques[:5], 1):  # Limit to top 5
            severity = c.get("severity", "medium").upper()
            type_str = c.get("type", "issue")
            desc = c.get("description", "")[:150]
            
            if c.get("step_ref"):
                lines.append(f"{i}. [{severity}] Step {c['step_ref']}: {desc}")
            elif c.get("claim"):
                lines.append(f"{i}. [{severity}] Claim '{c['claim'][:50]}...': {desc}")
            else:
                lines.append(f"{i}. [{severity}] {type_str}: {desc}")
        
        if len(critiques) > 5:
            lines.append(f"... and {len(critiques) - 5} more issues")
        
        return "\n".join(lines)
