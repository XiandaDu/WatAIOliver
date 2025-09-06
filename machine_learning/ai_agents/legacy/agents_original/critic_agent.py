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
        - Think methodically and document reasoning for each critique

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
            
            self.logger.info("\n" + "="*250)
            self.logger.info("CRITIC AGENT - DRAFT ANALYSIS")
            self.logger.info("="*250)
            self.logger.info(f"CoT steps: {len(chain_of_thought)}")
            self.logger.info(f"Context items: {len(context)}")
            self.logger.info(f"Draft length: {len(draft_content)} characters")
            
            # ULTRA VERBOSE: Show the actual content being analyzed
            self.logger.info(f"\n--- DRAFT CONTENT TO ANALYZE ---")
            self.logger.info(f"'{draft_content}'")
            
            self.logger.info(f"\n--- CONTEXT ITEMS FOR VERIFICATION ---")
            for i, ctx_item in enumerate(context[:3]):
                content = ctx_item.get('content', ctx_item.get('text', str(ctx_item)))
                self.logger.info(f"Context {i+1}: '{content}'")
            if len(context) > 3:
                self.logger.info(f"... and {len(context) - 3} more context items")
                
            self.logger.info(f"\n--- CHAIN OF THOUGHT STEPS ---")
            for i, step in enumerate(chain_of_thought[:3]):
                step_text = step.get('thought', str(step))
                self.logger.info(f"CoT Step {i+1}: '{step_text}...'")
            if len(chain_of_thought) > 3:
                self.logger.info(f"... and {len(chain_of_thought) - 3} more CoT steps")
            
            # Perform three core verification tasks in parallel
            critiques = []
            
            # Task 1: Logical Verification
            self.logger.info("\n" + "-"*250)
            self.logger.info("PHASE 1: LOGICAL CONSISTENCY VERIFICATION")
            self.logger.info("-"*250)
            logic_start = time.time()
            logic_critiques = await self._verify_logical_consistency(chain_of_thought, draft_content)
            logic_time = time.time() - logic_start
            self.logger.info(f"Logical verification completed in {logic_time:.2f}s")
            
            # Task 2: Factual Verification
            self.logger.info("\n" + "-"*250)
            self.logger.info("PHASE 2: FACTUAL ACCURACY VERIFICATION")
            self.logger.info("-"*250)
            fact_start = time.time()
            factual_issues = await self._verify_factual_accuracy(draft_content, context)
            fact_time = time.time() - fact_start
            self.logger.info(f"Factual verification completed in {fact_time:.2f}s")
            
            # Task 3: Hallucination Detection
            self.logger.info("\n" + "-"*250)
            self.logger.info("PHASE 3: HALLUCINATION DETECTION")
            self.logger.info("-"*250)
            halluc_start = time.time()
            hallucination_issues = await self._detect_hallucinations(draft_content, context)
            halluc_time = time.time() - halluc_start
            self.logger.info(f"Hallucination detection completed in {halluc_time:.2f}s")
            
            # Combine all critiques
            self.logger.info("\n" + "-"*250)
            self.logger.info("COMBINING ALL CRITIQUES")
            self.logger.info("-"*250)
            critiques.extend(logic_critiques)
            critiques.extend(factual_issues)
            critiques.extend(hallucination_issues)
            
            # Assess overall critique severity
            overall_assessment = self._assess_overall_quality(critiques)
            
            # ULTRA VERBOSE: Log final assessment details
            self.logger.info("\n" + "="*250)
            self.logger.info("FINAL CRITIC ASSESSMENT")
            self.logger.info("="*250)
            self.logger.info(f"TOTAL ISSUES FOUND: {len(critiques)}")
            
            # Break down by severity
            critical_count = len([c for c in critiques if c.get('severity') == 'critical'])
            high_count = len([c for c in critiques if c.get('severity') == 'high'])
            medium_count = len([c for c in critiques if c.get('severity') == 'medium'])
            low_count = len([c for c in critiques if c.get('severity') == 'low'])
            
            self.logger.info(f"CRITICAL: {critical_count}")
            self.logger.info(f"HIGH: {high_count}")
            self.logger.info(f"MEDIUM: {medium_count}")
            self.logger.info(f"LOW: {low_count}")
            
            # Break down by type
            logic_count = len([c for c in critiques if c.get('type') == 'logic_flaw'])
            fact_count = len([c for c in critiques if c.get('type') == 'fact_contradiction'])
            halluc_count = len([c for c in critiques if c.get('type') == 'hallucination'])
            
            self.logger.info(f"LOGICAL ISSUES: {logic_count}")
            self.logger.info(f"FACTUAL ISSUES: {fact_count}")
            self.logger.info(f"HALLUCINATION ISSUES: {halluc_count}")
            
            self.logger.info(f"OVERALL ASSESSMENT: {overall_assessment.upper()}")
            
            if critiques:
                self.logger.info(f"ISSUE DETAILS:")
                for i, issue in enumerate(critiques, 1):
                    severity = issue.get('severity', 'unknown').upper()
                    issue_type = issue.get('type', 'unknown').upper()
                    desc = issue.get('description', 'no description')
                    self.logger.info(f"   {i}. [{severity}] {issue_type}: {desc}...")
            else:
                self.logger.info(f"NO ISSUES DETECTED - DRAFT IS CLEAN!")
            
            self.logger.info("\n" + "="*250)
            self.logger.info("CRITIC ANALYSIS COMPLETE")
            self.logger.info("="*250)
            
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
                
                # ULTRA VERBOSE: Log evaluation decision
                self.logger.info(f"LOGICAL STEP {step_num} EVALUATION:")
                if response and "NO_ISSUES" not in response.upper():
                    self.logger.info(f"ISSUES DETECTED in step {step_num}")
                    # Parse LLM response for issues
                    parsed_issues = self._parse_llm_critique(response, step_num, "logic_flaw")
                    self.logger.info(f"PARSED {len(parsed_issues)} logical issues from response")
                    for issue in parsed_issues:
                        self.logger.info(f"   • {issue.get('severity', 'unknown').upper()}: {issue.get('description', 'no description')}")
                    issues.extend(parsed_issues)
                else:
                    self.logger.info(f"NO LOGICAL ISSUES found in step {step_num}")
                    
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

======= REASONING CHAIN START =======
{cot_summary}
======= REASONING CHAIN END =======

======= FINAL DRAFT START =======
{draft_content}
======= FINAL DRAFT END =======

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
            
            # ULTRA VERBOSE: Log the full prompt being sent to LLM
            self.logger.info(f"\n" + "="*250)
            self.logger.info(f"LOGICAL FLOW ANALYSIS - FULL PROMPT TO LLM")
            self.logger.info(f"="*250)
            self.logger.info(f"PROMPT CONTENT:")
            self.logger.info(f"{prompt}")
            self.logger.info(f"="*250)
            
            response = await self._call_llm(prompt, temperature=0.1)
            
            self.logger.info(f"\nLLM RESPONSE FOR LOGICAL FLOW:")
            self.logger.info(f"{response}")
            self.logger.info(f"="*250)
            
            # ULTRA VERBOSE: Log flow evaluation decision
            self.logger.info(f"LOGICAL FLOW EVALUATION:")
            if response and "NO_MAJOR_ISSUES" not in response.upper():
                self.logger.info(f"LOGICAL FLOW ISSUES DETECTED")
                parsed_issues = self._parse_llm_critique(response, None, "logic_flaw")
                self.logger.info(f"PARSED {len(parsed_issues)} flow issues from response")
                for issue in parsed_issues:
                    self.logger.info(f"   • {issue.get('severity', 'unknown').upper()}: {issue.get('description', 'no description')}")
                issues.extend(parsed_issues)
            else:
                self.logger.info(f"LOGICAL FLOW IS SOUND")
                
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
            
            # ULTRA VERBOSE: Log extracted claims
            self.logger.info(f"FACTUAL CLAIMS EXTRACTION:")
            self.logger.info(f"EXTRACTED {len(claims)} factual claims from draft:")
            for i, claim in enumerate(claims, 1):
                self.logger.info(f"   {i}. '{claim}'")
            
            if not claims:
                self.logger.info("️ NO EXPLICIT FACTUAL CLAIMS FOUND for verification")
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
                f"Source {i+1}: {item.get('text', item.get('content', ''))}"
                for i, item in enumerate(context[:5])  # Limit context to prevent overflow
            ])
            
            # ULTRA VERBOSE: Show exactly what context is being used for verification
            self.logger.info(f"\n--- FACT-CHECKING CLAIM AGAINST CONTEXT ---")
            self.logger.info(f"Claim: '{claim}'")
            self.logger.info(f"Context sources ({len(context)} total, showing first 5):")
            self.logger.info(f"'{context_text}'")
            
            prompt = f"""
            Verify the following claim against the provided context:

======= CLAIM TO VERIFY START =======
{claim}
======= CLAIM TO VERIFY END =======

======= CONTEXT SOURCES START =======
{context_text}
======= CONTEXT SOURCES END =======

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
            
            # ULTRA VERBOSE: Log the full fact-check prompt
            self.logger.info(f"\n" + "="*250)
            self.logger.info(f"FACT-CHECK ANALYSIS - FULL PROMPT TO LLM")
            self.logger.info(f"="*250)
            self.logger.info(f"CLAIM: '{claim}'")
            self.logger.info(f"PROMPT CONTENT:")
            self.logger.info(f"{prompt}")
            self.logger.info(f"="*250)
            
            response = await self._call_llm(prompt, temperature=0.1)
            
            self.logger.info(f"\nLLM RESPONSE FOR FACT-CHECK:")
            self.logger.info(f"{response}")
            self.logger.info(f"="*250)
            
            # ULTRA VERBOSE: Log fact-check evaluation
            self.logger.info(f"FACT-CHECK EVALUATION for claim: '{claim}'")
            if response and "CONTRADICTED" in response.upper():
                self.logger.info(f"FACTUAL CONTRADICTION DETECTED")
                # Parse the contradiction details
                severity = "high"  # Default
                evidence = ""
                
                lines = response.split('\n')
                for line in lines:
                    if line.startswith('EVIDENCE:'):
                        evidence = line[9:].strip()
                    elif line.startswith('SEVERITY:'):
                        severity = line[9:].strip().lower()
                
                self.logger.info(f"CONTRADICTION: Severity={severity.upper()}, Evidence='{evidence}'")
                return {
                    "type": "fact_contradiction",
                    "severity": severity,
                    "claim": claim,
                    "description": f"Claim contradicted by provided context: {evidence}"
                }
            else:
                self.logger.info(f"FACT-CHECK PASSED for claim")
            
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
            
            # ULTRA VERBOSE: Show exactly what's being checked for hallucinations
            self.logger.info(f"\n--- HALLUCINATION DETECTION INPUT ---")
            self.logger.info(f"Draft content ({len(draft_content)} chars): '{draft_content}'")
            self.logger.info(f"Context summary ({len(context_summary)} chars): '{context_summary}'")
            
            prompt = f"""
            Analyze the draft for potential hallucinations - information that appears to be made up or not supported by the provided context.

            DRAFT CONTENT:
            {draft_content}

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
            
            # ULTRA VERBOSE: Log hallucination evaluation
            self.logger.info(f"HALLUCINATION DETECTION EVALUATION:")
            # Check if response contains actual hallucination reports (not just the "no hallucinations" phrase)
            has_severity = "SEVERITY:" in response.upper() if response else False
            has_hallucination_tag = "HALLUCINATION:" in response.upper() if response else False
            
            if response and (has_severity or has_hallucination_tag):
                self.logger.info(f"HALLUCINATIONS DETECTED")
                parsed_issues = self._parse_llm_critique(response, None, "hallucination")
                self.logger.info(f"PARSED {len(parsed_issues)} hallucination issues from response")
                for issue in parsed_issues:
                    self.logger.info(f"   • {issue.get('severity', 'unknown').upper()}: {issue.get('description', 'no description')}")
                hallucination_issues.extend(parsed_issues)
            else:
                self.logger.info(f"NO HALLUCINATIONS DETECTED")
            
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
            
            summary = f"Context {i+1} (Relevance: {score}):\n{text}"
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
            # ULTRA VERBOSE: Log what we're trying to parse
            self.logger.info(f"PARSING LLM RESPONSE:")
            self.logger.info(f"Response length: {len(response)} chars")
            self.logger.info(f"Looking for SEVERITY: {('SEVERITY:' in response.upper())}")
            self.logger.info(f"Looking for HALLUCINATION: {('HALLUCINATION:' in response.upper())}")
            
            # Handle different response formats
            if "SEVERITY:" in response.upper():
                # Format: explanatory text with SEVERITY: embedded
                issue = {"type": issue_type}
                
                if step_ref is not None:
                    issue["step_ref"] = step_ref
                
                lines = response.strip().split('\n')
                description_parts = []
                
                for line in lines:
                    line = line.strip()
                    
                    if line.startswith('ISSUE:') or line.startswith('HALLUCINATION:'):
                        description_parts.append(line.split(':', 1)[1].strip())
                    elif line.startswith('SEVERITY:'):
                        severity = line[9:].strip().lower()
                        if severity in self.severity_levels:
                            issue["severity"] = severity
                        else:
                            issue["severity"] = "medium"
                        self.logger.info(f"Found severity: {severity}")
                    elif line.startswith('EXPLANATION:'):
                        explanation = line[12:].strip()
                        description_parts.append(explanation)
                    elif line and not line.startswith('CONFIDENCE:') and len(line) > 20:
                        # Include substantial descriptive lines
                        description_parts.append(line)
                
                # Combine description parts
                if description_parts:
                    issue["description"] = " - ".join(description_parts[:2])  # Limit to first 2 parts
                else:
                    issue["description"] = "Issue detected but description unclear"
                
                if not issue.get("severity"):
                    issue["severity"] = "medium"  # Default
                    
                issues.append(issue)
                self.logger.info(f"Created issue: {issue.get('severity', 'unknown').upper()} - {issue.get('description', '')}")
            
            else:
                # Original format: Split response into individual issues
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
                    "description": response,
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
        """Call LLM with error handling and ultra-verbose debugging"""
        
        # ULTRA VERBOSE: Log the exact prompt being sent
        self.logger.info("\n" + "="*250)
        self.logger.info("CRITIC LLM CALL START")
        self.logger.info("="*250)
        self.logger.info(f"Temperature: {temperature}")
        self.logger.info(f"\nPROMPT:")
        self.logger.info("-"*250)
        self.logger.info(prompt)
        self.logger.info("-"*250)
        
        try:
            if hasattr(self.llm_client, 'get_llm_client'):
                llm = self.llm_client.get_llm_client()
                response = await llm.ainvoke(prompt, temperature=temperature)
                response_text = response.content if hasattr(response, 'content') else str(response)
            else:
                # Fallback for different LLM client interfaces
                response = await self.llm_client.generate(prompt, temperature=temperature)
                response_text = str(response)
            
            # ULTRA VERBOSE: Log the exact response received
            self.logger.info(f"\nLLM RESPONSE:")
            self.logger.info("-"*250)
            self.logger.info(response_text)
            self.logger.info("-"*250)
            self.logger.info("\n" + "="*250)
            self.logger.info("CRITIC LLM CALL COMPLETE")
            self.logger.info("="*250)
            
            return response_text
            
        except Exception as e:
            self.logger.error(f"LLM call FAILED: {str(e)}")
            self.logger.info("=== CRITIC LLM CALL FAILED ===")
            return "" 