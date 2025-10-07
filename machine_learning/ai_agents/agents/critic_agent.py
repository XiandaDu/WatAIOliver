"""
Critic Agent - LangChain Implementation with PARALLEL VERIFICATION

Critical verifier that performs ruthless, evidence-based review of drafts.
Uses independent parallel verification for logic, facts, and hallucinations.
"""

import time
import json
import asyncio
from typing import List, Dict, Any
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain.tools import Tool
from pydantic import BaseModel, Field

from ai_agents.state import WorkflowState, Critique, log_agent_execution
from ai_agents.utils import create_langchain_llm

# Import simple logger for backup logging
try:
    from ai_agents.simple_logger import simple_log
except:
    class SimpleLogFallback:
        def info(self, msg, data=None): pass
        def error(self, msg, data=None): pass
    simple_log = SimpleLogFallback()


class CritiqueOutput(BaseModel):
    """Structured critique output"""
    critiques: List[Dict[str, Any]] = Field(description="List of identified issues")
    overall_assessment: str = Field(description="Overall quality assessment")
    severity_score: float = Field(description="Overall severity score 0-1")


class CriticAgent:
    """
    Critical Verifier using LangChain chains with parallel execution.
    
    Performs three INDEPENDENT types of verification in parallel:
    1. Logical flow verification - checks reasoning coherence
    2. Factual accuracy checking - verifies claims against context
    3. Hallucination detection - identifies unsupported content
    
    All three run simultaneously and results are synthesized.
    """
    
    def __init__(self, context):
        self.context = context
        self.logger = context.logger.getChild("critic")
        self.llm_client = context.llm_client
        self.llm = create_langchain_llm(self.llm_client)
        
        # Setup verification chains
        self._setup_chains()
        
        # Create verification tools
        self._setup_tools()
    
    def _setup_chains(self):
        """Setup INDEPENDENT LangChain chains for parallel verification"""
        
        # Independent Logic Verification Chain
        self.logic_verification_chain = LLMChain(
            llm=self.llm,
            prompt=ChatPromptTemplate.from_messages([
                ("system", """You are a logic verifier that analyzes the ACTUAL content provided.
                
CRITICAL INSTRUCTIONS:
1. You must read and analyze ONLY the actual draft content provided below
2. Do NOT generate fake examples about "Event A caused Event B" or "X is the largest Y"
3. Do NOT make up problems that don't exist in the actual draft
4. Do NOT use template responses or placeholder critiques
5. If there are NO actual logical issues in the draft, return an empty logic_issues array

Your job is to find REAL logical problems in the ACTUAL text provided."""),
                ("human", """Query: {query}

===============================================================================
>>> SOLUTION DRAFT TO ANALYZE (ONLY THIS CONTENT CAN BE CRITICIZED) <<<
===============================================================================
{draft}
===============================================================================
>>> END OF DRAFT <<<
===============================================================================

>>> CHAIN OF THOUGHT TO ANALYZE <<<
===============================================================================
{cot}
===============================================================================
>>> END OF CHAIN OF THOUGHT <<<
===============================================================================

CRITICAL: Analyze ONLY the draft and chain of thought above. Look for REAL logical issues such as:
- Contradictory statements within the draft
- Logical leaps in the reasoning chain
- Assumptions that aren't supported by prior steps
- Conclusions that don't follow from premises

STEP REFERENCE INSTRUCTIONS:
- The Chain of Thought above has numbered steps like "Step 1:", "Step 2:", etc.
- When you find a logical issue, identify which step number it relates to
- If the issue relates to "Step 3:", set step_ref to 3
- If the issue spans multiple steps, use the primary step number
- If the issue is not tied to a specific step, set step_ref to null

Do NOT make up fake issues. Analyze only what is actually written in the draft above.

Return valid JSON:
{{
    "logic_issues": [
        {{
            "step_ref": <step_number_from_CoT_or_null>,
            "severity": "low/medium/high/critical",
            "description": "<describe the actual logical problem found in the text>",
            "problematic_content": "<exact quote from the actual draft>"
        }}
    ],
    "logic_summary": "<summary based on actual analysis>",
    "areas_of_concern": []
}}

If you find NO logical issues in the actual draft, return:
{{
    "logic_issues": [],
    "logic_summary": "No significant logical issues found",
    "areas_of_concern": []
}}""")
            ]),
            output_key="logic_analysis"
        )
        
        # Independent Fact Checking Chain
        self.fact_checking_chain = LLMChain(
            llm=self.llm,
            prompt=ChatPromptTemplate.from_messages([
                ("system", """You are a fact checker that verifies ACTUAL claims in the provided draft.
                
CRITICAL INSTRUCTIONS:
1. Read the actual draft content carefully
2. Identify specific factual claims made in the draft
3. Check ONLY those actual claims against the provided context
4. Do NOT generate fake fact-check examples like "X is the largest Y"
5. Do NOT invent factual contradictions that don't exist
6. If all facts in the draft are supported by the context, return empty fact_issues array

Focus on verifying REAL claims from the ACTUAL draft."""),
                ("human", """Query: {query}

===============================================================================
>>> DRAFT TO ANALYZE (ONLY CONTENT FROM THIS SECTION CAN BE CRITICIZED) <<<
===============================================================================
{draft}
===============================================================================
>>> END OF DRAFT - DO NOT CRITICIZE CONTENT BELOW THIS LINE <<<
===============================================================================

>>> REFERENCE CONTEXT (USE ONLY TO VERIFY CLAIMS FROM DRAFT ABOVE) <<<
===============================================================================
{context}
===============================================================================
>>> END OF CONTEXT - THIS IS REFERENCE MATERIAL, NOT CONTENT TO CRITICIZE <<<
===============================================================================

CRITICAL INSTRUCTIONS:
1. ONLY analyze claims made in the DRAFT section above
2. NEVER criticize or fact-check content from the CONTEXT section
3. The CONTEXT is your reference material to verify DRAFT claims
4. If you see content in CONTEXT, it is CORRECT - do not question it
5. Only report issues where the DRAFT contradicts or lacks support from CONTEXT

WORKFLOW:
1. Read the DRAFT section and identify factual claims
2. For each DRAFT claim, check if it's supported by the CONTEXT
3. Only flag DRAFT claims that contradict or lack support in CONTEXT

STEP REFERENCE INSTRUCTIONS:
- The Chain of Thought above has numbered steps like "Step 1:", "Step 2:", etc.
- When you find a factual issue, identify which step number it relates to
- If the issue relates to "Step 3:", set step_ref to 3
- If the issue spans multiple steps, use the primary step number
- If the issue is not tied to a specific step, set step_ref to null

Return valid JSON:
{{
    "fact_issues": [
        {{
            "claim": "<exact claim found in the actual draft>",
            "step_ref": <step_number_from_CoT_or_null>,
            "severity": "low/medium/high/critical",
            "description": "<why this claim is incorrect or unsupported based on context>"
        }}
    ],
    "fact_summary": "<summary of fact-checking results>",
    "verified_facts": ["<list of facts that were correctly stated>"]
}}

If the draft's claims are supported by context, return:
{{
    "fact_issues": [],
    "fact_summary": "All facts verified against context",
    "verified_facts": []
}}""")
            ]),
            output_key="fact_analysis"
        )
        
        # Independent Hallucination Detection Chain
        self.hallucination_chain = LLMChain(
            llm=self.llm,
            prompt=ChatPromptTemplate.from_messages([
                ("system", """You are a hallucination detector that identifies ACTUAL unsupported content.
                
CRITICAL INSTRUCTIONS:
1. Read the actual draft content carefully
2. Compare it against the provided context sources
3. Identify content in the draft that has NO support in the context
4. Do NOT make up fake hallucinations about "quantum tunneling" or "Mars colonies"
5. Do NOT invent problems that don't exist in the actual draft
6. If the draft is properly supported by context, return empty hallucinations array

Only flag content that is genuinely unsupported."""),
                ("human", """Query: {query}

===============================================================================
>>> DRAFT TO CHECK FOR HALLUCINATIONS (ONLY THIS CONTENT CAN BE FLAGGED) <<<
===============================================================================
{draft}
===============================================================================
>>> END OF DRAFT - DO NOT FLAG CONTENT BELOW THIS LINE <<<
===============================================================================

>>> REFERENCE CONTEXT (USE TO VERIFY DRAFT CLAIMS ARE SUPPORTED) <<<
===============================================================================
{context}
===============================================================================
>>> END OF CONTEXT - THIS IS REFERENCE MATERIAL, NOT CONTENT TO FLAG <<<
===============================================================================

CRITICAL INSTRUCTIONS:
1. ONLY flag content from the DRAFT section above
2. NEVER flag content from the CONTEXT section - it is reference material
3. The CONTEXT is your source of truth to verify DRAFT claims
4. Only flag DRAFT content that has NO support in the CONTEXT

WORKFLOW:
1. Read the DRAFT section and identify major claims/concepts
2. For each DRAFT claim, check if it appears anywhere in the CONTEXT
3. Only flag DRAFT content that is completely absent from CONTEXT
4. Do NOT flag reasonable inferences or explanations derived from CONTEXT

STEP REFERENCE INSTRUCTIONS:
- The Chain of Thought above has numbered steps like "Step 1:", "Step 2:", etc.
- When you find a hallucination, identify which step number it relates to
- If the issue relates to "Step 3:", set step_ref to 3
- If the issue spans multiple steps, use the primary step number
- If the issue is not tied to a specific step, set step_ref to null

Return valid JSON:
{{
    "hallucinations": [
        {{
            "content": "<actual unsupported content from draft>",
            "step_ref": <step_number_from_CoT_or_null>,
            "severity": "low/medium/high/critical",
            "reason": "<why this content is not supported by context>",
            "suggested_fix": "<what should be there based on context>"
        }}
    ],
    "hallucination_summary": "<summary of findings>"
}}

If the draft IS supported by context, return:
{{
    "hallucinations": [],
    "hallucination_summary": "Draft content is supported by context"
}}""")
            ]),
            output_key="hallucination_analysis"
        )
        
        # Synthesis Chain - Combines all independent verification results
        self.synthesis_chain = LLMChain(
            llm=self.llm,
            prompt=ChatPromptTemplate.from_messages([
                ("system", """You are a JSON extraction agent. Your ONLY job is to extract existing issues from analysis results.

ABSOLUTE RULES:
1. Look at the analysis results provided
2. If ALL analysis results show empty arrays (like "fact_issues": [], "logic_issues": [], "hallucinations": []), then output empty critiques array
3. NEVER generate example critiques like "Event A", "Person Z", "Mars colonies", etc.
4. NEVER create fake problems that don't exist in the analysis results
5. Only extract issues that are explicitly listed in the analysis results
6. CRITICAL: Issues must be about problems found in the DRAFT, not about reference context being "wrong"

CONTEXT CONFUSION PREVENTION:
- If an analysis mentions context content as problematic, IGNORE IT
- Only extract issues where the DRAFT contradicts or lacks support from context
- Context content is reference material and should NEVER be criticized

If you see empty analysis results, you MUST output an empty critiques array."""),
                ("human", """VERIFICATION ANALYSIS RESULTS:

Logic Analysis:
{logic_analysis}

Fact-Checking Analysis:
{fact_analysis}

Hallucination Analysis:
{hallucination_analysis}

TASK: Read the analysis results above and extract ONLY the actual issues found.

STEP 1: Check if all analysis results are empty:
- If Logic Analysis shows "logic_issues": [] AND
- If Fact Analysis shows "fact_issues": [] AND  
- If Hallucination Analysis shows "hallucinations": []
THEN output: {{"critiques": [], "overall_assessment": "No issues found", "severity_score": 0.1}}

STEP 2: If any analysis found actual issues, extract them exactly as written.

EXTRACTION RULES:
- For logic_issues: use type="logic_flaw", extract step_ref, description. claim is null.
- For fact_issues: use type="fact_contradiction", extract step_ref, description, claim.
- For hallucinations: use type="hallucination", extract step_ref, description. claim is null.

DO NOT GENERATE FAKE EXAMPLES. DO NOT USE TEMPLATES.

Required JSON format:
{{
    "critiques": [
        {{
            "type": "logic_flaw/fact_contradiction/hallucination",
            "severity": "low/medium/high/critical",
            "description": "<EXACT description from analysis above>",
            "step_ref": <step_ref_from_analysis_or_null>,
            "claim": "<EXACT claim from analysis or null>"
        }}
    ],
    "overall_assessment": "<based on ACTUAL findings>",
    "severity_score": <0.0-1.0>
}}

Output ONLY the JSON. Do NOT create fake critiques.""")
            ]),
            output_key="final_critique"
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
            simple_log.info("="*250)
            self.logger.info(f"CRITIC AGENT - ROUND {state['current_round']}")
            simple_log.info(f"CRITIC AGENT - ROUND {state['current_round']}")
            self.logger.info("="*250)
            simple_log.info("="*250)
            simple_log.info("CRITIC START", {
                "round": state['current_round'],
                "draft_id": state.get('draft_content', {}).get('draft_id', 'unknown')
            })
            
            draft = state["draft"]
            query = state["query"]
            context = state["retrieval_results"]
            
            if not draft:
                raise ValueError("No draft to critique")
            
            self.logger.info(f"Critiquing draft: {draft['draft_id']}")
            simple_log.info(f"Critiquing draft: {draft['draft_id']}")
            
            # Create structured input matching Strategist output format
            structured_draft_input = {
                "draft_id": draft["draft_id"],
                "draft_content": draft["content"],
                "chain_of_thought": draft["chain_of_thought"]
            }
            
            context_str = self._format_context(context)
            
            # RUN INDEPENDENT CHAINS IN PARALLEL
            self.logger.info("Running PARALLEL critique pipeline...")
            simple_log.info("Running PARALLEL critique pipeline...")
            self.logger.info("  • Logic Verification (independent)")
            simple_log.info("  • Logic Verification (independent)")
            self.logger.info("  • Fact Checking (independent)")  
            simple_log.info("  • Fact Checking (independent)")
            self.logger.info("  • Hallucination Detection (independent)")
            simple_log.info("  • Hallucination Detection (independent)")
            self.logger.info("  → All results combined in Synthesis")
            simple_log.info("  → All results combined in Synthesis")
            
            # Execute all verification chains in parallel
            try:
                # Prepare inputs for all chains using structured format
                base_inputs = {
                    "query": query,
                    "draft": draft["content"],
                    "cot": self._format_cot(draft["chain_of_thought"]),
                    "context": context_str
                }
                
                self.logger.info("="*250)
                simple_log.info("="*250)
                self.logger.info("LLM INPUT - PARALLEL VERIFICATION")
                simple_log.info("LLM INPUT - PARALLEL VERIFICATION")
                self.logger.info("="*250)
                simple_log.info("="*250)
                # Format the structured input for logging (matching Strategist format)
                try:
                    log_input = {
                        "query": query,
                        "draft_to_critique": structured_draft_input,
                        "retrieval_context": context if isinstance(context, list) else [],  # Show all retrieval results
                        "total_context_sources": len(context) if isinstance(context, list) else len([line for line in context_str.split('\n') if line.startswith('[Source')]),
                        "context_length": len(context_str)
                    }
                    
                    formatted_inputs = json.dumps(log_input, indent=2)
                    self.logger.info(f"Verification inputs (structured format):\n{formatted_inputs}")
                    simple_log.info(f"Verification inputs (structured format):\n{formatted_inputs}")
                except:
                    self.logger.info(f"Verification inputs: {base_inputs}")
                    simple_log.info(f"Verification inputs: {base_inputs}")
                self.logger.info("="*250)
                simple_log.info("="*250)
                
                # Run all three verification chains in parallel
                self.logger.info("Executing parallel verification chains...")
                simple_log.info("Executing parallel verification chains...")
                
                # Create async tasks for parallel execution
                async def run_chain_async(chain, inputs, chain_name):
                    """Helper to run chain asynchronously with proper debugging and fail-fast."""
                    self.logger.info("="*250)
                    simple_log.info("="*250)
                    self.logger.info(f"CHAIN EXECUTION: {chain_name.upper()}")
                    simple_log.info(f"CHAIN EXECUTION: {chain_name.upper()}")
                    self.logger.info("="*250)
                    simple_log.info("="*250)
                    
                    # ============================================================
                    # CRITICAL DEBUG SECTION - OUTSIDE TRY BLOCK
                    # ============================================================
                    
                    # 1. Debug what the chain object actually is
                    self.logger.info(f"🔍 CHAIN OBJECT DEBUG:")
                    simple_log.info(f"🔍 CHAIN OBJECT DEBUG:")
                    self.logger.info(f"   - Chain type: {type(chain)}")
                    simple_log.info(f"   - Chain type: {type(chain)}")
                    self.logger.info(f"   - Chain class: {chain.__class__.__name__}")
                    simple_log.info(f"   - Chain class: {chain.__class__.__name__}")
                    self.logger.info(f"   - Has prompt: {hasattr(chain, 'prompt')}")
                    simple_log.info(f"   - Has prompt: {hasattr(chain, 'prompt')}")
                    self.logger.info(f"   - Has output_key: {hasattr(chain, 'output_key')}")
                    simple_log.info(f"   - Has output_key: {hasattr(chain, 'output_key')}")
                    if hasattr(chain, 'output_key'):
                        self.logger.info(f"   - Output key value: {chain.output_key}")
                        simple_log.info(f"   - Output key value: {chain.output_key}")
                    
                    # 2. Debug the inputs
                    self.logger.info(f"🔍 INPUTS DEBUG:")
                    simple_log.info(f"🔍 INPUTS DEBUG:")
                    self.logger.info(f"   - Input type: {type(inputs)}")
                    simple_log.info(f"   - Input type: {type(inputs)}")
                    self.logger.info(f"   - Input keys: {list(inputs.keys())}")
                    simple_log.info(f"   - Input keys: {list(inputs.keys())}")
                    for key in inputs.keys():
                        val_preview = str(inputs[key])  # Full value
                        self.logger.info(f"   - {key}: {val_preview}...")
                        simple_log.info(f"   - {key}: {val_preview}...")
                    
                    # 3. Extract and validate expected variables OUTSIDE try block
                    expected_vars = []
                    if hasattr(chain, 'prompt') and hasattr(chain.prompt, 'input_variables'):
                        expected_vars = chain.prompt.input_variables
                        self.logger.info(f"🔍 TEMPLATE VARIABLES:")
                        simple_log.info(f"🔍 TEMPLATE VARIABLES:")
                        self.logger.info(f"   - Expected: {expected_vars}")
                        simple_log.info(f"   - Expected: {expected_vars}")
                    else:
                        self.logger.error(f"❌ CHAIN HAS NO PROMPT OR INPUT_VARIABLES!")
                        self.logger.error(f"   - Chain attributes: {dir(chain)}")  # Show all attributes
                        raise ValueError(f"Chain {chain_name} has no prompt.input_variables attribute!")
                    
                    # 4. Check variable matching OUTSIDE try block
                    self.logger.info(f"🔍 VARIABLE MATCHING:")
                    simple_log.info(f"🔍 VARIABLE MATCHING:")
                    missing_vars = []
                    available_vars = []
                    for var in expected_vars:
                        if var in inputs:
                            self.logger.info(f"   ✓ {var} - FOUND in inputs")
                            simple_log.info(f"   ✓ {var} - FOUND in inputs")
                            available_vars.append(var)
                        else:
                            self.logger.error(f"   ✗ {var} - MISSING from inputs!")
                            missing_vars.append(var)
                    
                    # 5. Build call_kwargs OUTSIDE try block
                    call_kwargs = {k: inputs[k] for k in expected_vars if k in inputs}
                    
                    # 6. FAIL FAST if there's a problem
                    if not call_kwargs:
                        self.logger.error(f"❌ FATAL: No matching variables found!")
                        self.logger.error(f"   Chain expects: {expected_vars}")
                        self.logger.error(f"   Inputs has: {list(inputs.keys())}")
                        raise ValueError(f"Cannot invoke {chain_name}: no matching variables between template {expected_vars} and inputs {list(inputs.keys())}")
                    
                    if missing_vars:
                        self.logger.error(f"❌ FATAL: Required variables missing!")
                        self.logger.error(f"   Missing: {missing_vars}")
                        raise ValueError(f"Cannot invoke {chain_name}: missing required variables {missing_vars}")
                    
                    # ============================================================
                    # LOG THE ACTUAL PROMPT (for debugging)
                    # ============================================================
                    try:
                        prompt_val = chain.prompt.format_prompt(**call_kwargs)
                        messages = prompt_val.to_messages()
                        self.logger.info(">>> ACTUAL COMPLETE PROMPT BEING SENT TO LLM <<<")
                        simple_log.info(">>> ACTUAL COMPLETE PROMPT BEING SENT TO LLM <<<")
                        self.logger.info("START_PROMPT" + "="*240)
                        simple_log.info("START_PROMPT" + "="*240)
                        for msg in messages:
                            self.logger.info(f"Message: {msg.content}")
                            simple_log.info(f"Message: {msg.content}")
                        self.logger.info("END_PROMPT" + "="*242)
                        simple_log.info("END_PROMPT" + "="*242)
                        self.logger.info(f"Total prompt length: {sum(len(m.content) for m in messages)} characters")
                        simple_log.info(f"Total prompt length: {sum(len(m.content) for m in messages)} characters")
                    except Exception as e:
                        self.logger.error(f"Could not format prompt for logging: {e}")
                    
                    self.logger.info("="*250)
                    simple_log.info("="*250)
                    
                    # ============================================================
                    # INVOKE THE CHAIN - NO FALLBACKS, FAIL FAST
                    # ============================================================
                    try:
                        self.logger.info(f"📞 Calling {chain_name}.arun() with args: {sorted(call_kwargs.keys())}")
                        simple_log.info(f"📞 Calling {chain_name}.arun() with args: {sorted(call_kwargs.keys())}")
                        
                        # Build the explicit call based on exact variables
                        if set(call_kwargs) == {"query", "draft", "cot"}:
                            raw_output = await chain.arun(
                                query=call_kwargs["query"],
                                draft=call_kwargs["draft"],
                                cot=call_kwargs["cot"]
                            )
                        elif set(call_kwargs) == {"query", "draft", "context"}:
                            raw_output = await chain.arun(
                                query=call_kwargs["query"],
                                draft=call_kwargs["draft"],
                                context=call_kwargs["context"]
                            )
                        elif set(call_kwargs) == {"query", "draft"}:
                            raw_output = await chain.arun(
                                query=call_kwargs["query"],
                                draft=call_kwargs["draft"]
                            )
                        else:
                            # NO FALLBACK - FAIL FAST
                            raise ValueError(f"Unsupported argument combination: {set(call_kwargs)}. Add explicit support for this pattern.")
                        
                        # Wrap output
                        raw_result = {chain.output_key: raw_output} if hasattr(chain,'output_key') else {'text': raw_output}
                        
                    except Exception as e:
                        self.logger.error(f"❌ Chain {chain_name} execution FAILED!")
                        self.logger.error(f"   Error: {e}")
                        self.logger.error(f"   Error type: {type(e).__name__}")
                        import traceback
                        self.logger.error(f"   Traceback:\n{traceback.format_exc()}")
                        raise  # FAIL FAST - no silent failures

                    # ------------------------------------------------------------------
                    # 4) Log FULL LLM response
                    # ------------------------------------------------------------------
                    self.logger.info("="*250)
                    simple_log.info("="*250)
                    self.logger.info(f"LLM OUTPUT - {chain_name.upper()}")
                    simple_log.info(f"LLM OUTPUT - {chain_name.upper()}")
                    self.logger.info("="*250)
                    simple_log.info("="*250)
                    self.logger.info(">>> ACTUAL COMPLETE RESPONSE FROM LLM <<<")
                    simple_log.info(">>> ACTUAL COMPLETE RESPONSE FROM LLM <<<")
                    self.logger.info("START_RESPONSE" + "="*236)
                    simple_log.info("START_RESPONSE" + "="*236)
                    self.logger.info(str(raw_output))
                    simple_log.info(str(raw_output))
                    self.logger.info("END_RESPONSE" + "="*238)
                    simple_log.info("END_RESPONSE" + "="*238)
                    self.logger.info(f"Total response length: {len(str(raw_output))} characters")
                    simple_log.info(f"Total response length: {len(str(raw_output))} characters")

                    return raw_result
                
                # Execute all three chains in parallel
                logic_task = run_chain_async(self.logic_verification_chain, base_inputs, "Logic Verification")
                fact_task = run_chain_async(self.fact_checking_chain, base_inputs, "Fact Checking")
                hallucination_task = run_chain_async(self.hallucination_chain, base_inputs, "Hallucination Detection")
                
                # Wait for all chains to complete
                try:
                    logic_result, fact_result, hallucination_result = await asyncio.gather(
                        logic_task, fact_task, hallucination_task
                    )
                except Exception as e:
                    self.logger.error(f"Error running parallel chains: {e}")
                    # Return empty results if chains fail
                    logic_result = {'logic_analysis': '{"logic_issues": [], "logic_summary": "Chain failed", "areas_of_concern": []}'}
                    fact_result = {'fact_analysis': '{"fact_issues": [], "fact_summary": "Chain failed", "verified_facts": []}'}
                    hallucination_result = {'hallucination_analysis': '{"hallucinations": [], "hallucination_summary": "Chain failed"}'}
                
                self.logger.info("="*250)
                simple_log.info("="*250)
                self.logger.info("PARALLEL VERIFICATION RESULTS")
                simple_log.info("PARALLEL VERIFICATION RESULTS")
                self.logger.info("="*250)
                simple_log.info("="*250)
                
                # Debug what we actually got back
                self.logger.info(f"Logic result type: {type(logic_result)}, keys: {logic_result.keys() if isinstance(logic_result, dict) else 'Not a dict'}")
                simple_log.info(f"Logic result type: {type(logic_result)}, keys: {logic_result.keys() if isinstance(logic_result, dict) else 'Not a dict'}")
                self.logger.info(f"Fact result type: {type(fact_result)}, keys: {fact_result.keys() if isinstance(fact_result, dict) else 'Not a dict'}")
                simple_log.info(f"Fact result type: {type(fact_result)}, keys: {fact_result.keys() if isinstance(fact_result, dict) else 'Not a dict'}")
                self.logger.info(f"Hallucination result type: {type(hallucination_result)}, keys: {hallucination_result.keys() if isinstance(hallucination_result, dict) else 'Not a dict'}")
                simple_log.info(f"Hallucination result type: {type(hallucination_result)}, keys: {hallucination_result.keys() if isinstance(hallucination_result, dict) else 'Not a dict'}")
                
                # Validate verification results
                logic_text = str(logic_result.get('logic_analysis', ''))
                fact_text = str(fact_result.get('fact_analysis', ''))
                halluc_text = str(hallucination_result.get('hallucination_analysis', ''))
                
                # Detect if LLM is generating completely unrelated examples
                unrelated_keywords = ['Tesla', 'OpenAI', 'Microsoft', 'Mars', 'planet', 'population', 'Q1 2023', 'vehicles', 'Event A', 'Person Z', 'Earth is flat']
                
                # Check if any result contains obviously unrelated content
                for result_name, result_text in [("Logic", logic_text), ("Fact", fact_text), ("Hallucination", halluc_text)]:
                    if any(keyword in result_text for keyword in unrelated_keywords):
                        self.logger.warning(f"WARNING: {result_name} checker may have generated unrelated examples!")
                        self.logger.warning(f"Found unrelated keywords in: {result_text}")
                        self.logger.warning("This suggests the LLM is not analyzing the actual draft content")
                
                # Now run synthesis chain with all results
                synthesis_inputs = {
                    "logic_analysis": logic_result.get('logic_analysis', '{}'),
                    "fact_analysis": fact_result.get('fact_analysis', '{}'),
                    "hallucination_analysis": hallucination_result.get('hallucination_analysis', '{}')
                }
                
                self.logger.info("="*250)
                simple_log.info("="*250)
                self.logger.info("LLM INPUT - SYNTHESIS CHAIN")
                simple_log.info("LLM INPUT - SYNTHESIS CHAIN")
                self.logger.info("="*250)
                simple_log.info("="*250)
                self.logger.info(">>> ACTUAL COMPLETE SYNTHESIS INPUTS <<<")
                simple_log.info(">>> ACTUAL COMPLETE SYNTHESIS INPUTS <<<")
                self.logger.info("START_SYNTHESIS_INPUT" + "="*229)
                simple_log.info("START_SYNTHESIS_INPUT" + "="*229)
                # Log ALL inputs without truncation
                self.logger.info("LOGIC ANALYSIS:")
                simple_log.info("LOGIC ANALYSIS:")
                self.logger.info(synthesis_inputs['logic_analysis'])
                simple_log.info(synthesis_inputs['logic_analysis'])
                self.logger.info("-" * 100)
                simple_log.info("-" * 100)
                self.logger.info("FACT ANALYSIS:")
                simple_log.info("FACT ANALYSIS:")
                self.logger.info(synthesis_inputs['fact_analysis'])
                simple_log.info(synthesis_inputs['fact_analysis'])
                self.logger.info("-" * 100)
                simple_log.info("-" * 100)
                self.logger.info("HALLUCINATION ANALYSIS:")
                simple_log.info("HALLUCINATION ANALYSIS:")
                self.logger.info(synthesis_inputs['hallucination_analysis'])
                simple_log.info(synthesis_inputs['hallucination_analysis'])
                self.logger.info("END_SYNTHESIS_INPUT" + "="*231)
                simple_log.info("END_SYNTHESIS_INPUT" + "="*231)
                self.logger.info("="*250)
                simple_log.info("="*250)
                
                # Use arun for proper variable substitution with ChatPromptTemplate
                synthesis_result_text = await self.synthesis_chain.arun(**synthesis_inputs)
                synthesis_result = {'text': synthesis_result_text}
                
                self.logger.info("="*250)
                simple_log.info("="*250)
                self.logger.info("LLM OUTPUT - SYNTHESIS CHAIN")
                simple_log.info("LLM OUTPUT - SYNTHESIS CHAIN")
                self.logger.info("="*250)
                simple_log.info("="*250)
                # Log the FULL synthesis result - NO TRUNCATION!
                self.logger.info(">>> ACTUAL COMPLETE SYNTHESIS RESPONSE <<<")
                simple_log.info(">>> ACTUAL COMPLETE SYNTHESIS RESPONSE <<<")
                self.logger.info("START_SYNTHESIS" + "="*235)
                simple_log.info("START_SYNTHESIS" + "="*235)
                if isinstance(synthesis_result, dict):
                    try:
                        formatted_result = json.dumps(synthesis_result, indent=2)
                        self.logger.info(formatted_result)  # Log the FULL formatted result
                        simple_log.info(formatted_result)
                    except:
                        self.logger.info(str(synthesis_result))  # Log as string if JSON fails
                        simple_log.info(str(synthesis_result))
                else:
                    self.logger.info(str(synthesis_result))  # Log the FULL result
                    simple_log.info(str(synthesis_result))
                self.logger.info("END_SYNTHESIS" + "="*237)
                simple_log.info("END_SYNTHESIS" + "="*237)
                self.logger.info(f"Total synthesis length: {len(str(synthesis_result))} characters")
                simple_log.info(f"Total synthesis length: {len(str(synthesis_result))} characters")
                self.logger.info("="*250)
                simple_log.info("="*250)
                
                # Parse the final synthesized critique
                self.logger.info(f"Attempting to parse synthesis result (type: {type(synthesis_result)})")
                simple_log.info(f"Attempting to parse synthesis result (type: {type(synthesis_result)})")
                
                # Extract the text from the synthesis result dict
                if isinstance(synthesis_result, dict):
                    json_text = synthesis_result.get("text", "")
                else:
                    json_text = str(synthesis_result)
                
                if not json_text or not json_text.strip():
                    self.logger.warning("Synthesis returned empty text response!")
                    raise json.JSONDecodeError("Empty response", str(json_text), 0)
                
                # Try to extract JSON if it's wrapped in markdown or other text
                json_text = json_text.strip()
                if "```json" in json_text:
                    # Extract JSON from markdown code block
                    json_text = json_text.split("```json")[1].split("```")[0].strip()
                    self.logger.info(f"Extracted JSON from markdown: {json_text}")
                    simple_log.info(f"Extracted JSON from markdown: {json_text}")
                elif "```" in json_text:
                    # Extract from generic code block
                    json_text = json_text.split("```")[1].split("```")[0].strip()
                    self.logger.info(f"Extracted JSON from code block: {json_text}")
                    simple_log.info(f"Extracted JSON from code block: {json_text}")
                
                # Fix double brace issue that sometimes occurs
                if json_text.startswith('{{') and json_text.endswith('}}'):
                    json_text = json_text[1:-1]
                    self.logger.info("Fixed double brace issue in JSON")
                    simple_log.info("Fixed double brace issue in JSON")
                
                final_critique = json.loads(json_text)
                critiques = self._convert_json_to_critiques(final_critique)
                overall_assessment = final_critique.get("overall_assessment", "Draft requires revision")
                severity_score = final_critique.get("severity_score", 0.5)
                
                self.logger.info(f"Parallel verification complete! Found {len(critiques)} issues through independent analysis")
                simple_log.info(f"Parallel verification complete! Found {len(critiques)} issues through independent analysis")
                
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON parsing failed: {e}")
                self.logger.error(f"Raw synthesis result: '{json_text if 'json_text' in locals() else 'N/A'}'")
                
                # Fallback to empty critiques
                critiques = []
                overall_assessment = "Failed to parse critique - JSON parsing error"
                severity_score = 0.5
            except Exception as e:
                self.logger.error(f"Unexpected error parsing critique: {e}")
                critiques = []
                overall_assessment = "Failed to parse critique - unexpected error"
                severity_score = 0.5
            
            # Create formatted JSON output according to specification
            formatted_output = {
                "draft_id": draft["draft_id"],
                "critiques": [
                    {
                        "step_ref": c.get("step_ref"),
                        "type": c.get("type", "logic_flaw"),
                        "severity": c.get("severity", "medium"),
                        "description": c.get("description", ""),
                        "claim": c.get("claim")
                    }
                    for c in critiques
                ],
                "overall_assessment": overall_assessment
            }
            
            # Log the JSON output
            self.logger.info("="*250)
            simple_log.info("="*250)
            self.logger.info("CRITIC OUTPUT (JSON)")
            simple_log.info("CRITIC OUTPUT (JSON)")
            self.logger.info("="*250)
            simple_log.info("="*250)
            self.logger.info(json.dumps(formatted_output, indent=2))
            simple_log.info(json.dumps(formatted_output, indent=2))
            self.logger.info("="*250)
            simple_log.info("="*250)

            # Send progress callback with critique details
            if self.context.progress_callback:
                try:
                    # Count critiques by severity
                    severity_counts = {
                        "critical": len([c for c in critiques if c.get("severity") == "critical"]),
                        "high": len([c for c in critiques if c.get("severity") == "high"]),
                        "medium": len([c for c in critiques if c.get("severity") == "medium"]),
                        "low": len([c for c in critiques if c.get("severity") == "low"])
                    }

                    progress_data = {
                        "status": "in_progress",
                        "stage": "critic",
                        "message": f"✅ Review complete: {len(critiques)} issues found (Critical: {severity_counts['critical']}, High: {severity_counts['high']}, Medium: {severity_counts['medium']}, Low: {severity_counts['low']})",
                        "agent": "critic",
                        "details": {
                            "type": "critique_complete",
                            "draft_id": draft["draft_id"],
                            "total_critiques": len(critiques),
                            "severity_counts": severity_counts,
                            "severity_score": severity_score,
                            "overall_assessment": overall_assessment,
                            "top_critiques": [
                                {
                                    "type": c.get("type"),
                                    "severity": c.get("severity"),
                                    "description": c.get("description"),
                                    "step_ref": c.get("step_ref")
                                }
                                for c in critiques[:5]  # Top 5 critiques
                            ],
                            "round": state['current_round']
                        }
                    }
                    self.logger.info(f"Critic: Sending progress update")
                    self.context.progress_callback(progress_data)
                except Exception as e:
                    self.logger.error(f"Failed to send critic progress: {e}")

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
            simple_log.info(f"Critique completed:")
            self.logger.info(f"  - Total issues: {len(critiques)}")
            simple_log.info(f"  - Total issues: {len(critiques)}")
            self.logger.info(f"  - Overall assessment: {overall_assessment}")
            simple_log.info(f"  - Overall assessment: {overall_assessment}")
            self.logger.info(f"  - Severity score: {severity_score:.2f}")
            simple_log.info(f"  - Severity score: {severity_score:.2f}")
            
            # Log critical issues
            critical_issues = [c for c in critiques if c.get("severity") == "critical"]
            if critical_issues:
                self.logger.warning(f"  - CRITICAL issues: {len(critical_issues)}")
                for issue in critical_issues:  # All critical issues
                    self.logger.warning(f"    • {issue['description']}")
            
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
    
    def _convert_json_to_critiques(self, final_critique: Dict) -> List[Critique]:
        """Convert the JSON output from chained pipeline to Critique objects"""
        critiques = []
        
        for c in final_critique.get("critiques", []):
            critiques.append(Critique(
                type=c.get("type", "logic_flaw"),
                severity=c.get("severity", "medium"),
                description=c.get("description", ""),
                step_ref=c.get("step_ref"),
                claim=c.get("claim")
            ))
        
        return critiques
    
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
                        elif ref_or_claim.upper() == "NA":
                            step_ref = None
                        elif default_type == "fact_contradiction":
                            claim = ref_or_claim
                        elif default_type == "hallucination":
                            # For hallucinations, no step ref
                            step_ref = None
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
        for i, result in enumerate(retrieval_results, 1):  # All results
            # Provide complete context for comprehensive fact-checking (no truncation)
            content = result.get('content', '')
            context_parts.append(f"[Source {i}]: {content}")
        
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
