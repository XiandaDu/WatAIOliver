"""
Tutor Agent - Intelligent User Interaction Manager

Manages direct interaction with users, transforming Q&A into dynamic, personalized learning experiences.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from ai_agents.agents.base_agent import BaseAgent, AgentInput, AgentOutput, AgentRole


class TutorAgent(BaseAgent):
    """
    Tutor Agent - Manages user interaction lifecycle
    
    Responsibilities:
    - Guide: Present contextual guidance before answers
    - Analyze: Monitor user behavior patterns
    - Test: Generate comprehension assessments
    - Discipline: Enforce learning-focused interactions
    """
    
    def __init__(self, config, llm_client=None, logger=None):
        super().__init__(agent_role=AgentRole.TUTOR, config=config, llm_client=llm_client, logger=logger)
        
        # User session tracking
        self.user_sessions = {}
        
        # Behavioral analysis thresholds
        self.similarity_threshold = 0.8
        self.consecutive_similar_limit = 3
        self.comprehension_threshold = 0.6
        self.cooldown_duration_minutes = 15
        
    async def process(self, agent_input: AgentInput) -> AgentOutput:
        """Process tutor interaction request"""
        try:
            session_id = agent_input.session_id
            query = agent_input.query
            metadata = agent_input.metadata
            
            # Extract final answer from Reporter
            final_answer = metadata.get("final_answer", {})
            conversation_history = metadata.get("conversation_history", [])
            
            # Initialize or update user session
            self._update_user_session(session_id, query, conversation_history)
            
            # Determine current interaction state
            interaction_state = self._analyze_user_behavior(session_id, query)
            
            # Generate appropriate response based on state
            if interaction_state == "cooldown":
                response = self._generate_cooldown_response(session_id)
            elif interaction_state == "test":
                response = self._generate_test_interaction(session_id, final_answer)
            else:  # guide or normal
                response = self._generate_guided_response(session_id, final_answer, query)
            
            return AgentOutput(
                success=True,
                content=response,
                metadata={
                    "interaction_state": interaction_state,
                    "session_metrics": self._get_session_metrics(session_id)
                },
                processing_time=time.time(),
                agent_role=self.agent_role
            )
            
        except Exception as e:
            self.logger.error(f"Tutor processing failed: {e}")
            return AgentOutput(
                success=False,
                content={},
                metadata={},
                processing_time=time.time(),
                agent_role=self.agent_role,
                error_message=str(e)
            )
    
    def _update_user_session(self, session_id: str, query: str, history: List[Dict]):
        """Update user session tracking"""
        if session_id not in self.user_sessions:
            self.user_sessions[session_id] = {
                "queries": [],
                "state": "guide",
                "test_scores": [],
                "cooldown_until": None,
                "created_at": datetime.now()
            }
        
        session = self.user_sessions[session_id]
        session["queries"].append({
            "query": query,
            "timestamp": datetime.now(),
            "vector": self._vectorize_query(query)  # Simplified - would use actual embedding
        })
        
        # Keep only recent queries (last 10)
        if len(session["queries"]) > 10:
            session["queries"] = session["queries"][-10:]
    
    def _analyze_user_behavior(self, session_id: str, current_query: str) -> str:
        """Analyze user behavior to determine interaction state"""
        session = self.user_sessions.get(session_id, {})
        
        # Check cooldown status
        cooldown_until = session.get("cooldown_until")
        if cooldown_until and datetime.now() < cooldown_until:
            return "cooldown"
        
        # Analyze query similarity patterns
        queries = session.get("queries", [])
        if len(queries) >= self.consecutive_similar_limit:
            recent_queries = queries[-self.consecutive_similar_limit:]
            similarity_count = self._count_similar_queries(recent_queries)
            
            if similarity_count >= self.consecutive_similar_limit - 1:
                # Switch to test mode
                session["state"] = "test"
                return "test"
        
        return session.get("state", "guide")
    
    def _count_similar_queries(self, queries: List[Dict]) -> int:
        """Count similar queries in the list"""
        # Simplified similarity check - in production would use actual vector similarity
        if len(queries) < 2:
            return 0
        
        similar_count = 0
        for i in range(1, len(queries)):
            if self._calculate_similarity(queries[i]["query"], queries[i-1]["query"]) > self.similarity_threshold:
                similar_count += 1
        
        return similar_count
    
    def _calculate_similarity(self, query1: str, query2: str) -> float:
        """Calculate query similarity (simplified implementation)"""
        # Simplified Jaccard similarity - in production would use vector similarity
        words1 = set(query1.lower().split())
        words2 = set(query2.lower().split())
        
        if not words1 and not words2:
            return 1.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _vectorize_query(self, query: str) -> List[float]:
        """Vectorize query for similarity analysis (simplified)"""
        # Simplified - in production would use actual embedding model
        return [hash(word) % 100 / 100.0 for word in query.split()[:10]]
    
    def _generate_guided_response(self, session_id: str, final_answer: Dict, query: str) -> Dict:
        """Generate guided learning response"""
        return {
            "interaction_type": "guided_learning",
            "elements": [
                {
                    "type": "guidance",
                    "content": self._generate_guidance_text(query, final_answer)
                },
                {
                    "type": "answer",
                    "content": final_answer
                },
                {
                    "type": "reflection_prompt",
                    "content": self._generate_reflection_prompt(final_answer)
                }
            ]
        }
    
    def _generate_test_interaction(self, session_id: str, final_answer: Dict) -> Dict:
        """Generate comprehension test"""
        quiz_questions = self._generate_quiz_questions(final_answer)
        
        return {
            "interaction_type": "comprehension_test",
            "elements": [
                {
                    "type": "test_intro",
                    "content": "I notice you've asked similar questions recently. Let's check your understanding with a quick quiz:"
                },
                {
                    "type": "answer",
                    "content": final_answer
                },
                {
                    "type": "quiz",
                    "content": quiz_questions
                }
            ]
        }
    
    def _generate_cooldown_response(self, session_id: str) -> Dict:
        """Generate cooldown message"""
        session = self.user_sessions[session_id]
        cooldown_until = session.get("cooldown_until")
        remaining_time = cooldown_until - datetime.now() if cooldown_until else timedelta(0)
        
        return {
            "interaction_type": "cooldown",
            "elements": [
                {
                    "type": "cooldown_message",
                    "content": f"It seems you need more time to review the material. Please take {remaining_time.seconds // 60} more minutes to study the provided resources before asking new questions."
                },
                {
                    "type": "study_resources",
                    "content": self._get_study_recommendations(session_id)
                }
            ]
        }
    
    def _generate_guidance_text(self, query: str, final_answer: Dict) -> str:
        """Generate contextual guidance text"""
        # Simplified guidance generation
        topic_keywords = self._extract_topic_keywords(query)
        
        if any(keyword in query.lower() for keyword in ["lagrange", "optimization", "constraint"]):
            return "Before diving into this optimization problem, recall that Lagrange multipliers help us find extrema of functions subject to constraints. The key insight is that at the optimal point, the gradients must be parallel."
        elif any(keyword in query.lower() for keyword in ["circuit", "resistance", "voltage"]):
            return "Let's approach this circuit analysis step by step. Remember Ohm's law and Kirchhoff's rules as our fundamental tools."
        else:
            return "Let's work through this problem systematically, building on the fundamental concepts."
    
    def _generate_reflection_prompt(self, final_answer: Dict) -> str:
        """Generate reflection prompt based on answer content"""
        return "Take a moment to consider: What was the key insight that made this solution work? How might you apply this approach to similar problems?"
    
    def _generate_quiz_questions(self, final_answer: Dict) -> Dict:
        """Generate quiz questions based on final answer"""
        # Simplified quiz generation - in production would use LLM
        return {
            "questions": [
                {
                    "id": 1,
                    "question": "What is the main concept demonstrated in this solution?",
                    "type": "multiple_choice",
                    "options": ["A) Basic algebra", "B) Advanced calculus", "C) The core principle from the answer", "D) Memorization"],
                    "correct": "C"
                }
            ]
        }
    
    def _extract_topic_keywords(self, query: str) -> List[str]:
        """Extract topic keywords from query"""
        # Simplified keyword extraction
        return [word.lower() for word in query.split() if len(word) > 3]
    
    def _get_study_recommendations(self, session_id: str) -> List[str]:
        """Get personalized study recommendations"""
        return [
            "Review the fundamental concepts covered in the recent answers",
            "Practice similar problems with different parameters",
            "Focus on understanding the underlying principles rather than memorizing steps"
        ]
    
    def _get_session_metrics(self, session_id: str) -> Dict:
        """Get session performance metrics"""
        session = self.user_sessions.get(session_id, {})
        return {
            "total_queries": len(session.get("queries", [])),
            "current_state": session.get("state", "guide"),
            "average_test_score": sum(session.get("test_scores", [])) / max(len(session.get("test_scores", [])), 1),
            "session_duration": (datetime.now() - session.get("created_at", datetime.now())).total_seconds()
        }
    
    def process_quiz_response(self, session_id: str, quiz_response: Dict) -> Dict:
        """Process user's quiz response and update state"""
        session = self.user_sessions.get(session_id, {})
        
        # Calculate score (simplified)
        score = self._calculate_quiz_score(quiz_response)
        session.setdefault("test_scores", []).append(score)
        
        if score < self.comprehension_threshold:
            # Trigger cooldown
            session["cooldown_until"] = datetime.now() + timedelta(minutes=self.cooldown_duration_minutes)
            session["state"] = "cooldown"
            
            return {
                "result": "needs_review",
                "score": score,
                "message": "Your score indicates you need more time to review the material."
            }
        else:
            # Reset to normal state
            session["state"] = "guide"
            return {
                "result": "passed",
                "score": score,
                "message": "Great job! You can continue asking questions."
            }
    
    def _calculate_quiz_score(self, quiz_response: Dict) -> float:
        """Calculate quiz score"""
        # Simplified scoring - in production would be more sophisticated
        correct_answers = quiz_response.get("correct_count", 0)
        total_questions = quiz_response.get("total_questions", 1)
        return correct_answers / total_questions 