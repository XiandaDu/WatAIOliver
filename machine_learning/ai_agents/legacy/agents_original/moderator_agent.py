"""
Moderator Agent - Debate Flow Controller

This agent evaluates critique reports and decides the next course of action:
convergence, iteration, or deadlock handling.
"""

from typing import List, Dict, Any
from ai_agents.agents.base_agent import BaseAgent, AgentInput, AgentOutput, AgentRole


class ModeratorAgent(BaseAgent):
    """
    Moderator Agent - Arbiter and Debate Flow Controller
    
    Responsible for:
    1. Evaluating critique severity and determining next steps
    2. Managing debate convergence logic
    3. Handling deadlock situations
    4. Generating feedback for iterative improvements
    """
    
    def __init__(self, config, llm_client=None, logger=None):
        super().__init__(AgentRole.MODERATOR, config, llm_client, logger)
        
        # Decision thresholds
        self.convergence_thresholds = {
            "no_issues": 0,
            "low_only": 1,     # Only low severity issues
            "acceptable_minor": 3,  # Up to 3 minor issues
            "critical_limit": 0,    # No critical issues allowed
            "high_limit": 1        # Max 1 high severity issue for convergence
        }
        
    async def process(self, agent_input: AgentInput) -> AgentOutput:
        """
        Evaluate critique report and determine next action
        
        Args:
            agent_input: Contains critique report, draft info, and round count
            
        Returns:
            AgentOutput: Decision on next steps with detailed reasoning
        """
        try:
            # Extract critique data
            critiques = agent_input.metadata.get('critiques', [])
            draft_id = agent_input.metadata.get('draft_id', 'unknown')
            current_round = agent_input.metadata.get('current_round', 1)
            overall_assessment = agent_input.metadata.get('overall_assessment', 'unknown')
            
            self.logger.info(f"️ Moderator evaluating critique report for {draft_id}")
            self.logger.info(f"Round {current_round}, {len(critiques)} issues found")
            
            # ULTRA VERBOSE: Log all received critiques
            self.logger.info(f"\n" + "="*200)
            self.logger.info(f"MODERATOR - DETAILED CRITIQUE ANALYSIS")
            self.logger.info(f"="*200)
            self.logger.info(f"RECEIVED CRITIQUES ({len(critiques)} total):")
            for i, critique in enumerate(critiques):
                severity = critique.get('severity', 'unknown')
                ctype = critique.get('type', 'unknown')
                desc = critique.get('description', 'no description')
                self.logger.info(f"  {i+1}. [{severity.upper()}] {ctype}: {desc}")
            self.logger.info(f"Overall assessment: {overall_assessment}")
            self.logger.info(f"="*200)
            
            # Analyze critique severity
            severity_analysis = self._analyze_critique_severity(critiques)
            
            # Make decision based on rules and thresholds
            decision = self._make_decision(
                severity_analysis, 
                current_round, 
                overall_assessment
            )
            
            # ULTRA VERBOSE: Log severity analysis and decision logic
            self.logger.info(f"\nSEVERITY BREAKDOWN:")
            self.logger.info(f"  CRITICAL: {severity_analysis['by_severity']['critical']}")
            self.logger.info(f"  HIGH: {severity_analysis['by_severity']['high']}")
            self.logger.info(f"  MEDIUM: {severity_analysis['by_severity']['medium']}")
            self.logger.info(f"  LOW: {severity_analysis['by_severity']['low']}")
            self.logger.info(f"  TOTAL: {severity_analysis['total_issues']}")
            
            self.logger.info(f"\nDECISION LOGIC:")
            self.logger.info(f"  Current Round: {current_round}")
            self.logger.info(f"  Convergence Check: {self._check_convergence_conditions(severity_analysis, current_round)}")
            self.logger.info(f"  Action: {decision['action']}")
            self.logger.info(f"  Reasoning: {decision['reasoning']}")
            self.logger.info(f"  Confidence: {decision['confidence']}")
            self.logger.info(f"="*200)
            
            # Generate appropriate response based on decision
            decision_content = await self._generate_decision_content(
                decision, 
                critiques, 
                severity_analysis, 
                current_round
            )
            
            self.logger.info(f"Moderator decision: {decision['action']}")
            
            return AgentOutput(
                success=True,
                content={
                    "decision": decision["action"],
                    "reasoning": decision["reasoning"],
                    "feedback_to_strategist": decision_content.get("feedback", ""),
                    "final_draft": decision_content.get("final_draft"),
                    "critiques": decision_content.get("remaining_critiques"),
                    "decision_metadata": {
                        "round_number": current_round,
                        "severity_breakdown": severity_analysis,
                        "convergence_score": decision["convergence_score"],
                        "decision_confidence": decision["confidence"]
                    }
                },
                metadata={
                    "draft_id": draft_id,
                    "total_critiques": len(critiques),
                    "decision_rationale": decision["detailed_reasoning"]
                },
                processing_time=0.0,  # Set by parent class
                agent_role=self.agent_role
            )
            
        except Exception as e:
            self.logger.error(f"Moderator failed: {str(e)}")
            raise e
    
    def _analyze_critique_severity(self, critiques: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze critique severity distribution and patterns"""
        
        analysis = {
            "total_issues": len(critiques),
            "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            "by_type": {"logic_flaw": 0, "fact_contradiction": 0, "hallucination": 0},
            "severity_score": 0.0,
            "most_severe": "none",
            "issue_distribution": []
        }
        
        if not critiques:
            return analysis
        
        # Count by severity and type
        severity_weights = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        total_weight = 0
        
        for critique in critiques:
            severity = critique.get('severity', 'medium')
            issue_type = critique.get('type', 'unknown')
            
            # Update counts
            if severity in analysis["by_severity"]:
                analysis["by_severity"][severity] += 1
            
            if issue_type in analysis["by_type"]:
                analysis["by_type"][issue_type] += 1
            
            # Calculate weighted severity
            weight = severity_weights.get(severity, 2)
            total_weight += weight
            
            # Track most severe issue
            if not analysis["most_severe"] or severity_weights.get(severity, 0) > severity_weights.get(analysis["most_severe"], 0):
                analysis["most_severe"] = severity
        
        # Calculate severity score (0-4 scale)
        analysis["severity_score"] = total_weight / len(critiques) if critiques else 0
        
        # Create distribution summary
        analysis["issue_distribution"] = [
            f"{count} {severity}" for severity, count in analysis["by_severity"].items() if count > 0
        ]
        
        return analysis
    
    def _make_decision(
        self, 
        severity_analysis: Dict[str, Any], 
        current_round: int, 
        overall_assessment: str
    ) -> Dict[str, Any]:
        """
        Make decision based on critique analysis and debate rules
        
        Returns:
            Dict containing decision action, reasoning, and confidence
        """
        
        critical_count = severity_analysis["by_severity"]["critical"]
        high_count = severity_analysis["by_severity"]["high"]
        medium_count = severity_analysis["by_severity"]["medium"]
        total_issues = severity_analysis["total_issues"]
        severity_score = severity_analysis["severity_score"]
        
        # Decision logic based on specified rules
        
        # Rule 1: Check convergence conditions with NEW STRICT criteria
        if self._check_convergence_conditions(severity_analysis, current_round):
            return {
                "action": "converged",
                "reasoning": self._generate_convergence_reasoning(severity_analysis),
                "convergence_score": 1.0 - (severity_score / 4.0),
                "confidence": "high",
                "detailed_reasoning": f"Quality acceptable after {current_round} rounds with {total_issues} remaining issues"
            }
        
        # Rule 2: ESCALATION - 3+ iterations with persistent MEDIUM+ issues
        if current_round >= 3 and (critical_count > 0 or high_count > 0 or medium_count > 0):
            return {
                "action": "escalate_with_warning",
                "reasoning": f"After {current_round} improvement iterations, {critical_count + high_count + medium_count} serious issues remain",
                "convergence_score": 0.4,
                "confidence": "low",
                "detailed_reasoning": f"Persistent quality issues: {critical_count} critical, {high_count} high, {medium_count} medium - escalating to user notification",
                "unresolved_issues": {
                    "critical": critical_count,
                    "high": high_count, 
                    "medium": medium_count
                }
            }
        
        # Rule 3: Standard deadlock (max rounds without escalation case)
        if current_round >= self.config.max_debate_rounds:
            return {
                "action": "abort_deadlock",
                "reasoning": f"Maximum debate rounds ({self.config.max_debate_rounds}) reached",
                "convergence_score": 0.3,
                "confidence": "medium",
                "detailed_reasoning": f"Hard deadlock after {current_round} rounds"
            }
        
        # Rule 3: Critical issues require iteration
        if critical_count > 0:
            return {
                "action": "iterate",
                "reasoning": f"Critical issues ({critical_count}) must be addressed before convergence",
                "convergence_score": 0.1,
                "confidence": "high",
                "detailed_reasoning": "Critical factual errors or logical fallacies detected"
            }
        
        # Rule 4: Too many high severity issues
        if high_count > self.convergence_thresholds["high_limit"] or high_count > 2:
            return {
                "action": "iterate", 
                "reasoning": f"Too many high severity issues ({high_count}) require revision",
                "convergence_score": 0.4,
                "confidence": "high",
                "detailed_reasoning": "Significant logical gaps or unsupported claims need addressing"
            }
        
        # Rule 5: Moderate issue threshold
        if total_issues > 5 and severity_score > 2.0:
            return {
                "action": "iterate",
                "reasoning": f"Overall issue severity ({severity_score:.2f}) exceeds acceptable threshold",
                "convergence_score": 0.5,
                "confidence": "medium", 
                "detailed_reasoning": f"Multiple issues with average severity {severity_score:.2f} require attention"
            }
        
        # Default: Converge with minor issues
        return {
            "action": "converged",
            "reasoning": f"Issues are minor and acceptable ({total_issues} total, severity {severity_score:.2f})",
            "convergence_score": 0.8,
            "confidence": "medium",
            "detailed_reasoning": "Quality meets acceptance criteria despite minor remaining issues"
        }
    
    def _check_convergence_conditions(self, severity_analysis: Dict[str, Any], current_round: int) -> bool:
        """Check if debate has converged based on NEW STRICT criteria"""
        
        critical_count = severity_analysis["by_severity"]["critical"]
        high_count = severity_analysis["by_severity"]["high"]
        medium_count = severity_analysis["by_severity"]["medium"]
        low_count = severity_analysis["by_severity"]["low"]
        total_issues = severity_analysis["total_issues"]
        
        # Rule 1: Perfect convergence - ZERO issues allowed
        if total_issues == 0:
            return True
        
        # Rule 2: NO convergence allowed if ANY issues exist UNLESS we've done 3+ iterations
        if current_round < 3:
            return False  # Always iterate if we haven't done 3 rounds yet
            
        # Rule 3: After 3+ iterations, only converge if NO CRITICAL/HIGH/MEDIUM issues remain
        if critical_count > 0 or high_count > 0 or medium_count > 0:
            return False  # Still have serious issues after 3 iterations - this will trigger escalation
        
        # Rule 4: After 3+ iterations with only LOW severity issues - allow convergence
        return True
    
    def _generate_convergence_reasoning(self, severity_analysis: Dict[str, Any]) -> str:
        """Generate human-readable convergence reasoning"""
        
        total_issues = severity_analysis["total_issues"]
        
        if total_issues == 0:
            return "No issues found - draft meets all quality criteria"
        
        issue_summary = []
        for severity, count in severity_analysis["by_severity"].items():
            if count > 0:
                issue_summary.append(f"{count} {severity}")
        
        return f"Draft acceptable with only minor issues: {', '.join(issue_summary)}"
    
    async def _generate_decision_content(
        self, 
        decision: Dict[str, Any], 
        critiques: List[Dict[str, Any]], 
        severity_analysis: Dict[str, Any], 
        current_round: int
    ) -> Dict[str, Any]:
        """Generate appropriate content based on decision"""
        
        content = {}
        
        if decision["action"] == "converged":
            # Prepare final package
            content["final_draft"] = {
                "status": "approved",
                "remaining_issues": [c for c in critiques if c.get('severity') == 'low'],
                "quality_score": decision["convergence_score"]
            }
            content["remaining_critiques"] = [c for c in critiques if c.get('severity') == 'low']
            
        elif decision["action"] == "iterate":
            # Generate focused feedback for revision
            content["feedback"] = await self._generate_revision_feedback(critiques, severity_analysis)
            
        elif decision["action"] == "escalate_with_warning":
            # Handle escalation - persistent issues after 3 iterations
            content["final_draft"] = {
                "status": "escalated",
                "quality_warning": True,
                "persistent_issues": decision["unresolved_issues"],
                "quality_score": decision["convergence_score"]
            }
            content["warning_message"] = self._generate_escalation_warning(critiques, severity_analysis)
            content["remaining_critiques"] = critiques
            
        elif decision["action"] == "abort_deadlock":
            # Handle deadlock situation
            content["final_draft"] = {
                "status": "deadlock",
                "partial_quality": True,
                "unresolved_issues": critiques,
                "quality_score": decision["convergence_score"]
            }
            content["remaining_critiques"] = critiques
        
        return content
    
    async def _generate_revision_feedback(
        self, 
        critiques: List[Dict[str, Any]], 
        severity_analysis: Dict[str, Any]
    ) -> str:
        """Generate actionable feedback for the Strategist to revise the draft"""
        
        if not critiques:
            return "No specific issues to address."
        
        # Priority order: critical > high > medium > low
        priority_critiques = sorted(
            critiques, 
            key=lambda x: {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(x.get('severity', 'medium'), 2),
            reverse=True
        )
        
        feedback_sections = []
        
        # Group critiques by severity for structured feedback
        critical_issues = [c for c in critiques if c.get('severity') == 'critical']
        high_issues = [c for c in critiques if c.get('severity') == 'high']
        medium_issues = [c for c in critiques if c.get('severity') == 'medium']
        
        if critical_issues:
            feedback_sections.append("CRITICAL ISSUES (must fix):")
            for issue in critical_issues[:3]:  # Limit to avoid overwhelming feedback
                description = issue.get('description', 'No description')
                step_ref = issue.get('step_ref')
                step_info = f" (Step {step_ref})" if step_ref else ""
                feedback_sections.append(f"• {description}{step_info}")
        
        if high_issues:
            feedback_sections.append("\nHIGH PRIORITY ISSUES:")
            for issue in high_issues[:3]:
                description = issue.get('description', 'No description')
                step_ref = issue.get('step_ref') 
                step_info = f" (Step {step_ref})" if step_ref else ""
                feedback_sections.append(f"• {description}{step_info}")
        
        if medium_issues and len(critical_issues + high_issues) < 3:
            feedback_sections.append("\nMODERATE ISSUES:")
            for issue in medium_issues[:2]:
                description = issue.get('description', 'No description')
                feedback_sections.append(f"• {description}")
        
        # Add guidance
        feedback_sections.append("\nRevision Guidance:")
        
        if critical_issues or high_issues:
            feedback_sections.append("• Focus on addressing critical and high priority issues first")
        
        if severity_analysis["by_type"]["logic_flaw"] > 0:
            feedback_sections.append("• Review and strengthen logical reasoning connections")
        
        if severity_analysis["by_type"]["fact_contradiction"] > 0:
            feedback_sections.append("• Verify factual claims against provided context")
        
        if severity_analysis["by_type"]["hallucination"] > 0:
            feedback_sections.append("• Remove unsupported information not found in context")
        
        return "\n".join(feedback_sections)
    
    def _generate_escalation_warning(
        self, 
        critiques: List[Dict[str, Any]], 
        severity_analysis: Dict[str, Any]
    ) -> str:
        """Generate warning message for escalated quality issues"""
        
        critical_count = severity_analysis["by_severity"]["critical"]
        high_count = severity_analysis["by_severity"]["high"]
        medium_count = severity_analysis["by_severity"]["medium"]
        
        warning_parts = []
        warning_parts.append("️ QUALITY ESCALATION NOTICE:")
        warning_parts.append(f"After 3 improvement iterations, {critical_count + high_count + medium_count} serious issues remain unresolved:")
        
        if critical_count > 0:
            warning_parts.append(f"•{critical_count} CRITICAL issues (major factual errors, severe logical flaws)")
            
        if high_count > 0:
            warning_parts.append(f"•{high_count} HIGH severity issues (significant logical gaps, unsupported claims)")
            
        if medium_count > 0:
            warning_parts.append(f"•{medium_count} MEDIUM severity issues (inconsistencies, missing details)")
            
        warning_parts.append("\nThe system has made its best effort to improve this response, but some quality concerns persist.")
        warning_parts.append("Please review the answer critically and consider these limitations when using the information.")
        
        # Add specific issue details
        if len(critiques) > 0:
            warning_parts.append("\nSpecific concerns:")
            for issue in critiques[:3]:  # Show top 3 issues
                severity = issue.get('severity', 'unknown').upper()
                description = issue.get('description', 'No description')[:100]
                warning_parts.append(f"• [{severity}] {description}...")
                
        return "\n".join(warning_parts)
    
    def get_decision_statistics(self) -> Dict[str, Any]:
        """Get statistics about moderator decisions"""
        return {
            "convergence_rate": getattr(self, 'convergence_count', 0) / max(self.execution_count, 1),
            "average_rounds": getattr(self, 'total_rounds', 0) / max(self.execution_count, 1),
            "deadlock_rate": getattr(self, 'deadlock_count', 0) / max(self.execution_count, 1)
        } 