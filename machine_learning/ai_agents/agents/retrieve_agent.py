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
        
        # DEBUG: Log initial results
        sources = initial_results.get('sources', [])
        self.logger.info(f"DEBUG: Initial RAG returned {len(sources)} sources")
        for i, source in enumerate(sources[:3]):
            score = source.get('score', 'N/A')
            content = source.get('content', '')[:50]
            self.logger.info(f"  Source {i+1}: Score={score}, Content='{content}...'")
        
        # Stage 2: Quality assessment 
        quality_score = self._assess_retrieval_quality(initial_results)
        self.logger.info(f"DEBUG: Quality score assessed as {quality_score:.3f} (threshold: {self.min_quality_threshold})")
        
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
        
        # DEBUG: Log formatting results
        self.logger.info(f"DEBUG: Final results has {len(final_results.get('sources', []))} sources")
        self.logger.info(f"DEBUG: Formatted context has {len(formatted_context)} items")
        
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
            # DEBUG: Always show first 3 chunks from this course for sanity check
            await self._debug_course_chunks(course_id, query)
            
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
    
    async def _debug_course_chunks(self, course_id: str, actual_query: str = None):
        """Debug: Show first 3 chunks from this course with similarity scores"""
        try:
            if not self.rag_service:
                self.logger.info(f"DEBUG: No RAG service available for course {course_id}")
                return
                
            # Get the vector client directly to query raw chunks
            vector_client = getattr(self.rag_service, 'vector_client', None)
            if not vector_client:
                self.logger.info(f"DEBUG: No vector client available for course {course_id}")
                return
                
            # Query for any 3 documents from this course (no similarity filtering)
            try:
                # First, get any chunks to show they exist
                raw_results = vector_client.similarity_search(
                    query="course content", 
                    k=3, 
                    filter={"course_id": course_id}
                )
                
                if raw_results:
                    self.logger.info(f"DEBUG: Found {len(raw_results)} chunks in course {course_id}")
                    
                    # If we have the actual query, show similarity scores with that query
                    if actual_query:
                        try:
                            scored_results = vector_client.similarity_search_with_score(
                                query=actual_query,
                                k=3,
                                filter={"course_id": course_id}
                            )
                            
                            self.logger.info(f"DEBUG: Similarity scores for query '{actual_query[:50]}...':")
                            for i, (doc, score) in enumerate(scored_results, 1):
                                content_preview = doc.page_content[:80] + '...' if len(doc.page_content) > 80 else doc.page_content
                                metadata = doc.metadata or {}
                                chunk_id = metadata.get('chunk_index', 'unknown')
                                self.logger.info(f"   {i}. Chunk {chunk_id} | Score: {score:.4f} | {content_preview}")
                                
                        except Exception as score_error:
                            self.logger.error(f"DEBUG: Error getting similarity scores: {score_error}")
                            # Fallback to showing chunks without scores
                            for i, doc in enumerate(raw_results, 1):
                                content_preview = doc.page_content[:80] + '...' if len(doc.page_content) > 80 else doc.page_content
                                metadata = doc.metadata or {}
                                chunk_id = metadata.get('chunk_index', 'unknown')
                                self.logger.info(f"   {i}. Chunk {chunk_id}: {content_preview}")
                    else:
                        # Just show the chunks without scores
                        for i, doc in enumerate(raw_results, 1):
                            content_preview = doc.page_content[:80] + '...' if len(doc.page_content) > 80 else doc.page_content
                            metadata = doc.metadata or {}
                            chunk_id = metadata.get('chunk_index', 'unknown')
                            self.logger.info(f"   {i}. Chunk {chunk_id}: {content_preview}")
                else:
                    self.logger.info(f"DEBUG: No chunks found in course {course_id} database")
                    
            except Exception as search_error:
                self.logger.error(f"DEBUG: Error searching course {course_id}: {search_error}")
                
        except Exception as e:
            self.logger.error(f"DEBUG: Failed to debug course chunks: {e}")

    def get_agent_metrics(self) -> Dict[str, Any]:
        """Get retrieval-specific metrics"""
        base_metrics = self.get_metrics()
        return {
            **base_metrics,
            "retrieval_strategy_distribution": getattr(self, '_strategy_stats', {}),
            "average_quality_score": getattr(self, '_avg_quality', 0.0)
        } 