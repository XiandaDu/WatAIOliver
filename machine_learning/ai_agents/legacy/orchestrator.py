"""
Speculative AI Orchestrator

Main orchestrator that coordinates all agents in the multi-agent reasoning system.
Implements the complete debate loop with proper error handling and monitoring.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, AsyncGenerator
from datetime import datetime

from ai_agents.config import SpeculativeAIConfig
from ai_agents.agents.base_agent import AgentRole, AgentInput, AgentOutput
from ai_agents.agents.retrieve_agent import RetrieveAgent
from ai_agents.agents.strategist_agent import StrategistAgent
from ai_agents.agents.critic_agent import CriticAgent
from ai_agents.agents.moderator_agent import ModeratorAgent
from ai_agents.agents.reporter_agent import ReporterAgent
from ai_agents.agents.tutor_agent import TutorAgent
from rag_system.llm_clients.cerebras_client import CerebrasClient
from rag_system.llm_clients.gemini_client import GeminiClient


class MultiAgentOrchestrator:
    """
    Main orchestrator for the Multi-Agent System
    
    Coordinates the complete workflow:
    1. Retrieve - Enhanced retrieval with query reframing
    2. Strategist - Generate draft solution with CoT
    3. Critic - Critical verification and issue identification
    4. Moderator - Debate flow control and convergence decisions
    5. Reporter - Final answer synthesis and formatting
    """
    
    def __init__(
        self, 
        config: Optional[SpeculativeAIConfig] = None,
        rag_service=None,
        llm_client=None,
        logger: Optional[logging.Logger] = None
    ):
        self.config = config or SpeculativeAIConfig()
        self.rag_service = rag_service
        self.llm_client = llm_client
        self.logger = logger or logging.getLogger("ai_agents.orchestrator")
        
        # Initialize agents directly
        self._setup_agents()
        
        # Session tracking
        self.current_sessions = {}
        
        # Agent conversation tracker
        self.conversation_history = []
        
        # Performance metrics
        self.execution_stats = {
            "total_queries": 0,
            "successful_completions": 0,
            "convergence_rate": 0.0,
            "average_debate_rounds": 0.0,
            "deadlock_rate": 0.0
        }
        
        self.logger.info("Multi-Agent System Orchestrator initialized")
        self.logger.info(f"Config: max_rounds={self.config.max_debate_rounds}, retrieval_k={self.config.retrieval_k}")
    def _setup_agents(self):
        """Initialize all agents directly"""
        
        # Create agent instances with shared configuration
        self.retrieve_agent = RetrieveAgent(
            config=self.config,
            llm_client=self.llm_client,
            rag_service=self.rag_service,
            logger=self.logger.getChild("retrieve")
        )
        
        self.strategist_agent = StrategistAgent(
            config=self.config,
            llm_client=self.llm_client,
            logger=self.logger.getChild("strategist")
        )
        
        self.critic_agent = CriticAgent(
            config=self.config,
            llm_client=self.llm_client,
            logger=self.logger.getChild("critic")
        )
        
        self.moderator_agent = ModeratorAgent(
            config=self.config,
            llm_client=self.llm_client,
            logger=self.logger.getChild("moderator")
        )
        
        self.reporter_agent = ReporterAgent(
            config=self.config,
            llm_client=self.llm_client,
            logger=self.logger.getChild("reporter")
        )
        
        self.tutor_agent = TutorAgent(
            config=self.config,
            llm_client=self.llm_client,
            logger=self.logger.getChild("tutor")
        )
        
        self.logger.info(f"Initialized 6 agents (Retrieve, Strategist, Critic, Moderator, Reporter, Tutor)")

    def _create_llm_client(self, model_name: str):
        """Create an LLM client based on model name."""
        try:
            if model_name.startswith("gemini"):
                return GeminiClient(
                    api_key=self.rag_service.settings.google_api_key,
                    model=model_name,
                    temperature=0.6,
                )
            if model_name.startswith("qwen") or model_name.startswith("cerebras"):
                return CerebrasClient(
                    api_key=self.rag_service.settings.cerebras_api_key,
                    model=model_name,
                )
        except Exception as e:
            self.logger.error(f"Failed to create llm client for {model_name}: {e}")
        return None
    
    def _log_agent_conversation(self, agent_name: str, input_data: Any, output_data: Any, stage: str = ""):
        """Log agent conversation in detailed chat-group format"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Enhanced input formatting
        if hasattr(input_data, 'query'):
            query_preview = input_data.query[:100] + "..." if len(input_data.query) > 100 else input_data.query
            input_preview = f"'{query_preview}'"
        elif isinstance(input_data, dict):
            input_preview = f"Data: {str(input_data)[:80]}..."
        else:
            input_preview = f"Input: {str(input_data)[:80]}..."
        
        # Enhanced output formatting with detailed content
        if hasattr(output_data, 'content') and output_data.content:
            if 'draft_content' in output_data.content:
                draft = output_data.content['draft_content']
                draft_preview = draft[:300] + "..." if len(draft) > 300 else draft
                output_preview = f"Generated draft ({len(draft)} chars):\n{draft_preview}"
                
            elif 'critiques' in output_data.content:
                critiques = output_data.content['critiques'] or []
                if critiques:
                    critique_details = []
                    for i, critique in enumerate(critiques[:2], 1):
                        issue = critique.get('issue', 'Unknown issue')[:80]
                        critique_details.append(f"  • {issue}")
                    critique_text = "\n".join(critique_details)
                    if len(critiques) > 2:
                        critique_text += f"\n  • (+{len(critiques)-2} more issues)"
                    output_preview = f"Found {len(critiques)} issues:\n{critique_text}"
                else:
                    output_preview = "No issues found - draft approved!"
                    
            elif 'decision' in output_data.content:
                decision = output_data.content['decision']
                reasoning = output_data.content.get('reasoning', '')
                reasoning_preview = reasoning[:120] + "..." if len(reasoning) > 120 else reasoning
                output_preview = f"Decision: {decision}\n  Reasoning: {reasoning_preview}"
                
            elif 'final_answer' in output_data.content:
                answer = str(output_data.content['final_answer'])
                if isinstance(output_data.content['final_answer'], dict):
                    # Extract key parts of structured answer
                    intro = output_data.content['final_answer'].get('introduction', '')
                    solution = output_data.content['final_answer'].get('step_by_step_solution', '')
                    answer_preview = f"Introduction: {intro}\nSolution: {solution}"
                else:
                    answer_preview = answer
                output_preview = f"Final answer:\n{answer_preview}"
                
            elif 'retrieval_results' in output_data.content:
                results = output_data.content['retrieval_results']
                quality = output_data.content.get('quality_assessment', {}).get('score', 0)
                output_preview = f"Retrieved {len(results)} chunks (quality: {quality:.3f})"
                if results:
                    for i, result in enumerate(results[:2], 1):
                        content = result.get('content', '')
                        score = result.get('score', 'N/A')
                        output_preview += f"\n  • Chunk {i}: {content} (score: {score})"
                    if len(results) > 2:
                        output_preview += f"\n  • (+{len(results)-2} more chunks)"
                        
            else:
                content_str = str(output_data.content)
                output_preview = content_str
        else:
            output_preview = str(output_data)
        
        # Add to conversation history
        conversation_entry = {
            "timestamp": timestamp,
            "agent": agent_name,
            "stage": stage,
            "input": input_preview,
            "output": output_preview,
            "success": getattr(output_data, 'success', True)
        }
        
        if not hasattr(self, 'conversation_history'):
            self.conversation_history = []
        self.conversation_history.append(conversation_entry)
        
        # Display as chat group conversation
        status_icon = "SUCCESS" if conversation_entry["success"] else "ERROR"
        stage_info = f" [{stage}]" if stage else ""
        
        self.logger.info(f"")
        self.logger.info(f"=== {agent_name.upper()}{stage_info} @ {timestamp} ===")
        self.logger.info(f"INPUT: {input_preview}")
        self.logger.info(f"OUTPUT [{status_icon}]: {output_preview}")
        
        # Add processing time if available
        if hasattr(output_data, 'processing_time') and output_data.processing_time > 0:
            self.logger.info(f"PROCESSING TIME: {output_data.processing_time:.2f}s")
    
    def _display_conversation_summary(self):
        """Display the full agent conversation like a chat history"""
        if not hasattr(self, 'conversation_history') or not self.conversation_history:
            self.logger.info("AGENT CONVERSATION HISTORY: No conversation data available")
            return
            
        self.logger.info("AGENT CONVERSATION HISTORY:")
        self.logger.info("=" * 80)
        
        for entry in self.conversation_history:
            status = "" if entry["success"] else ""
            stage_info = f" ({entry['stage']})" if entry['stage'] else ""
            
            self.logger.info(f"[{entry['timestamp']}] {entry['agent']}{stage_info}:")
            self.logger.info(f"  {entry['input']}")
            self.logger.info(f"  {status} {entry['output']}")
            self.logger.info("")
        
        self.logger.info("=" * 80)
    
    async def process_query(
        self,
        query: str,
        course_id: str,
        session_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        heavy_model: Optional[str] = None,
        course_prompt: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process a user query through the complete speculative AI workflow
        """
        
        start_time = datetime.now()
        self.execution_stats["total_queries"] += 1

        # Clear conversation history for new query
        self.conversation_history = []

        heavy_llm = None
        original_strategist_llm = None
        original_critic_llm = None

        try:
            self.logger.info(f"QUERY: '{query[:80]}...' | Course: {course_id[:8]}...")
            
            yield {"status": "in_progress", "stage": "initialization", "message": "Starting agent processing..."}
            
            # Add course prompt to metadata for all agents
            enhanced_metadata = metadata.copy() if metadata else {}
            if course_prompt:
                enhanced_metadata['course_prompt'] = course_prompt
                self.logger.info(f"Using course-specific prompt: {course_prompt[:50]}...")
            
            # Use heavy model if specified, otherwise fall back to base model from metadata
            debate_model = heavy_model
            if not debate_model:
                # If no heavy model specified, check metadata for base model
                debate_model = enhanced_metadata.get('base_model')
            
            if debate_model:
                debate_llm = self._create_llm_client(debate_model)
                if debate_llm:
                    original_strategist_llm = self.strategist_agent.llm_client
                    original_critic_llm = self.critic_agent.llm_client
                    self.strategist_agent.llm_client = debate_llm
                    self.critic_agent.llm_client = debate_llm
                    self.logger.info(f"Using {debate_model} for debate agents")
            
            # Stage 1: Enhanced Retrieval
            self.logger.info("")
            self.logger.info("=== RETRIEVAL STAGE ===")
            yield {"status": "in_progress", "stage": "retrieval", "message": "Performing contextual retrieval..."}
            retrieval_result = await self._execute_retrieval(query, course_id, session_id, enhanced_metadata)
            
            if not retrieval_result.success:
                yield self._create_error_response("Retrieval failed", retrieval_result.error_message)
                return # Stop execution on error

            context = retrieval_result.content.get("retrieval_results", [])
            self.logger.info(f"   Retrieved {len(context)} context chunks")
            yield {"status": "in_progress", "stage": "retrieval_complete", "message": f"Retrieved {len(context)} context chunks.", "context_items": len(context)}

            # Stage 2: Debate Loop
            self.logger.info("")
            self.logger.info("️  === DEBATE STAGE ===")
            yield {"status": "in_progress", "stage": "debate", "message": "Starting multi-agent debate..."}
            debate_result = await self._execute_debate_loop(query, context, session_id, enhanced_metadata)
            
            if not debate_result["success"]:
                yield self._create_error_response("Debate loop failed", debate_result.get("error"))
                return # Stop execution on error
            
            yield {"status": "in_progress", "stage": "debate_complete", "message": f"Debate completed in {debate_result['result']['debate_rounds']} rounds.", "debate_rounds": debate_result['result']['debate_rounds']}
            
            # Stage 3: Final Synthesis
            self.logger.info("")
            self.logger.info("=== SYNTHESIS STAGE ===")
            yield {"status": "in_progress", "stage": "synthesis", "message": "Synthesizing final answer..."}
            final_result = await self._execute_final_synthesis(
                query, context, debate_result["result"], session_id, enhanced_metadata
            )
            
            if not final_result.success:
                yield self._create_error_response("Final synthesis failed", final_result.error_message)
                return # Stop execution on error
            
            yield {"status": "in_progress", "stage": "synthesis_complete", "message": "Final answer synthesized."}
            
            # Stage 4: Tutor Interaction
            self.logger.info("")
            self.logger.info("=== TUTOR STAGE ===")
            yield {"status": "in_progress", "stage": "tutor_interaction", "message": "Engaging tutor for additional insights..."}
            tutor_result = await self._execute_tutor_interaction(
                query, final_result.content["final_answer"], session_id, enhanced_metadata
            )
            
            if not tutor_result.success:
                self.logger.warning(f"Tutor interaction failed: {tutor_result.error_message}")
                # Continue with basic response if tutor fails
                tutor_content = {"interaction_type": "basic", "elements": [{"type": "answer", "content": final_result.content["final_answer"]}]}
            else:
                tutor_content = tutor_result.content
            
            # Update success metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            self.execution_stats["successful_completions"] += 1
            self._update_execution_stats(debate_result["result"])
            
            # Show conversation summary
            self._display_conversation_summary()
            
            # Format final response with tutor interaction
            response = self._format_tutor_response(
                tutor_content,
                final_result.content["final_answer"],
                retrieval_result,
                debate_result["result"],
                final_result,
                processing_time
            )
            
            self.logger.info(f"Query completed successfully in {processing_time:.2f}s")
            yield {"status": "complete", "final_response": response, "processing_time": processing_time}

        except Exception as e:
            self.logger.error(f"Query processing failed: {str(e)}")
            yield self._create_error_response("System error", str(e))
        finally:
            if heavy_llm:
                if original_strategist_llm:
                    self.strategist_agent.llm_client = original_strategist_llm
                if original_critic_llm:
                    self.critic_agent.llm_client = original_critic_llm
    
    async def _execute_retrieval(
        self, 
        query: str, 
        course_id: str, 
        session_id: str, 
        metadata: Optional[Dict[str, Any]]
    ) -> AgentOutput:
        """Execute enhanced retrieval stage"""
        
        retrieve_agent = self.retrieve_agent
        
        if not retrieve_agent:
            self.logger.error("Retrieve agent not available!")
            raise Exception("Retrieve agent not available")
        
        retrieval_input = AgentInput(
            query=query,
            context=[],  # No initial context for retrieval
            metadata={
                "course_id": course_id,
                **(metadata or {})
            },
            session_id=session_id
        )
        
        result = await retrieve_agent.execute(retrieval_input)
        
        # Log the agent conversation
        self._log_agent_conversation("Retrieve", retrieval_input, result, "Retrieval")
        
        return result
    
    async def _execute_debate_loop(
        self, 
        query: str, 
        context: List[Dict[str, Any]], 
        session_id: str, 
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute the complete debate loop with iteration control"""
        
        self.logger.info(f"")
        self.logger.info(f"[DEBATE LOOP] Starting multi-agent debate")
        self.logger.info(f"   Context items: {len(context)}")
        self.logger.info(f"   Max rounds: {self.config.max_debate_rounds}")
        
        try:
            current_round = 1
            current_draft = None
            current_cot = None
            
            # Get agents
            strategist = self.strategist_agent
            critic = self.critic_agent
            moderator = self.moderator_agent
            
            if not all([strategist, critic, moderator]):
                self.logger.error("[DEBATE LOOP] Required debate agents not available!")
                raise Exception("Required debate agents not available")
            
            while current_round <= self.config.max_debate_rounds:
                self.logger.info(f"")
                self.logger.info(f"=== ROUND {current_round}/{self.config.max_debate_rounds} ===")
                
                # Stage 1: Strategist generates draft and CoT
                self.logger.info(f"STRATEGIST: Analyzing query and generating draft...")
                strategist_input = AgentInput(
                    query=query,
                    context=context,
                    metadata={
                        "round": current_round,
                        "previous_feedback": getattr(self, '_last_feedback', None),
                        **(metadata or {})
                    },
                    session_id=session_id
                )
                
                strategist_result = await strategist.execute(strategist_input)
                
                # Log the agent conversation
                self._log_agent_conversation("Strategist", strategist_input, strategist_result, f"Round {current_round}")
                
                if not strategist_result.success:
                    return {"success": False, "error": f"Strategist failed in round {current_round}"}
                
                current_draft = strategist_result.content["draft_content"]
                current_cot = strategist_result.content["chain_of_thought"]
                draft_id = strategist_result.content["draft_id"]

                # Step 2: Critic analyzes draft
                self.logger.info(f"CRITIC: Evaluating draft for issues...")
                critic_input = AgentInput(
                    query=query,
                    context=context,
                    metadata={
                        "draft_content": current_draft,
                        "chain_of_thought": current_cot,
                        "draft_id": draft_id,
                        "round": current_round,
                        **(metadata or {})
                    },
                    session_id=session_id
                )
                
                critic_result = await critic.execute(critic_input)
                
                # Log the agent conversation
                self._log_agent_conversation("Critic", critic_input, critic_result, f"Round {current_round}")
                
                if not critic_result.success:
                    return {"success": False, "error": f"Critic failed in round {current_round}"}
                
                critiques = critic_result.content["critiques"]
                overall_assessment = critic_result.content["overall_assessment"]

                # Step 3: Moderator decides next action
                self.logger.info(f"MODERATOR: Making decision on draft quality...")
                moderator_input = AgentInput(
                    query=query,
                    context=context,
                    metadata={
                        "critiques": critiques,
                        "draft_id": draft_id,
                        "current_round": current_round,
                        "overall_assessment": overall_assessment,
                        "draft_content": current_draft,
                        "chain_of_thought": current_cot,
                        **(metadata or {})
                    },
                    session_id=session_id
                )
                
                moderator_result = await moderator.execute(moderator_input)
                
                # Log the agent conversation
                self._log_agent_conversation("Moderator", moderator_input, moderator_result, f"Round {current_round}")
                
                if not moderator_result.success:
                    return {"success": False, "error": f"Moderator failed in round {current_round}"}
                
                decision = moderator_result.content["decision"]
                
                if decision not in ["converged", "iterate", "abort_deadlock", "escalate_with_warning"]:
                    self.logger.warning(f"Unknown decision: {decision}")
                
                # Act on moderator decision
                if decision == "converged":
                    self.logger.info(f"   Debate converged after {current_round} rounds")
                    return {
                        "success": True,
                        "result": {
                            "status": "converged",
                            "final_draft": {
                                "content": current_draft,
                                "cot": current_cot,
                                "draft_id": draft_id,
                                "status": "approved",
                                "quality_score": moderator_result.content["decision_metadata"]["convergence_score"]
                            },
                            "remaining_critiques": moderator_result.content.get("critiques") or [],
                            "debate_rounds": current_round,
                            "convergence_score": moderator_result.content["decision_metadata"]["convergence_score"]
                        }
                    }
                
                elif decision == "abort_deadlock":
                    self.logger.info(f"   ️ Debate deadlocked after {current_round} rounds")
                    return {
                        "success": True,
                        "result": {
                            "status": "deadlock",
                            "final_draft": {
                                "content": current_draft,
                                "cot": current_cot,
                                "draft_id": draft_id,
                                "status": "deadlock",
                                "quality_score": moderator_result.content["decision_metadata"]["convergence_score"]
                            },
                            "remaining_critiques": critiques or [],
                            "debate_rounds": current_round,
                            "convergence_score": moderator_result.content["decision_metadata"]["convergence_score"]
                        }
                    }
                
                elif decision == "escalate_with_warning":
                    self.logger.info(f"️ Quality issues escalated after {current_round} rounds")
                    return {
                        "success": True,
                        "result": {
                            "status": "escalated",
                            "final_draft": {
                                "content": current_draft,
                                "cot": current_cot,
                                "draft_id": draft_id,
                                "status": "escalated",
                                "quality_score": moderator_result.content["decision_metadata"]["convergence_score"],
                                "quality_warning": moderator_result.content.get("warning_message", "Quality issues detected")
                            },
                            "remaining_critiques": critiques or [],
                            "debate_rounds": current_round,
                            "convergence_score": moderator_result.content["decision_metadata"]["convergence_score"],
                            "escalation_warning": moderator_result.content.get("warning_message")
                        }
                    }
                
                elif decision == "iterate":
                    # Prepare for next iteration
                    feedback = moderator_result.content.get("feedback_to_strategist", "")
                    self.logger.debug(f"Moderator feedback type: {type(feedback)}, content: {feedback}")
                    self._last_feedback = feedback or ""
                    current_round += 1
                
                else:
                    return {"success": False, "error": f"Unknown moderator decision: {decision}"}
            
            # Should not reach here due to moderator deadlock detection
            return {"success": False, "error": "Debate loop exceeded maximum rounds"}
            
        except Exception as e:
            self.logger.error(f"Debate loop failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _execute_final_synthesis(
        self, 
        query: str, 
        context: List[Dict[str, Any]], 
        debate_result: Dict[str, Any], 
        session_id: str, 
        metadata: Optional[Dict[str, Any]]
    ) -> AgentOutput:
        """Execute final answer synthesis"""
        
        self.logger.info("[REPORTER] Starting final synthesis")
        
        reporter = self.reporter_agent
        
        if not reporter:
            self.logger.error("[REPORTER] Agent not available!")
            raise Exception("Reporter agent not available")
        
        final_draft = debate_result["final_draft"]
        self.logger.info(f"[REPORTER] Processing final draft with status: {final_draft.get('status', 'unknown')}")
        
        reporter_input = AgentInput(
            query=query,
            context=context,
            metadata={
                "draft_content": final_draft["content"],
                "chain_of_thought": final_draft["cot"],
                "final_draft_status": {
                    "status": final_draft["status"],
                    "quality_score": final_draft["quality_score"]
                },
                "remaining_critiques": debate_result.get("remaining_critiques", []),
                "debate_rounds": debate_result["debate_rounds"],
                **(metadata or {})
            },
            session_id=session_id
        )
        
        result = await reporter.execute(reporter_input)
        
        # Log the agent conversation
        self._log_agent_conversation("Reporter", reporter_input, result, "Synthesis")
        
        return result
    
    async def _execute_tutor_interaction(
        self,
        query: str,
        final_answer: Dict[str, Any],
        session_id: str,
        metadata: Optional[Dict[str, Any]]
    ) -> AgentOutput:
        """Execute tutor interaction stage"""
        
        tutor_input = AgentInput(
            query=query,
            context=[],  # Tutor doesn't need retrieval context
            metadata={
                "final_answer": final_answer,
                "conversation_history": metadata.get("conversation_history", []),
                **(metadata or {})
            },
            session_id=session_id
        )
        
        result = await self.tutor_agent.execute(tutor_input)
        
        # Log the agent conversation
        self._log_agent_conversation("Tutor", tutor_input, result, "Interaction")
        
        return result
    
    def _format_final_response(
        self, 
        final_answer: Dict[str, Any], 
        retrieval_result: AgentOutput, 
        debate_result: Dict[str, Any], 
        synthesis_result: AgentOutput,
        processing_time: float
    ) -> Dict[str, Any]:
        """Format the complete response for the user"""
        
        return {
            "success": True,
            "answer": final_answer,
            "metadata": {
                "processing_time": processing_time,
                "debate_status": debate_result["status"],
                "debate_rounds": debate_result["debate_rounds"],
                "convergence_score": debate_result["convergence_score"],
                "retrieval_quality": retrieval_result.content.get("quality_assessment", {}),
                "synthesis_metadata": synthesis_result.content.get("synthesis_metadata", {}),
                "agent_performance": self._get_simple_metrics()
            },
            "debug_info": {
                "retrieval_strategy": retrieval_result.metadata.get("retrieval_strategy"),
                "context_items": len(retrieval_result.content.get("retrieval_results", [])),
                "remaining_issues": len(debate_result.get("remaining_critiques", [])),
                "quality_indicators": final_answer.get("quality_indicators", {})
            } if self.config.enable_debug_logging else {}
        }
    
    def _format_tutor_response(
        self,
        tutor_content: Dict[str, Any],
        final_answer: Dict[str, Any],
        retrieval_result: AgentOutput,
        debate_result: Dict[str, Any],
        synthesis_result: AgentOutput,
        processing_time: float
    ) -> Dict[str, Any]:
        """Format response with tutor interaction"""
        
        return {
            "success": True,
            "answer": final_answer,
            "tutor_interaction": tutor_content,
            "metadata": {
                "processing_time": processing_time,
                "debate_status": debate_result["status"],
                "debate_rounds": debate_result["debate_rounds"],
                "convergence_score": debate_result["convergence_score"],
                "retrieval_quality": retrieval_result.content.get("quality_assessment", {}),
                "synthesis_metadata": synthesis_result.content.get("synthesis_metadata", {}),
                "agent_performance": self._get_simple_metrics()
            },
            "debug_info": {
                "retrieval_strategy": retrieval_result.metadata.get("retrieval_strategy"),
                "context_items": len(retrieval_result.content.get("retrieval_results", [])),
                "remaining_issues": len(debate_result.get("remaining_critiques", [])),
                "quality_indicators": final_answer.get("quality_indicators", {})
            } if self.config.enable_debug_logging else {}
        }
    
    def _create_error_response(self, error_type: str, error_message: str) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            "success": False,
            "error": {
                "type": error_type,
                "message": error_message,
                "timestamp": datetime.now().isoformat()
            },
                            "error_response": {
                "introduction": "I apologize, but I encountered an error while processing your query.",
                "step_by_step_solution": f"Error: {error_message}",
                "important_notes": "Please try rephrasing your question or contact support if the issue persists."
            }
        }
    
    def _update_execution_stats(self, debate_result: Dict[str, Any]):
        """Update execution statistics"""
        total_completions = self.execution_stats["successful_completions"]
        
        # Update convergence rate
        if debate_result["status"] == "converged":
            converged_count = getattr(self, '_converged_count', 0) + 1
            self._converged_count = converged_count
            self.execution_stats["convergence_rate"] = converged_count / total_completions
        
        # Update deadlock rate
        if debate_result["status"] == "deadlock":
            deadlock_count = getattr(self, '_deadlock_count', 0) + 1
            self._deadlock_count = deadlock_count
            self.execution_stats["deadlock_rate"] = deadlock_count / total_completions
        
        # Update average debate rounds
        total_rounds = getattr(self, '_total_rounds', 0) + debate_result["debate_rounds"]
        self._total_rounds = total_rounds
        self.execution_stats["average_debate_rounds"] = total_rounds / total_completions
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            "orchestrator_status": "operational",
            "agents_initialized": 6,
            "configuration": {
                "max_debate_rounds": self.config.max_debate_rounds,
                "retrieval_k": self.config.retrieval_k,
                "enable_debug": self.config.enable_debug_logging
            },
            "execution_stats": self.execution_stats,
            "agent_metrics": self._get_simple_metrics()
        }
    
    def _get_simple_metrics(self) -> Dict[str, Any]:
        """Get simple performance metrics for all agents"""
        return {
            "retrieve": self.retrieve_agent.get_metrics(),
            "strategist": self.strategist_agent.get_metrics(),
            "critic": self.critic_agent.get_metrics(),
            "moderator": self.moderator_agent.get_metrics(),
            "reporter": self.reporter_agent.get_metrics(),
            "tutor": self.tutor_agent.get_metrics(),
        }
        
    def reset_system_metrics(self):
        """Reset all system and agent metrics"""
        self.execution_stats = {
            "total_queries": 0,
            "successful_completions": 0,
            "convergence_rate": 0.0,
            "average_debate_rounds": 0.0,
            "deadlock_rate": 0.0
        }
        
        # Reset internal counters
        self._converged_count = 0
        self._deadlock_count = 0
        self._total_rounds = 0
        
        # Reset agent metrics
        for agent in [self.retrieve_agent, self.strategist_agent, self.critic_agent, self.moderator_agent, self.reporter_agent, self.tutor_agent]:
            agent.execution_count = 0
            agent.total_processing_time = 0.0
            agent.error_count = 0
        
        self.logger.info("System metrics reset") 