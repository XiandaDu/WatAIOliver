"""
Critic Agent - Critical Verifier

This agent performs ruthless, evidence-based review of draft solutions,
identifying logical flaws, factual errors, and hallucinations.
"""

import re
from typing import List, Dict, Any, Tuple
from ai_agents.agents.base_agent import BaseAgent, AgentInput, AgentOutput, AgentRole


class CriticAgent(BaseAgent):
    """
    Critic Agent - Critical Verifier
    
    Responsible for:
    1. Logical verification of Chain-of-Thought steps
    2. Fact-checking against provided context
    3. Hallucination detection
    4. Generating structured critique reports
    """
    
    def __init__(self, config, llm_client=None, logger=None):
        super().__init__(AgentRole.CRITIC, config, llm_client, logger)
        
        # Critic-specific settings
        self.system_prompt = self._build_system_prompt()
        
        # Severity levels for critiques
        self.severity_levels = {
            "critical": 4,    # Major factual errors, logical fallacies
            "high": 3,        # Significant logical gaps, unsupported claims
            "medium": 2,      # Minor inconsistencies, missing details
            "low": 1         # Style issues, minor improvements
        }
        
    def _build_system_prompt(self) -> str:
        """Build the system prompt for the critic"""
        return """
        You are a rigorous academic critic and fact-checker. Your role is to:

        1. ANALYZE the draft solution and Chain-of-Thought for logical consistency
        2. VERIFY factual claims against the provided context
        3. DETECT any hallucinated or unsupported information
        4. IDENTIFY logical gaps, fallacies, or inconsistencies

        Critical principles:
        - Be ruthless but constructive in your analysis
        - Focus on evidence-based verification
        - Identify specific issues with precise references
        - Classify issues by severity: critical, high, medium, low
        - Do NOT provide corrections, only identify problems

        Your output should be a structured critique report suitable for revision guidance.
        """
    
    async def process(self, agent_input: AgentInput) -> AgentOutput:
        """
        Perform critical verification of draft solution
        
        Args:
            agent_input: Contains draft, CoT, context, and metadata
            
        Returns:
            AgentOutput: Structured critique report with issues identified
        """
        import time
        start_time = time.time()
        
        try:
            # Extract data from input
            draft_content = agent_input.metadata.get('draft_content', '')
            chain_of_thought = agent_input.metadata.get('chain_of_thought', [])
            context = agent_input.context
            
            self.logger.info(f"Critic analyzing draft solution...")
            self.logger.info(f"CoT steps: {len(chain_of_thought)}, Context items: {len(context)}")
            
            # Perform three core verification tasks in parallel
            critiques = []
            
            # Task 1: Logical Verification
            self.logger.info("Starting logical verification...")
            logic_start = time.time()
            logic_critiques = await self._verify_logical_consistency(chain_of_thought, draft_content)
            logic_time = time.time() - logic_start
            self.logger.info(f"Logical verification completed in {logic_time:.2f}s")
            
            # Task 2: Factual Verification
            self.logger.info("Starting factual verification...")
            fact_start = time.time()
            factual_issues = await self._verify_factual_accuracy(draft_content, context)
            fact_time = time.time() - fact_start
            self.logger.info(f"Factual verification completed in {fact_time:.2f}s")
            
            # Task 3: Hallucination Detection
            self.logger.info("Starting hallucination detection...")
            halluc_start = time.time()
            hallucination_issues = await self._detect_hallucinations(draft_content, context)
            halluc_time = time.time() - halluc_start
            self.logger.info(f"Hallucination detection completed in {halluc_time:.2f}s")
            
            # Combine all critiques
            critiques.extend(logic_critiques)
            critiques.extend(factual_issues)
            critiques.extend(hallucination_issues)
            
            # Assess overall critique severity
            overall_assessment = self._assess_overall_quality(critiques)
            
            self.logger.info(f"Found {len(critiques)} issues - Assessment: {overall_assessment}")
            
            return AgentOutput(
                success=True,
                content={
                    "draft_id": agent_input.metadata.get('draft_id', 'unknown'),
                    "critiques": critiques,
                    "overall_assessment": overall_assessment,
                    "critique_summary": {
                        "total_issues": len(critiques),
                        "critical_issues": len([c for c in critiques if c.get('severity') == 'critical']),
                        "high_issues": len([c for c in critiques if c.get('severity') == 'high']),
                        "verification_categories": {
                            "logical": len([c for c in critiques if c.get('type') == 'logic_flaw']),
                            "factual": len([c for c in critiques if c.get('type') == 'fact_contradiction']),
                            "hallucination": len([c for c in critiques if c.get('type') == 'hallucination'])
                        }
                    }
                },
                metadata={
                    "verification_scope": {
                        "cot_steps_analyzed": len(chain_of_thought),
                        "context_items_checked": len(context),
                        "draft_length": len(draft_content)
                    }
                },
                processing_time=0.0,  # Set by parent class
                agent_role=self.agent_role
            )
            
        except Exception as e:
            self.logger.error(f"Critic failed: {str(e)}")
            raise e
    
    async def _verify_logical_consistency(
        self, 
        chain_of_thought: List[Dict[str, Any]], 
        draft_content: str
    ) -> List[Dict[str, Any]]:
        """Verify logical flow and consistency in reasoning"""
        
        logical_issues = []
        
        if not chain_of_thought:
            logical_issues.append({
                "type": "logic_flaw",
                "severity": "high",
                "description": "No Chain-of-Thought provided for verification",
                "step_ref": None
            })
            return logical_issues
        
        try:
            # Check each reasoning step for logical validity
            for i, step in enumerate(chain_of_thought):
                step_issues = await self._analyze_reasoning_step(step, i, chain_of_thought)
                logical_issues.extend(step_issues)
            
            # Check overall logical flow
            flow_issues = await self._analyze_logical_flow(chain_of_thought, draft_content)
            logical_issues.extend(flow_issues)
            
            self.logger.debug(f"Logical verification found {len(logical_issues)} issues")
            
        except Exception as e:
            self.logger.error(f"Logical verification failed: {str(e)}")
            logical_issues.append({
                "type": "logic_flaw",
                "severity": "medium",
                "description": f"Logical verification failed due to error: {str(e)}",
                "step_ref": None
            })
        
        return logical_issues
    
    async def _analyze_reasoning_step(
        self, 
        step: Dict[str, Any], 
        step_index: int, 
        all_steps: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Analyze a single reasoning step for logical issues"""
        
        issues = []
        step_num = step.get('step', step_index + 1)
        step_thought = step.get('thought', '')
        
        # Check for empty or trivial steps
        if len(step_thought.strip()) < 20:
            issues.append({
                "type": "logic_flaw",
                "severity": "medium",
                "step_ref": step_num,
                "description": f"Step {step_num} is too brief or lacks substance"
            })
            return issues
        
        # Use LLM to analyze logical validity
        if self.llm_client:
            try:
                previous_context = ""
                if step_index > 0:
                    prev_steps = all_steps[:step_index]
                    previous_context = "\n".join([f"Step {s.get('step', i+1)}: {s.get('thought', '')}" for i, s in enumerate(prev_steps)])
                
                prompt = f"""
                Analyze the logical validity of the following reasoning step:

                Previous steps context:
                {previous_context}

                Current step to analyze:
                Step {step_num}: {step_thought}

                Check for:
                1. Logical fallacies or invalid inferences
                2. Unsupported leaps in reasoning
                3. Contradictions with previous steps
                4. Missing crucial logical connections

                If you find issues, respond in this format:
                ISSUE: [brief description]
                SEVERITY: [critical/high/medium/low]
                EXPLANATION: [detailed explanation]

                If no significant logical issues, respond: "NO_ISSUES"
                """
                
                response = await self._call_llm(prompt, temperature=0.1)
                
                if response and "NO_ISSUES" not in response.upper():
                    # Parse LLM response for issues
                    parsed_issues = self._parse_llm_critique(response, step_num, "logic_flaw")
                    issues.extend(parsed_issues)
                    
            except Exception as e:
                self.logger.warning(f"️ LLM-based step analysis failed: {str(e)}")
        
        return issues
    
    async def _analyze_logical_flow(
        self, 
        chain_of_thought: List[Dict[str, Any]], 
        draft_content: str
    ) -> List[Dict[str, Any]]:
        """Analyze overall logical flow from CoT to draft"""
        
        issues = []
        
        if not self.llm_client:
            return issues
        
        try:
            # Create summary of reasoning chain
            cot_summary = "\n".join([
                f"Step {step.get('step', i+1)}: {step.get('thought', '')}"
                for i, step in enumerate(chain_of_thought)
            ])
            
            prompt = f"""
            Analyze the logical flow from reasoning steps to final draft:

            REASONING CHAIN:
            {cot_summary}

            FINAL DRAFT:
            {draft_content[:1000]}...

            Check for:
            1. Does the draft logically follow from the reasoning chain?
            2. Are there major gaps between reasoning and conclusions?
            3. Does the draft contradict any reasoning steps?
            4. Are key reasoning insights missing from the draft?

            If you find significant flow issues, respond in this format:
            ISSUE: [brief description]
            SEVERITY: [critical/high/medium/low]
            EXPLANATION: [detailed explanation]

            If the flow is generally sound, respond: "NO_MAJOR_ISSUES"
            """
            
            response = await self._call_llm(prompt, temperature=0.1)
            
            if response and "NO_MAJOR_ISSUES" not in response.upper():
                parsed_issues = self._parse_llm_critique(response, None, "logic_flaw")
                issues.extend(parsed_issues)
                
        except Exception as e:
            self.logger.warning(f"️ Logical flow analysis failed: {str(e)}")
        
        return issues
    
    async def _verify_factual_accuracy(
        self, 
        draft_content: str, 
        context: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Verify factual claims against provided context"""
        
        factual_issues = []
        
        if not context:
            self.logger.info("No context provided for fact-checking")
            return factual_issues
        
        try:
            # Extract key factual claims from draft
            claims = self._extract_factual_claims(draft_content)
            
            if not claims:
                self.logger.debug("No explicit factual claims found for verification")
                return factual_issues
            
            # Verify each claim against context
            for claim in claims:
                verification_result = await self._verify_single_claim(claim, context)
                if verification_result:
                    factual_issues.append(verification_result)
            
            self.logger.debug(f"Fact-checking found {len(factual_issues)} issues")
            
        except Exception as e:
            self.logger.error(f"Factual verification failed: {str(e)}")
            factual_issues.append({
                "type": "fact_contradiction",
                "severity": "medium",
                "description": f"Fact-checking failed due to error: {str(e)}",
                "claim": None
            })
        
        return factual_issues
    
    def _extract_factual_claims(self, content: str) -> List[str]:
        """Extract specific factual claims from content"""
        claims = []
        
        # Look for specific patterns that indicate factual claims
        patterns = [
            r"The value is (\d+\.?\d*)",
            r"The result is (\w+)",
            r"According to (.+?),",
            r"The formula is (.+?)[\.\n]",
            r"(\w+) equals (\w+)",
            r"The answer is (.+?)[\.\n]"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    claim = " ".join(match).strip()
                else:
                    claim = match.strip()
                
                if len(claim) > 5:  # Filter out very short matches
                    claims.append(claim)
        
        # Also extract sentences with definitive statements
        sentences = re.split(r'[.!?]+', content)
        for sentence in sentences:
            sentence = sentence.strip()
            if any(indicator in sentence.lower() for indicator in ['is', 'equals', 'equals to', 'the value', 'the result']):
                if 20 < len(sentence) < 200:  # Reasonable length
                    claims.append(sentence)
        
        return list(set(claims))  # Remove duplicates
    
    async def _verify_single_claim(
        self, 
        claim: str, 
        context: List[Dict[str, Any]]
    ) -> Dict[str, Any] | None:
        """Verify a single claim against context"""
        
        if not self.llm_client:
            return None
        
        try:
            # Create context summary for verification
            context_text = "\n".join([
                f"Source {i+1}: {item.get('text', item.get('content', ''))[:500]}"
                for i, item in enumerate(context[:5])  # Limit context to prevent overflow
            ])
            
            prompt = f"""
            Verify the following claim against the provided context:

            CLAIM TO VERIFY: {claim}

            CONTEXT SOURCES:
            {context_text}

            Determine:
            1. Is this claim explicitly supported by the context?
            2. Is this claim contradicted by the context?
            3. Is this claim not mentioned in the context at all?

            Respond in this format:
            VERIFICATION: [SUPPORTED/CONTRADICTED/NOT_MENTIONED]
            EVIDENCE: [specific quote from context if applicable]
            CONFIDENCE: [high/medium/low]

            If CONTRADICTED, also include:
            SEVERITY: [critical/high/medium/low]
            """
            
            response = await self._call_llm(prompt, temperature=0.1)
            
            if response and "CONTRADICTED" in response.upper():
                # Parse the contradiction details
                severity = "high"  # Default
                evidence = ""
                
                lines = response.split('\n')
                for line in lines:
                    if line.startswith('EVIDENCE:'):
                        evidence = line[9:].strip()
                    elif line.startswith('SEVERITY:'):
                        severity = line[9:].strip().lower()
                
                return {
                    "type": "fact_contradiction",
                    "severity": severity,
                    "claim": claim,
                    "description": f"Claim contradicted by provided context: {evidence}"
                }
            
        except Exception as e:
            self.logger.warning(f"️ Single claim verification failed: {str(e)}")
        
        return None
    
    async def _detect_hallucinations(
        self, 
        draft_content: str, 
        context: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Detect hallucinated information not supported by context"""
        
        hallucination_issues = []
        
        if not self.llm_client or not context:
            return hallucination_issues
        
        try:
            # Create comprehensive context summary
            context_summary = self._create_context_summary(context)
            
            prompt = f"""
            Analyze the draft for potential hallucinations - information that appears to be made up or not supported by the provided context.

            DRAFT CONTENT:
            {draft_content[:1500]}...

            AVAILABLE CONTEXT:
            {context_summary}

            Look for:
            1. Specific facts, figures, or formulas not in the context
            2. References to concepts not mentioned in the context  
            3. Made-up examples or case studies
            4. Invented technical terms or jargon
            5. Fabricated historical details or citations

            For each potential hallucination, respond in this format:
            HALLUCINATION: [specific content that appears fabricated]
            SEVERITY: [critical/high/medium/low]
            EXPLANATION: [why this appears to be hallucinated]

            If no clear hallucinations are detected, respond: "NO_HALLUCINATIONS_DETECTED"
            """
            
            response = await self._call_llm(prompt, temperature=0.1)
            
            if response and "NO_HALLUCINATIONS_DETECTED" not in response.upper():
                parsed_issues = self._parse_llm_critique(response, None, "hallucination")
                hallucination_issues.extend(parsed_issues)
            
            self.logger.debug(f"Hallucination detection found {len(hallucination_issues)} issues")
            
        except Exception as e:
            self.logger.error(f"Hallucination detection failed: {str(e)}")
        
        return hallucination_issues
    
    def _create_context_summary(self, context: List[Dict[str, Any]]) -> str:
        """Create a summary of available context for hallucination detection"""
        if not context:
            return "No context provided."
        
        summaries = []
        for i, item in enumerate(context[:8]):  # Limit to prevent prompt overflow
            text = item.get('text', item.get('content', ''))
            score = item.get('score', 'N/A')
            
            summary = f"Context {i+1} (Relevance: {score}):\n{text[:400]}..."
            summaries.append(summary)
        
        return "\n\n".join(summaries)
    
    def _parse_llm_critique(
        self, 
        response: str, 
        step_ref: int | None, 
        issue_type: str
    ) -> List[Dict[str, Any]]:
        """Parse LLM response into structured critique format"""
        
        issues = []
        
        try:
            # Split response into individual issues
            issue_blocks = re.split(r'\n(?=ISSUE:|HALLUCINATION:)', response)
            
            for block in issue_blocks:
                if not block.strip():
                    continue
                
                issue = {"type": issue_type}
                
                if step_ref is not None:
                    issue["step_ref"] = step_ref
                
                lines = block.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    
                    if line.startswith('ISSUE:') or line.startswith('HALLUCINATION:'):
                        issue["description"] = line.split(':', 1)[1].strip()
                    elif line.startswith('SEVERITY:'):
                        severity = line[9:].strip().lower()
                        if severity in self.severity_levels:
                            issue["severity"] = severity
                        else:
                            issue["severity"] = "medium"  # Default
                    elif line.startswith('EXPLANATION:'):
                        explanation = line[12:].strip()
                        if "description" in issue:
                            issue["description"] += f" - {explanation}"
                        else:
                            issue["description"] = explanation
                
                # Only add issues with valid descriptions
                if "description" in issue:
                    issues.append(issue)
            
        except Exception as e:
            self.logger.warning(f"️ Failed to parse LLM critique: {str(e)}")
            
            # Fallback: create a single issue from raw response
            if response and len(response) > 10:
                issues.append({
                    "type": issue_type,
                    "severity": "medium",
                    "description": response[:200] + "..." if len(response) > 200 else response,
                    "step_ref": step_ref
                })
        
        return issues
    
    def _assess_overall_quality(self, critiques: List[Dict[str, Any]]) -> str:
        """Assess overall quality based on critique severity"""
        
        if not critiques:
            return "acceptable"
        
        # Count issues by severity
        critical_count = len([c for c in critiques if c.get('severity') == 'critical'])
        high_count = len([c for c in critiques if c.get('severity') == 'high'])
        
        if critical_count > 0:
            return "major_revisions_required"
        elif high_count > 2:
            return "significant_revisions_required" 
        elif high_count > 0 or len(critiques) > 3:
            return "minor_revisions_suggested"
        else:
            return "acceptable_with_minor_issues"
    
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