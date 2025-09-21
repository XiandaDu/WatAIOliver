"""
Moderator Agent - LangChain Implementation

Arbiter that controls the debate flow and makes convergence decisions.
"""

import time
import json
from typing import List, Dict, Any
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
# Messages handled via tuple format in ChatPromptTemplate
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
        self.llm_client = context.llm_client
        self.llm = create_langchain_llm(self.llm_client)
        
        # Decision thresholds
        self.convergence_threshold = 0.3  # Converge if score < 0.3 (adjusted for actual scores)
        self.critical_severity_threshold = 2  # Max critical issues allowed
        
        # Explicit severity to score mapping (from planning docs)
        self.severity_to_score = {
            "low": 0.2,
            "medium": 0.5,
            "high": 0.8,
            "critical": 1.0
        }
        
        # Setup chains
        self._setup_chains()
    
    def _setup_chains(self):
        """Setup LangChain chains for moderation decisions"""
        
        # Main decision chain
        self.decision_chain = LLMChain(
            llm=self.llm,
            prompt=ChatPromptTemplate.from_messages([
                ("system", """You are a debate moderator controlling the quality assurance process.
                Analyze critiques and make strategic decisions about the debate flow.
                
                Decision options:
                - converged: Draft is acceptable (ONLY low severity or no issues)
                - iterate: Draft needs revision (medium, high, or critical issues found)
                - abort_deadlock: Cannot converge after max attempts
                - escalate_with_warning: Serious quality concerns
                
                CRITICAL RULES:
                - If ANY medium, high, or critical issues exist: ALWAYS choose 'iterate'
                - Only choose 'converged' if ALL issues are low severity or no issues found
                - Be strict about quality standards"""),
                ("human", """Query: {query}

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
DECISION: [converged/iterate/abort_deadlock/escalate_with_warning]
REASONING: [Your reasoning]
FEEDBACK: [Specific actionable feedback for strategist if iterating]
CONVERGENCE_SCORE: [0.XX]

IMPORTANT: If DECISION is 'iterate', provide clear, specific feedback about what needs to be fixed.""")
            ])
        )
        
        # Feedback generation chain
        self.feedback_chain = LLMChain(
            llm=self.llm,
            prompt=ChatPromptTemplate.from_messages([
                ("system", """Generate specific, actionable feedback for draft revision based on ACTUAL issues found.

CRITICAL INSTRUCTIONS:
1. Read the actual issues provided below carefully
2. Generate feedback based ONLY on the real issues listed
3. Do NOT use placeholder text like "[Specific concept X]" or "[Specific claim Y]"
4. Provide concrete, actionable advice based on the actual problems
5. If no real issues are provided, generate minimal feedback"""),
                ("human", """ACTUAL Critical Issues Found:
{critical_issues}

ACTUAL High Priority Issues Found:
{high_issues}

CRITICAL: You must generate PLAIN TEXT feedback, NOT code or templates.

TASK: Write specific feedback for the strategist in plain English.

Requirements:
1. Write actual feedback text, not Python code
2. Reference the problems listed above specifically
3. Provide concrete revision instructions
4. Do NOT output code, variables, or programming syntax
5. Write as if speaking to a human

Example format:
1. Fix the logical issue in step 2 by explaining why...
2. Correct the factual error about... by checking the source material...
3. Remove the unsupported claim about... since it's not in the context...

Write ONLY plain text feedback, no code.""")
            ])
        )
    
    async def __call__(self, state: WorkflowState) -> WorkflowState:
        """Make moderation decision based on critiques"""
        start_time = time.time()
        
        try:
            self.logger.info("="*250)
            simple_log.info("="*250)
            self.logger.info(f"MODERATOR AGENT - ROUND {state['current_round']}")
            simple_log.info(f"MODERATOR AGENT - ROUND {state['current_round']}")
            self.logger.info("="*250)
            simple_log.info("="*250)
            simple_log.info("MODERATOR START", {
                "round": state['current_round'],
                "has_drafts": bool(state.get('draft_content')),
                "has_critiques": bool(state.get('critiques'))
            })
            
            critiques = state["critiques"]
            current_round = state["current_round"]
            max_rounds = state["max_rounds"]
            draft = state["draft"]
            
            # Analyze critique severity
            severity_counts = self._analyze_severity(critiques)
            
            self.logger.info(f"Critique analysis:")
            simple_log.info(f"Critique analysis:")
            self.logger.info(f"  - Critical: {severity_counts['critical']}")
            simple_log.info(f"  - Critical: {severity_counts['critical']}")
            self.logger.info(f"  - High: {severity_counts['high']}")
            simple_log.info(f"  - High: {severity_counts['high']}")
            self.logger.info(f"  - Medium: {severity_counts['medium']}")
            simple_log.info(f"  - Medium: {severity_counts['medium']}")
            self.logger.info(f"  - Low: {severity_counts['low']}")
            simple_log.info(f"  - Low: {severity_counts['low']}")
            
            # Prepare decision inputs
            draft_summary = draft["content"] if draft else "No draft"
            
            # Log critique formatting to debug truncation issues
            self.logger.info(f"Formatting {len(critiques)} critiques for moderator input:")
            simple_log.info(f"Formatting {len(critiques)} critiques for moderator input:")
            for i, critique in enumerate(critiques):  # Show all critiques for debugging
                desc_len = len(critique.get("description", ""))
                self.logger.info(f"  Critique {i+1}: {critique.get('type')} - {critique.get('severity')} - {desc_len} chars")
                simple_log.info(f"  Critique {i+1}: {critique.get('type')} - {critique.get('severity')} - {desc_len} chars")
                # Show full description in logs - no truncation
                if desc_len > 0:
                    self.logger.info(f"    Full description: {critique.get('description', '')}")
                    simple_log.info(f"    Full description: {critique.get('description', '')}")
            
            critiques_str = self._format_critiques(critiques)
            has_previous = "Yes" if state.get("moderator_feedback") else "No"
            
            # Make decision
            decision_inputs = {
                "query": state["query"],
                "current_round": current_round,
                "max_rounds": max_rounds,
                "draft_summary": draft_summary,
                "critiques": critiques_str,
                "critical_count": severity_counts["critical"],
                "high_count": severity_counts["high"],
                "medium_count": severity_counts["medium"],
                "low_count": severity_counts["low"],
                "has_previous": has_previous
            }
            
            self.logger.info("="*250)
            simple_log.info("="*250)
            self.logger.info("LLM INPUT - MODERATOR DECISION CHAIN")
            simple_log.info("LLM INPUT - MODERATOR DECISION CHAIN")
            self.logger.info("="*250)
            simple_log.info("="*250)
            try:
                formatted_inputs = json.dumps(decision_inputs, indent=2)
                self.logger.info(f"Decision inputs (formatted):\n{formatted_inputs}")
                simple_log.info(f"Decision inputs (formatted):\n{formatted_inputs}")
            except:
                self.logger.info(f"Decision inputs: {decision_inputs}")
                simple_log.info(f"Decision inputs: {decision_inputs}")
            self.logger.info("="*250)
            simple_log.info("="*250)
            
            # Log the ACTUAL prompt being sent to the LLM
            try:
                prompt_value = self.decision_chain.prompt.format_prompt(**decision_inputs)
                messages = prompt_value.to_messages()
                
                self.logger.info(">>> ACTUAL COMPLETE PROMPT BEING SENT TO MODERATOR LLM <<<")
                simple_log.info(">>> ACTUAL COMPLETE PROMPT BEING SENT TO MODERATOR LLM <<<")
                self.logger.info("START_PROMPT" + "="*240)
                simple_log.info("START_PROMPT" + "="*240)
                for msg in messages:
                    # Check message type by its class name
                    msg_type = type(msg).__name__
                    if 'System' in msg_type:
                        self.logger.info(f"System: {msg.content}")
                        simple_log.info(f"System: {msg.content}")
                    elif 'Human' in msg_type:
                        self.logger.info(f"Human: {msg.content}")
                        simple_log.info(f"Human: {msg.content}")
                    else:
                        self.logger.info(f"{msg_type}: {msg.content}")
                        simple_log.info(f"{msg_type}: {msg.content}")
                self.logger.info("END_PROMPT" + "="*242)
                simple_log.info("END_PROMPT" + "="*242)
                self.logger.info(f"Total prompt length: {sum(len(msg.content) for msg in messages)} characters")
                simple_log.info(f"Total prompt length: {sum(len(msg.content) for msg in messages)} characters")
            except Exception as e:
                self.logger.error(f"Could not log prompt: {e}")
            
            # Use arun for proper variable substitution with ChatPromptTemplate
            decision_response = await self.decision_chain.arun(**decision_inputs)
            
            self.logger.info("="*250)
            simple_log.info("="*250)
            self.logger.info("LLM OUTPUT - MODERATOR DECISION CHAIN")
            simple_log.info("LLM OUTPUT - MODERATOR DECISION CHAIN")
            self.logger.info("="*250)
            simple_log.info("="*250)
            # Format the raw response nicely if it contains JSON
            if "```json" in decision_response:
                try:
                    # Extract and format JSON
                    json_part = decision_response.split("```json")[1].split("```")[0].strip()
                    formatted_json = json.dumps(json.loads(json_part), indent=2)
                    self.logger.info(f"Raw decision response:\n{formatted_json}")
                    simple_log.info(f"Raw decision response:\n{formatted_json}")
                except:
                    self.logger.info(f"Raw decision response: {decision_response}")
                    simple_log.info(f"Raw decision response: {decision_response}")
            else:
                self.logger.info(f"Raw decision response: {decision_response}")
                simple_log.info(f"Raw decision response: {decision_response}")
            self.logger.info("="*250)
            simple_log.info("="*250)
            
            # Parse decision
            decision, reasoning, feedback, convergence_score = self._parse_decision(decision_response)
            
            # Apply decision rules
            decision = self._apply_decision_rules(
                decision, severity_counts, current_round, max_rounds
            )
            
            # Generate detailed feedback if iterating
            if decision == "iterate":
                # Ensure feedback is concrete and actionable
                if not feedback or len(feedback) < 20:
                    detailed_feedback = await self._generate_detailed_feedback(critiques)
                    feedback = detailed_feedback if detailed_feedback else self._generate_simple_feedback(severity_counts)
            
            # Create formatted JSON output according to specification
            if decision == "converged":
                formatted_output = {
                    "decision": "converged",
                    "payload": {
                        "final_draft": draft,
                        "critiques": [c for c in critiques if c.get("severity") == "low"]
                    }
                }
            elif decision == "iterate":
                formatted_output = {
                    "decision": "iterate",
                    "feedback_to_strategist": feedback or "Please address the identified issues and improve the solution."
                }
            elif decision == "abort_deadlock":
                formatted_output = {
                    "decision": "abort_deadlock",
                    "reason": f"Failed to converge after {current_round} iterations."
                }
            else:  # escalate_with_warning
                formatted_output = {
                    "decision": "escalate_with_warning",
                    "reason": f"Critical issues remain: {severity_counts['critical']} critical, {severity_counts['high']} high severity issues."
                }
            
            # Log the JSON output
            self.logger.info("="*250)
            simple_log.info("="*250)
            self.logger.info("MODERATOR OUTPUT (JSON)")
            simple_log.info("MODERATOR OUTPUT (JSON)")
            self.logger.info("="*250)
            simple_log.info("="*250)
            self.logger.info(json.dumps(formatted_output, indent=2))
            simple_log.info(json.dumps(formatted_output, indent=2))
            self.logger.info("="*250)
            simple_log.info("="*250)
            
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
            simple_log.info(f"Moderation decision:")
            self.logger.info(f"  - Decision: {decision}")
            simple_log.info(f"  - Decision: {decision}")
            self.logger.info(f"  - Reasoning: {reasoning}")
            simple_log.info(f"  - Reasoning: {reasoning}")
            self.logger.info(f"  - Convergence score: {convergence_score:.2f}")
            simple_log.info(f"  - Convergence score: {convergence_score:.2f}")
            if feedback:
                self.logger.info(f"  - Feedback: {feedback}")
                simple_log.info(f"  - Feedback: {feedback}")
            
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
        
        self.logger.info(f"Decision rule processing:")
        simple_log.info(f"Decision rule processing:")
        self.logger.info(f"  LLM decision: {decision}")
        simple_log.info(f"  LLM decision: {decision}")
        self.logger.info(f"  Round: {current_round}/{max_rounds}")
        simple_log.info(f"  Round: {current_round}/{max_rounds}")
        self.logger.info(f"  Severity counts: {severity_counts}")
        simple_log.info(f"  Severity counts: {severity_counts}")
        
        # Rule 1: Force deadlock if at max rounds
        if current_round >= max_rounds:
            self.logger.warning(f"RULE 1 TRIGGERED: Forcing deadlock - reached max rounds ({max_rounds})")
            return "abort_deadlock"
        
        # Rule 2: Cannot converge with critical issues
        if decision == "converged" and severity_counts["critical"] > 0:
            self.logger.warning(f"RULE 2 TRIGGERED: Overriding convergence - {severity_counts['critical']} critical issues remain")
            return "iterate" if current_round < max_rounds else "escalate_with_warning"
        
        # Rule 3: Escalate if too many critical issues
        if severity_counts["critical"] >= self.critical_severity_threshold:
            self.logger.warning(f"RULE 3 TRIGGERED: Escalating - {severity_counts['critical']} critical issues exceed threshold")
            return "escalate_with_warning"
        
        # Rule 4: Calculate aggregate severity score
        aggregate_score = 0.0
        for severity, count in severity_counts.items():
            aggregate_score += count * self.severity_to_score.get(severity, 0.5)
        
        # Log aggregate score calculation for debugging
        self.logger.info(f"Aggregate severity score calculation:")
        simple_log.info(f"Aggregate severity score calculation:")
        for severity, count in severity_counts.items():
            if count > 0:
                score_contribution = count * self.severity_to_score.get(severity, 0.5)
                self.logger.info(f"  {count} {severity} × {self.severity_to_score.get(severity, 0.5)} = {score_contribution}")
                simple_log.info(f"  {count} {severity} × {self.severity_to_score.get(severity, 0.5)} = {score_contribution}")
        self.logger.info(f"  Total aggregate score: {aggregate_score:.2f}")
        simple_log.info(f"  Total aggregate score: {aggregate_score:.2f}")
        self.logger.info(f"  Convergence threshold: {self.convergence_threshold}")
        simple_log.info(f"  Convergence threshold: {self.convergence_threshold}")
        
        # Rule 5: Force convergence if aggregate score is below threshold AND LLM agrees
        if aggregate_score < self.convergence_threshold and decision == "converged":
            self.logger.info(f"RULE 5 TRIGGERED: Allowing convergence - aggregate score {aggregate_score:.2f} < threshold {self.convergence_threshold} and LLM agrees")
            simple_log.info(f"RULE 5 TRIGGERED: Allowing convergence - aggregate score {aggregate_score:.2f} < threshold {self.convergence_threshold} and LLM agrees")
            return "converged"
        
        # Rule 6: Force convergence ONLY if no critical, high, or medium issues exist
        if severity_counts["critical"] == 0 and severity_counts["high"] == 0 and severity_counts["medium"] == 0:
            self.logger.info("RULE 6 TRIGGERED: Forcing convergence - only low-severity issues remain")
            simple_log.info("RULE 6 TRIGGERED: Forcing convergence - only low-severity issues remain")
            return "converged"
        
        # Rule 7: Respect LLM decision if no rules override
        self.logger.info(f"NO RULES TRIGGERED: Respecting LLM decision '{decision}'")
        simple_log.info(f"NO RULES TRIGGERED: Respecting LLM decision '{decision}'")
        return decision
    
    async def _generate_detailed_feedback(self, critiques: List[Dict]) -> str:
        """Generate detailed feedback for iteration"""
        
        # Separate issues by severity
        critical_issues = [c for c in critiques if c.get("severity") == "critical"]
        high_issues = [c for c in critiques if c.get("severity") == "high"]
        
        if not critical_issues and not high_issues:
            # Focus on medium issues
            high_issues = [c for c in critiques if c.get("severity") == "medium"]  # All medium issues
        
        # Format issues for feedback generation
        critical_str = self._format_critiques(critical_issues) if critical_issues else "None"
        high_str = self._format_critiques(high_issues) if high_issues else "None"
        
        # Generate feedback
        try:
            feedback_inputs = {
                "critical_issues": critical_str,
                "high_issues": high_str
            }
            
            self.logger.info("="*250)
            simple_log.info("="*250)
            self.logger.info("LLM INPUT - MODERATOR FEEDBACK CHAIN")
            simple_log.info("LLM INPUT - MODERATOR FEEDBACK CHAIN")
            self.logger.info("="*250)
            simple_log.info("="*250)
            try:
                formatted_feedback_inputs = json.dumps(feedback_inputs, indent=2)
                self.logger.info(f"Feedback inputs (formatted):\n{formatted_feedback_inputs}")
                simple_log.info(f"Feedback inputs (formatted):\n{formatted_feedback_inputs}")
            except:
                self.logger.info(f"Feedback inputs: {feedback_inputs}")
                simple_log.info(f"Feedback inputs: {feedback_inputs}")
            self.logger.info("="*250)
            simple_log.info("="*250)
            
            # Log the ACTUAL feedback prompt
            feedback_inputs = {
                'critical_issues': critical_str,
                'high_issues': high_str
            }
            
            try:
                prompt_value = self.feedback_chain.prompt.format_prompt(**feedback_inputs)
                messages = prompt_value.to_messages()
                
                self.logger.info(">>> ACTUAL COMPLETE FEEDBACK PROMPT <<<")
                simple_log.info(">>> ACTUAL COMPLETE FEEDBACK PROMPT <<<")
                self.logger.info("START_FEEDBACK_PROMPT" + "="*230)
                simple_log.info("START_FEEDBACK_PROMPT" + "="*230)
                for i, msg in enumerate(messages):
                    self.logger.info(f"Message {i+1}: {msg.content}")
                    simple_log.info(f"Message {i+1}: {msg.content}")
                self.logger.info("END_FEEDBACK_PROMPT" + "="*232)
                simple_log.info("END_FEEDBACK_PROMPT" + "="*232)
                self.logger.info(f"Total prompt length: {sum(len(msg.content) for msg in messages)} characters")
                simple_log.info(f"Total prompt length: {sum(len(msg.content) for msg in messages)} characters")
            except Exception as e:
                self.logger.error(f"Could not log feedback prompt: {e}")
            
            # Use arun for proper substitution
            feedback = await self.feedback_chain.arun(**feedback_inputs)
            
            self.logger.info("="*250)
            simple_log.info("="*250)
            self.logger.info("LLM OUTPUT - MODERATOR FEEDBACK CHAIN")
            simple_log.info("LLM OUTPUT - MODERATOR FEEDBACK CHAIN")
            self.logger.info("="*250)
            simple_log.info("="*250)
            self.logger.info(f"Generated feedback: {feedback}")
            simple_log.info(f"Generated feedback: {feedback}")
            self.logger.info("="*250)
            simple_log.info("="*250)
            
            return feedback
        except Exception as e:
            self.logger.error(f"Failed to generate detailed feedback: {e}")
            return "Please address the identified critical and high-severity issues."
    
    def _generate_simple_feedback(self, severity_counts: Dict[str, int]) -> str:
        """Generate simple fallback feedback based on severity counts"""
        feedback_parts = []
        
        if severity_counts.get("critical", 0) > 0:
            feedback_parts.append(f"Address {severity_counts['critical']} critical issues that prevent acceptance.")
        
        if severity_counts.get("high", 0) > 0:
            feedback_parts.append(f"Fix {severity_counts['high']} high-priority issues.")
            
        if severity_counts.get("medium", 0) > 0:
            feedback_parts.append(f"Consider resolving {severity_counts['medium']} medium-priority issues.")
        
        if not feedback_parts:
            return "Minor revisions suggested based on low-priority feedback."
        
        return " ".join(feedback_parts)
    
    def _format_critiques(self, critiques: List[Dict]) -> str:
        """Format critiques for display"""
        if not critiques:
            return "No issues"
        
        lines = []
        for i, c in enumerate(critiques, 1):  # All critiques
            severity = c.get("severity", "medium").upper()
            type_str = c.get("type", "issue")
            desc = c.get("description", "")  # Keep full description - no truncation
            
            if c.get("step_ref"):
                lines.append(f"{i}. [{severity}] Step {c['step_ref']}: {desc}")
            elif c.get("claim"):
                claim_preview = c['claim']  # Full claim - no truncation
                lines.append(f"{i}. [{severity}] Claim '{claim_preview}': {desc}")
            else:
                lines.append(f"{i}. [{severity}] {type_str}: {desc}")
        
        # Show all critiques - no arbitrary limits
        
        return "\n".join(lines)
