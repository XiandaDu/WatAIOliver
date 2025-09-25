"""
LangGraph Workflow for Multi-Agent System

Main workflow that orchestrates all agents using LangGraph.
"""

import logging
from typing import Dict, Any, List, Literal, AsyncGenerator, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from ai_agents.simple_logger import simple_log

from ai_agents.state import WorkflowState, AgentContext, initialize_state
from ai_agents.agents.retrieve_agent import RetrieveAgent
from ai_agents.agents.strategist_agent import StrategistAgent
from ai_agents.agents.critic_agent import CriticAgent
from ai_agents.agents.moderator_agent import ModeratorAgent
from ai_agents.agents.reporter_agent import ReporterAgent
from ai_agents.agents.tutor_agent import TutorAgent


class MultiAgentWorkflow:
    """
    LangGraph-based Multi-Agent Workflow
    
    Implements the complete debate loop with proper state management and routing.
    """
    
    def __init__(self, context: AgentContext, logger: logging.Logger = None):
        self.context = context
        self.logger = logger or logging.getLogger("langgraph.workflow")
        
        # Initialize agents
        self.retrieve_agent = RetrieveAgent(context)
        self.strategist_agent = StrategistAgent(context)
        self.critic_agent = CriticAgent(context)
        self.moderator_agent = ModeratorAgent(context)
        self.reporter_agent = ReporterAgent(context)
        self.tutor_agent = TutorAgent(context)
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
        
        # Add memory for conversation tracking
        self.memory = MemorySaver()
        self.app = self.workflow.compile(checkpointer=self.memory)
        
        self.logger.info("Multi-Agent Workflow initialized with LangGraph")
        simple_log.info("Multi-Agent Workflow initialized with LangGraph")
        simple_log.info("WORKFLOW INITIALIZED", {"agents": ["retrieve", "strategist", "critic", "moderator", "reporter", "tutor"]})
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        # Create the graph
        workflow = StateGraph(WorkflowState)
        
        # Add nodes for each agent
        workflow.add_node("retrieve", self.retrieve_agent)
        workflow.add_node("strategist", self.strategist_agent)
        workflow.add_node("critic", self.critic_agent)
        workflow.add_node("moderator", self.moderator_agent)
        workflow.add_node("reporter", self.reporter_agent)
        workflow.add_node("tutor", self.tutor_agent)
        
        # Define the flow
        # Start -> Retrieve
        workflow.set_entry_point("retrieve")
        
        # Retrieve -> Strategist (always after retrieval)
        workflow.add_edge("retrieve", "strategist")
        
        # Strategist -> Critic (always critique after draft)
        workflow.add_edge("strategist", "critic")
        
        # Critic -> Moderator (always moderate after critique)
        workflow.add_edge("critic", "moderator")
        
        # Moderator -> Conditional routing based on decision
        workflow.add_conditional_edges(
            "moderator",
            self._route_from_moderator,
            {
                "strategist": "strategist",  # Iterate
                "reporter": "reporter",       # Converged or deadlock
                "end": END                    # Error case
            }
        )
        
        # Reporter -> Tutor (always add tutoring after synthesis)
        workflow.add_edge("reporter", "tutor")
        
        # Tutor -> End
        workflow.add_edge("tutor", END)
        
        return workflow
    
    def _route_from_moderator(self, state: WorkflowState) -> Literal["strategist", "reporter", "end"]:
        """
        Routing function from Moderator node.
        Determines next step based on moderator decision.
        """
        decision = state.get("moderator_decision", "pending")
        current_round = state.get("current_round", 0)
        max_rounds = state.get("max_rounds", 3)
        convergence_score = state.get("convergence_score", 0.0)
        
        self.logger.info("="*250)
        simple_log.info("="*250)
        self.logger.info("WORKFLOW ROUTING DECISION")
        simple_log.info("WORKFLOW ROUTING DECISION")
        self.logger.info("="*250)
        simple_log.info("="*250)
        self.logger.info(f"Moderator decision: {decision}")
        simple_log.info(f"Moderator decision: {decision}")
        self.logger.info(f"Current round: {current_round} / {max_rounds}")
        simple_log.info(f"Current round: {current_round} / {max_rounds}")
        self.logger.info(f"Convergence score: {convergence_score:.3f}")
        simple_log.info(f"Convergence score: {convergence_score:.3f}")
        
        if decision == "iterate":
            self.logger.info("→ ROUTING TO: STRATEGIST (continue iteration)")
            simple_log.info("→ ROUTING TO: STRATEGIST (continue iteration)")
            self.logger.info("="*250)
            simple_log.info("="*250)
            return "strategist"
        elif decision in ["converged", "abort_deadlock", "escalate_with_warning"]:
            self.logger.info(f"→ ROUTING TO: REPORTER (synthesis phase - {decision})")
            simple_log.info(f"→ ROUTING TO: REPORTER (synthesis phase - {decision})")
            self.logger.info("="*250)
            simple_log.info("="*250)
            return "reporter"
        else:
            self.logger.error(f"→ ROUTING TO: END (unexpected decision: {decision})")
            self.logger.info("="*250)
            simple_log.info("="*250)
            return "end"
    
    async def process_query(
        self,
        query: str,
        course_id: str,
        session_id: str,
        metadata: Dict[str, Any] = None,
        course_prompt: str = None,
        max_rounds: int = 3
    ) -> Dict[str, Any]:
        """
        Process a query through the multi-agent workflow.
        
        Args:
            query: User's question
            course_id: Course identifier for retrieval
            session_id: Session identifier for tracking
            metadata: Additional metadata
            course_prompt: Course-specific prompt
            max_rounds: Maximum debate rounds
            
        Returns:
            Final response with answer and metadata
        """
        
        try:
            self.logger.info("="*250)
            simple_log.info("="*250)
            self.logger.info("STARTING LANGGRAPH MULTI-AGENT WORKFLOW")
            simple_log.info("STARTING LANGGRAPH MULTI-AGENT WORKFLOW")
            self.logger.info("="*250)
            simple_log.info("="*250)
            self.logger.info(f"Query: {query[:100]}...")
            simple_log.info(f"Query: {query[:100]}...")
            self.logger.info(f"Course: {course_id}")
            simple_log.info(f"Course: {course_id}")
            self.logger.info(f"Session: {session_id}")
            simple_log.info(f"Session: {session_id}")
            
            # Also log to simple logger for debugging
            simple_log.info("WORKFLOW START", {
                "query": query[:100],
                "course_id": course_id,
                "session_id": session_id,
                "max_rounds": max_rounds
            })
            
            # Initialize state
            initial_state = initialize_state(
                query=query,
                course_id=course_id,
                session_id=session_id,
                metadata=metadata,
                course_prompt=course_prompt,
                max_rounds=max_rounds
            )
            
            # Run the workflow
            config = {"configurable": {"thread_id": session_id}}
            
            # Stream execution for real-time updates
            async for event in self.app.astream(initial_state, config):
                # Log each node execution with detailed state information
                for node, state_update in event.items():
                    self.logger.info("="*250)
                    simple_log.info("="*250)
                    self.logger.info(f"STATE TRANSITION - NODE: {node.upper()}")
                    simple_log.info(f"STATE TRANSITION - NODE: {node.upper()}")
                    self.logger.info("="*250)
                    simple_log.info("="*250)
                    simple_log.info(f"NODE TRANSITION: {node.upper()}", {
                        "node": node,
                        "has_status": "workflow_status" in state_update
                    })
                    
                    # Log key state changes
                    if "workflow_status" in state_update:
                        self.logger.info(f"Status: {state_update['workflow_status']}")
                        simple_log.info(f"Status: {state_update['workflow_status']}")
                    
                    if "current_round" in state_update:
                        self.logger.info(f"Current round: {state_update['current_round']} / {state_update.get('max_rounds', 'unknown')}")
                        simple_log.info(f"Current round: {state_update['current_round']} / {state_update.get('max_rounds', 'unknown')}")
                    
                    if "moderator_decision" in state_update:
                        self.logger.info(f"Moderator decision: {state_update['moderator_decision']}")
                        simple_log.info(f"Moderator decision: {state_update['moderator_decision']}")
                        simple_log.info("MODERATOR DECISION", {
                            "decision": state_update['moderator_decision'],
                            "round": state_update.get('current_round', 'unknown')
                        })
                        if "convergence_score" in state_update:
                            self.logger.info(f"Convergence score: {state_update['convergence_score']}")
                            simple_log.info(f"Convergence score: {state_update['convergence_score']}")
                            simple_log.info("CONVERGENCE SCORE", {
                                "score": state_update['convergence_score']
                            })
                    
                    if "error_messages" in state_update and state_update["error_messages"]:
                        self.logger.warning(f"Errors accumulated: {len(state_update['error_messages'])}")
                        simple_log.error("WORKFLOW ERRORS", {
                            "error_count": len(state_update['error_messages']),
                            "latest_errors": state_update["error_messages"][-3:]
                        })
                        for i, error in enumerate(state_update["error_messages"][-3:], 1):  # Last 3 errors
                            self.logger.warning(f"  {i}. {error}")
                    
                    # Log agent-specific outputs
                    if node == "retrieve" and "retrieval_results" in state_update:
                        # retrieval_results is a list of RetrievalResult objects
                        retrieval_results = state_update["retrieval_results"]
                        if isinstance(retrieval_results, list):
                            sources_count = len(retrieval_results)
                        else:
                            # Fallback if it's somehow a dict
                            sources_count = len(retrieval_results.get("sources", []))
                        quality_score = state_update.get("retrieval_quality_score", "unknown")
                        self.logger.info(f"Retrieved {sources_count} sources, quality: {quality_score}")
                        simple_log.info(f"Retrieved {sources_count} sources, quality: {quality_score}")
                        simple_log.info("RETRIEVAL RESULT", {
                            "sources_count": sources_count,
                            "quality_score": quality_score
                        })
                    
                    elif node == "strategist" and "draft" in state_update:
                        draft_length = len(str(state_update["draft"].get("content", "")))
                        self.logger.info(f"Generated draft: {draft_length} characters")
                        simple_log.info(f"Generated draft: {draft_length} characters")
                    
                    elif node == "critic" and "critiques" in state_update:
                        critique_count = len(state_update.get("critiques", []))
                        severity_counts = {}
                        for c in state_update.get("critiques", []):
                            sev = c.get("severity", "unknown")
                            severity_counts[sev] = severity_counts.get(sev, 0) + 1
                        self.logger.info(f"Found {critique_count} critiques: {dict(severity_counts)}")
                        simple_log.info(f"Found {critique_count} critiques: {dict(severity_counts)}")
                    
                    elif node == "reporter" and "final_answer" in state_update:
                        answer_length = len(str(state_update["final_answer"]))
                        self.logger.info(f"Synthesized final answer: {answer_length} characters")
                        simple_log.info(f"Synthesized final answer: {answer_length} characters")
                    
                    elif node == "tutor" and "tutor_interaction" in state_update:
                        interaction_type = state_update["tutor_interaction"].get("interaction_type", "unknown")
                        elements_count = len(state_update["tutor_interaction"].get("elements", []))
                        self.logger.info(f"Prepared {interaction_type} interaction with {elements_count} elements")
                        simple_log.info(f"Prepared {interaction_type} interaction with {elements_count} elements")
                    
                    self.logger.info("="*250)
                    simple_log.info("="*250)
                    
                    # Yield intermediate updates
                    if isinstance(state_update, dict):
                        status = state_update.get("workflow_status", "processing")
                        yield {
                            "status": "in_progress",
                            "stage": node,
                            "message": f"Processing: {node}",
                            "state": status
                        }
            
            # Get final state
            final_state = await self.app.aget_state(config)
            state_data = final_state.values
            
            # Format final response
            response = self._format_final_response(state_data)
            
            self.logger.info("="*250)
            simple_log.info("="*250)
            self.logger.info("WORKFLOW COMPLETED SUCCESSFULLY")
            simple_log.info("WORKFLOW COMPLETED SUCCESSFULLY")
            self.logger.info("="*250)
            simple_log.info("="*250)
            self._log_execution_summary(state_data)
            
            yield {
                "status": "complete",
                "response": response
            }
            
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {str(e)}")
            yield {
                "status": "error",
                "error": str(e),
                "message": "An error occurred during processing"
            }
    
    def _format_final_response(self, state: WorkflowState) -> Dict[str, Any]:
        """Format the final response from workflow state"""
        
        final_answer = state.get("final_answer", {})
        tutor_interaction = state.get("tutor_interaction", {})
        
        response = {
            "success": True,
            "answer": final_answer,
            "tutor_interaction": tutor_interaction,
            "metadata": {
                "debate_rounds": state.get("current_round", 0),
                "convergence_score": state.get("convergence_score", 0),
                "retrieval_quality": state.get("retrieval_quality_score", 0),
                "retrieval_strategy": state.get("retrieval_strategy", ""),
                "moderator_decision": state.get("moderator_decision", ""),
                "processing_times": state.get("processing_times", {}),
                "total_processing_time": sum(state.get("processing_times", {}).values())
            },
            "debug_info": {
                "conversation_history": state.get("conversation_history", []),
                "error_messages": state.get("error_messages", []),
                "speculative_queries": state.get("speculative_queries", [])
            } if self.context.config.enable_debug_logging else {}
        }
        
        return response
    
    def _log_execution_summary(self, state: WorkflowState):
        """Log execution summary"""
        
        self.logger.info("EXECUTION SUMMARY:")
        simple_log.info("EXECUTION SUMMARY:")
        self.logger.info(f"  Query: {state.get('query', '')[:100]}...")
        simple_log.info(f"  Query: {state.get('query', '')[:100]}...")
        self.logger.info(f"  Debate Rounds: {state.get('current_round', 0)}")
        simple_log.info(f"  Debate Rounds: {state.get('current_round', 0)}")
        self.logger.info(f"  Final Decision: {state.get('moderator_decision', 'unknown')}")
        simple_log.info(f"  Final Decision: {state.get('moderator_decision', 'unknown')}")
        self.logger.info(f"  Convergence Score: {state.get('convergence_score', 0):.2f}")
        simple_log.info(f"  Convergence Score: {state.get('convergence_score', 0):.2f}")
        self.logger.info(f"  Retrieval Quality: {state.get('retrieval_quality_score', 0):.2f}")
        simple_log.info(f"  Retrieval Quality: {state.get('retrieval_quality_score', 0):.2f}")
        
        # Log timing
        times = state.get("processing_times", {})
        if times:
            self.logger.info("  Processing Times:")
            simple_log.info("  Processing Times:")
            for agent, time_val in times.items():
                self.logger.info(f"    - {agent}: {time_val:.2f}s")
                simple_log.info(f"    - {agent}: {time_val:.2f}s")
            self.logger.info(f"  Total Time: {sum(times.values()):.2f}s")
            simple_log.info(f"  Total Time: {sum(times.values()):.2f}s")
        
        # Log any errors
        errors = state.get("error_messages", [])
        if errors:
            self.logger.warning(f"  Errors encountered: {len(errors)}")
            for error in errors[:3]:
                self.logger.warning(f"    - {error[:100]}...")
    
    async def get_workflow_status(self) -> Dict[str, Any]:
        """Get current workflow status"""
        return {
            "status": "operational",
            "agents": {
                "retrieve": "ready",
                "strategist": "ready",
                "critic": "ready",
                "moderator": "ready",
                "reporter": "ready",
                "tutor": "ready"
            },
            "workflow_graph": {
                "nodes": list(self.workflow.nodes.keys()),
                "edges": str(self.workflow.edges)
            }
        }
    
    async def execute_with_content_streaming(
        self,
        query: str,
        course_id: str,
        session_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        heavy_model: Optional[str] = None,
        course_prompt: Optional[str] = None,
        max_rounds: int = 3
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute workflow with streaming of final content.
        
        This method runs all agent stages normally but streams the final reporter response
        content directly instead of collecting it completely first.
        """
        try:
            self.logger.info("="*250)
            simple_log.info("="*250)
            self.logger.info("STARTING STREAMING WORKFLOW EXECUTION")
            simple_log.info("STARTING STREAMING WORKFLOW EXECUTION")
            self.logger.info("="*250)
            simple_log.info("="*250)
            self.logger.info(f"Query: {query[:100]}...")
            simple_log.info(f"Query: {query[:100]}...")
            self.logger.info(f"Course: {course_id}")
            simple_log.info(f"Course: {course_id}")
            
            # Initialize state
            initial_state = initialize_state(
                query=query,
                course_id=course_id,
                session_id=session_id,
                metadata=metadata,
                course_prompt=course_prompt,
                max_rounds=max_rounds
            )
            
            # Run the workflow up to reporter stage
            config = {"configurable": {"thread_id": session_id}}
            
            # Track if we've reached reporter stage
            reached_reporter = False
            final_state = None
            
            # Stream execution for real-time updates
            async for event in self.app.astream(initial_state, config):
                for node, state_update in event.items():
                    # Yield progress updates for non-reporter stages
                    if node != "reporter":
                        yield {
                            "status": "in_progress",
                            "stage": node,
                            "message": f"Processing: {node}",
                            "state": state_update.get("workflow_status", "processing")
                        }
                    else:
                        # We've reached the reporter stage - stream its content
                        reached_reporter = True
                        self.logger.info("=== STREAMING REPORTER CONTENT ===")
                        simple_log.info("=== STREAMING REPORTER CONTENT ===")
                        
                        # Get the current state for reporter
                        current_state = await self.app.aget_state(config)
                        state_data = current_state.values
                        
                        # Create reporter instance if needed
                        from ai_agents.agents.reporter_agent import ReporterAgent
                        reporter = ReporterAgent(self.context)
                        
                        # Stream the reporter's response
                        full_content = ""
                        async for chunk in reporter.process_streaming(state_data):
                            if chunk:
                                full_content += chunk
                                yield {
                                    "status": "streaming",
                                    "content": chunk
                                }
                        
                        # Store the final answer in state
                        state_data["final_answer"] = {
                            "content": full_content,
                            "streamed": True
                        }
                        final_state = state_data
            
            # If we didn't reach reporter (shouldn't happen), get final state
            if not final_state:
                final_state_obj = await self.app.aget_state(config)
                final_state = final_state_obj.values
            
            # Format and yield final completion
            response = self._format_final_response(final_state)
            
            self.logger.info("="*250)
            simple_log.info("="*250)
            self.logger.info("STREAMING WORKFLOW COMPLETED")
            simple_log.info("STREAMING WORKFLOW COMPLETED")
            self.logger.info("="*250)
            simple_log.info("="*250)
            
            yield {
                "status": "complete",
                "response": response
            }
            
        except Exception as e:
            self.logger.error(f"Streaming workflow execution failed: {str(e)}")
            yield {
                "status": "error",
                "error": str(e),
                "message": "An error occurred during processing"
            }


# Convenience function for creating workflow
def create_workflow(
    llm_client,
    rag_service,
    config,
    logger: logging.Logger = None
) -> MultiAgentWorkflow:
    """
    Create a configured Multi-Agent Workflow.
    
    Args:
        llm_client: LLM client for agent chains
        rag_service: RAG service for retrieval
        config: Configuration object
        logger: Optional logger
        
    Returns:
        Configured MultiAgentWorkflow instance
    """
    
    context = AgentContext(
        llm_client=llm_client,
        rag_service=rag_service,
        config=config,
        logger=logger or logging.getLogger("langgraph")
    )
    
    return MultiAgentWorkflow(context, logger)

