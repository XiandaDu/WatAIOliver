"""
Retrieval Logger - Structured logging for the retrieve agent workflow.

Tracks sessions, retrievals, decisions, and quality metrics.
"""

import time
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
import json


class RetrievalLogger:
    """
    Structured logger for retrieval agent sessions.

    Tracks:
    - Session lifecycle (create, complete)
    - Individual retrievals (initial, expanded)
    - Decision agent outputs
    - Quality metrics and timing
    """

    def __init__(self, base_logger):
        """
        Initialize retrieval logger.

        Args:
            base_logger: The base Python logger instance
        """
        self.logger = base_logger
        self.sessions = {}  # Track active sessions

    async def create_session(
        self,
        session_id: str,
        course_id: str,
        query: str
    ) -> str:
        """
        Create a new retrieval session.

        Args:
            session_id: Unique session identifier (from state)
            course_id: Course being queried
            query: User's query

        Returns:
            session_uuid: UUID for this session (or fallback UUID on error)
        """
        try:
            session_uuid = str(uuid.uuid4())

            session_data = {
                "session_uuid": session_uuid,
                "session_id": session_id,
                "course_id": course_id,
                "query": query,
                "start_time": time.time(),
                "retrievals": [],
                "decisions": [],
                "status": "in_progress"
            }

            self.sessions[session_uuid] = session_data

            self.logger.info(
                f"[SESSION START] UUID={session_uuid} | "
                f"SessionID={session_id} | CourseID={course_id} | Query='{query[:100]}'"
            )

            return session_uuid
        except Exception as e:
            # Graceful fallback - return a UUID even if logging fails
            fallback_uuid = str(uuid.uuid4())
            try:
                self.logger.error(f"Failed to create session log: {e}")
            except:
                pass  # Even error logging failed - silent fail
            return fallback_uuid

    async def log_retrieval(
        self,
        session_uuid: str,
        retrieval_uuid: str,
        strategy: str,
        results: List[Dict[str, Any]],
        processing_time_ms: float
    ):
        """
        Log a retrieval operation.

        Args:
            session_uuid: Session this retrieval belongs to
            retrieval_uuid: Unique ID for this retrieval
            strategy: "initial" or "expanded"
            results: Retrieved documents with scores
            processing_time_ms: Time taken in milliseconds
        """
        try:
            if session_uuid not in self.sessions:
                self.logger.warning(f"Session {session_uuid} not found for retrieval logging")
                return

            retrieval_data = {
                "retrieval_uuid": retrieval_uuid,
                "strategy": strategy,
                "num_results": len(results),
                "sources": [
                    {
                        "score": r.get("score", 0.0),
                        "content_length": len(r.get("content", ""))
                    }
                    for r in results[:10]  # Top 10
                ],
                "processing_time_ms": processing_time_ms,
                "timestamp": time.time()
            }

            self.sessions[session_uuid]["retrievals"].append(retrieval_data)

            # Calculate average score
            scores = [r.get("score", 0.0) for r in results]
            avg_score = sum(scores) / len(scores) if scores else 0.0

            self.logger.info(
                f"[RETRIEVAL] SessionUUID={session_uuid} | "
                f"RetrievalUUID={retrieval_uuid} | "
                f"Strategy={strategy} | "
                f"Results={len(results)} | "
                f"AvgScore={avg_score:.3f} | "
                f"Time={processing_time_ms:.0f}ms"
            )
        except Exception as e:
            try:
                self.logger.error(f"Failed to log retrieval: {e}")
            except:
                pass  # Silent fail

    async def log_decision(
        self,
        session_uuid: str,
        retrieval_uuid: str,
        decision_data: Dict[str, Any],
        retry_count: int,
        input_data: Optional[Dict[str, Any]] = None
    ):
        """
        Log a decision agent's output with references to what it evaluated.

        Args:
            session_uuid: Session UUID
            retrieval_uuid: Which retrieval this decision is for
            decision_data: Decision agent output (decision, reason, confidence)
            retry_count: Current retry iteration
            input_data: Optional dict with references to what LLM evaluated
                - num_results: Number of results evaluated
                - top_scores: Top 5 scores shown to LLM
                - query: Query being evaluated
        """
        try:
            if session_uuid not in self.sessions:
                self.logger.warning(f"Session {session_uuid} not found for decision logging")
                return

            decision_log = {
                "retrieval_uuid": retrieval_uuid,
                "decision": decision_data.get("decision"),
                "reason": decision_data.get("reason"),
                "confidence": decision_data.get("confidence"),
                "retry_count": retry_count,
                "timestamp": time.time()
            }

            # Add input references if provided
            if input_data:
                decision_log["input_references"] = {
                    "num_results_evaluated": input_data.get("num_results", 0),
                    "top_scores_shown_to_llm": input_data.get("top_scores", []),
                    "query": input_data.get("query", "")
                }

            self.sessions[session_uuid]["decisions"].append(decision_log)

            # Format log message with references
            log_msg = (
                f"[DECISION] SessionUUID={session_uuid} | "
                f"RetrievalUUID={retrieval_uuid} | "
                f"Decision={decision_data.get('decision')} | "
                f"Reason='{decision_data.get('reason')[:100]}' | "
                f"Confidence={decision_data.get('confidence'):.2f} | "
                f"Retry={retry_count}"
            )

            if input_data:
                top_scores = input_data.get("top_scores", [])
                if top_scores:
                    scores_str = ", ".join([f"{s:.3f}" for s in top_scores[:5]])
                    log_msg += f" | EvaluatedScores=[{scores_str}]"

            self.logger.info(log_msg)
        except Exception as e:
            try:
                self.logger.error(f"Failed to log decision: {e}")
            except:
                pass  # Silent fail

    async def complete_session(
        self,
        session_uuid: str,
        final_quality_score: float,
        total_retries: int
    ):
        """
        Mark session as complete and log final metrics.

        Args:
            session_uuid: Session to complete
            final_quality_score: Final quality score of results
            total_retries: Total number of retries performed
        """
        try:
            if session_uuid not in self.sessions:
                self.logger.warning(f"Session {session_uuid} not found for completion")
                return

            session = self.sessions[session_uuid]
            session["status"] = "completed"
            session["end_time"] = time.time()
            session["final_quality_score"] = final_quality_score
            session["total_retries"] = total_retries

            total_time_ms = (session["end_time"] - session["start_time"]) * 1000

            self.logger.info(
                f"[SESSION COMPLETE] UUID={session_uuid} | "
                f"FinalScore={final_quality_score:.3f} | "
                f"Retries={total_retries} | "
                f"TotalTime={total_time_ms:.0f}ms"
            )
        except Exception as e:
            try:
                self.logger.error(f"Failed to complete session: {e}")
            except:
                pass  # Silent fail

    async def log_quality_metrics(
        self,
        session_uuid: str,
        initial_score: Optional[float],
        final_score: float,
        retrieval_strategy_count: int,
        was_expanded: bool,
        total_time_ms: float
    ):
        """
        Log detailed quality metrics for analytics.

        Args:
            session_uuid: Session UUID
            initial_score: Score from initial retrieval (None if not calculated)
            final_score: Final score after all operations
            retrieval_strategy_count: Number of retrieval strategies used (1 = initial only, 2+ = expanded)
            was_expanded: Whether query expansion was triggered
            total_time_ms: Total processing time
        """
        try:
            if session_uuid not in self.sessions:
                self.logger.warning(f"Session {session_uuid} not found for quality metrics")
                return

            session = self.sessions[session_uuid]

            metrics = {
                "session_uuid": session_uuid,
                "session_id": session.get("session_id"),
                "initial_score": initial_score,
                "final_score": final_score,
                "score_improvement": (final_score - initial_score) if initial_score else None,
                "retrieval_strategy_count": retrieval_strategy_count,
                "was_expanded": was_expanded,
                "total_retries": session.get("total_retries", 0),
                "total_time_ms": total_time_ms,
                "num_retrievals": len(session.get("retrievals", [])),
                "num_decisions": len(session.get("decisions", []))
            }

            # Log as structured JSON for easy parsing
            self.logger.info(f"[QUALITY METRICS] {json.dumps(metrics)}")
        except Exception as e:
            try:
                self.logger.error(f"Failed to log quality metrics: {e}")
            except:
                pass  # Silent fail

    def get_session_summary(self, session_uuid: str) -> Optional[Dict[str, Any]]:
        """
        Get a summary of a session for debugging.

        Args:
            session_uuid: Session to summarize

        Returns:
            Session summary dict or None if not found
        """
        if session_uuid not in self.sessions:
            return None

        session = self.sessions[session_uuid]

        return {
            "session_uuid": session_uuid,
            "query": session.get("query"),
            "status": session.get("status"),
            "num_retrievals": len(session.get("retrievals", [])),
            "num_decisions": len(session.get("decisions", [])),
            "total_retries": session.get("total_retries", 0),
            "final_score": session.get("final_quality_score")
        }
