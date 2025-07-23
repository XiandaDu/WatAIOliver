"""
Retrieve Agent - Enhanced RAG Integration

This agent integrates directly with the existing RAG system and adds
speculative query reframing capabilities on top of it.
"""

import asyncio
from typing import Dict, Any, List, Optional

from ai_agents.agents.base_agent import BaseAgent, AgentRole, AgentInput, AgentOutput
from ai_agents.config import SpeculativeAIConfig


class RetrieveAgent(BaseAgent):
    """Enhanced retrieval agent that integrates with existing RAG system"""
    
    def __init__(
        self,
        config: SpeculativeAIConfig,
        llm_client=None,
        rag_service=None,
        logger=None
    ):
        super().__init__(
            agent_role=AgentRole.RETRIEVE,
            config=config,
            llm_client=llm_client,
            logger=logger
        )
        
        self.rag_service = rag_service
        
        # Quality thresholds for triggering speculative retrieval
        self.min_quality_threshold = 0.7
        self.min_results_count = 3
        
    async def process(self, agent_input: AgentInput) -> AgentOutput:
        """Execute enhanced retrieval with speculative query reframing"""
        
        # Extract course_id from metadata  
        course_id = agent_input.metadata.get('course_id')
        if not course_id:
            return AgentOutput(
                success=False,
                content={},
                metadata={},
                processing_time=0.0,
                agent_role=self.agent_role,
                error_message="course_id required for retrieval"
            )
        
        # Stage 1: Initial RAG retrieval using existing system
        initial_results = await self._perform_rag_query(agent_input.query, course_id)
        
        if not initial_results:
            return AgentOutput(
                success=False,
                content={"retrieval_results": [], "quality_assessment": {"score": 0.0}},
                metadata={"retrieval_strategy": "failed"},
                processing_time=0.0,
                agent_role=self.agent_role,
                error_message="Initial RAG retrieval failed"
            )
        
        # Stage 2: Quality assessment 
        quality_score = self._assess_retrieval_quality(initial_results)
        
        # Stage 3: Speculative reframing if quality is poor
        if quality_score < self.min_quality_threshold and self.llm_client:
            reframed_results = await self._speculative_reframing(
                agent_input.query, 
                course_id, 
                initial_results
            )
            
            if reframed_results:
                # Merge and deduplicate results
                final_results = self._merge_results(initial_results, reframed_results)
                strategy = "speculative_enhanced"
            else:
                final_results = initial_results
                strategy = "initial_only"
        else:
            final_results = initial_results
            strategy = "initial_sufficient"
        
        # Format final results for downstream agents
        formatted_context = self._format_for_agents(final_results)
        
        # Log clean chunk summary
        self._log_retrieved_chunks(formatted_context, strategy)
        
        return AgentOutput(
            success=True,
            content={
                "retrieval_results": formatted_context,
                "quality_assessment": {
                    "score": max(quality_score, self._assess_retrieval_quality(final_results)),
                    "initial_count": len(initial_results.get('sources', [])),
                    "final_count": len(formatted_context)
                }
            },
            metadata={
                "retrieval_strategy": strategy,
                "quality_improvement": strategy == "speculative_enhanced"
            },
            processing_time=0.0,
            agent_role=self.agent_role
        )
    
    async def _perform_rag_query(self, query: str, course_id: str) -> Optional[Dict[str, Any]]:
        """Perform RAG query using existing system"""
        try:
            if self.rag_service:
                return self.rag_service.answer_question(course_id, query)
            else:
                self.logger.warning("No RAG service available - using mock results")
                return {
                    "success": True,
                    "answer": "Mock RAG response",
                    "sources": [{"content": "Mock content", "score": 0.8}]
                }
        except Exception as e:
            self.logger.error(f"RAG query failed: {e}")
            return None
    
    def _assess_retrieval_quality(self, rag_result: Dict[str, Any]) -> float:
        """Assess quality of RAG retrieval results"""
        if not rag_result or not rag_result.get('success'):
            return 0.0
        
        sources = rag_result.get('sources', [])
        if len(sources) < self.min_results_count:
            return 0.3
        
        # Calculate average relevance score
        scores = []
        for source in sources:
            score = source.get('score', 0)
            if score and score != 'N/A':
                try:
                    scores.append(float(score))
                except (ValueError, TypeError):
                    continue
        if not scores:
            return 0.5
        
        avg_score = sum(scores) / len(scores)
        return min(avg_score * 1.2, 1.0)  # Boost slightly, cap at 1.0
    
    async def _speculative_reframing(
        self, 
        original_query: str, 
        course_id: str, 
        initial_results: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Generate alternative queries and perform parallel retrieval"""
        
        try:
            # Generate alternative queries using LLM
            alternative_queries = await self._generate_alternative_queries(original_query)
            
            if not alternative_queries:
                return None
            
            # Perform parallel retrieval for alternative queries
            tasks = []
            for alt_query in alternative_queries:
                task = self._perform_rag_query(alt_query, course_id)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Find the best alternative result
            best_result = None
            best_score = 0.0
            
            for result in results:
                if isinstance(result, dict) and result.get('success'):
                    score = self._assess_retrieval_quality(result)
                    if score > best_score:
                        best_score = score
                        best_result = result
            
            return best_result
            
        except Exception as e:
            self.logger.error(f"Speculative reframing failed: {e}")
            return None
    
    async def _generate_alternative_queries(self, original_query: str) -> List[str]:
        """Generate alternative queries using LLM"""
        try:
            prompt = f"""
            The original query "{original_query}" didn't retrieve high-quality results.
            Generate 2-3 alternative queries that might find better information:
            
            1. A more specific version
            2. A broader conceptual version  
            3. A query using different terminology
            
            Return only the alternative queries, one per line.
            """
            
            response = self.llm_client.generate(prompt)
            queries = [q.strip() for q in response.split('\n') if q.strip() and not q.startswith('#')]
            return queries[:3]  # Limit to 3 alternatives
            
        except Exception as e:
            self.logger.error(f"Alternative query generation failed: {e}")
            return []
    
    def _merge_results(
        self, 
        initial_results: Dict[str, Any], 
        reframed_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge and deduplicate results from multiple retrievals"""
        
        initial_sources = initial_results.get('sources', [])
        reframed_sources = reframed_results.get('sources', [])
        
        # Simple deduplication by content similarity
        merged_sources = initial_sources.copy()
        
        for new_source in reframed_sources:
            new_content = new_source.get('content', '')
            is_duplicate = False
            
            for existing_source in merged_sources:
                existing_content = existing_source.get('content', '')
                # Simple overlap check
                if len(set(new_content.split()) & set(existing_content.split())) > len(new_content.split()) * 0.7:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                merged_sources.append(new_source)
        
        # Return merged result
        return {
            "success": True,
            "answer": reframed_results.get('answer', initial_results.get('answer')),
            "sources": merged_sources
        }
    
    def _format_for_agents(self, rag_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format RAG results for downstream agent consumption"""
        
        if not rag_result or not rag_result.get('success'):
            return []
        
        sources = rag_result.get('sources', [])
        formatted_results = []
        
        for i, source in enumerate(sources):
            formatted_item = {
                "index": i,
                "content": source.get('content', ''),
                "score": source.get('score', 0.0),
                "source": source.get('metadata', {})
            }
            formatted_results.append(formatted_item)
        
        return formatted_results
    
    def _log_retrieved_chunks(self, chunks: List[Dict[str, Any]], strategy: str):
        """Log retrieved chunks in a clean, organized format"""
        if not chunks:
            self.logger.info("No chunks retrieved")
            return
            
        self.logger.info(f"Retrieved {len(chunks)} chunks using {strategy}:")
        for chunk in chunks:
            score = chunk.get('score', 0.0)
            # Handle the score properly - it might be 'N/A', None, or a number
            if score == 'N/A' or score is None:
                score_display = "N/A"
            else:
                try:
                    score_float = float(score)
                    score_display = f"{score_float:.3f}"
                except (ValueError, TypeError):
                    score_display = "N/A"
            
            content_preview = chunk.get('content', '')[:50] + '...' if len(chunk.get('content', '')) > 50 else chunk.get('content', '')
            self.logger.info(f"   • Similarity: {score_display} | {content_preview}")
    
    def get_agent_metrics(self) -> Dict[str, Any]:
        """Get retrieval-specific metrics"""
        base_metrics = self.get_metrics()
        return {
            **base_metrics,
            "retrieval_strategy_distribution": getattr(self, '_strategy_stats', {}),
            "average_quality_score": getattr(self, '_avg_quality', 0.0)
        } 