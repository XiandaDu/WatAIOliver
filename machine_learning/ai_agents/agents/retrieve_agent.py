"""
Retrieve Agent - LangChain Implementation

Enhanced retrieval with speculative query reframing using LangChain tools and chains.
Integrates with existing RAG service while maintaining LangChain native approach.
"""

import asyncio
import time
import json
from typing import Dict, Any, List
from langchain.schema import Document
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain.tools import Tool
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.messages import HumanMessage, SystemMessage

from ai_agents.state import WorkflowState, RetrievalResult, log_agent_execution
from ai_agents.utils import (
    create_langchain_llm, 
    perform_rag_retrieval, 
    debug_course_chunks,
    format_rag_results_for_agents
)


class RetrieveAgent:
    """
    Speculative Retriever using LangChain chains and tools.
    
    Implements the complete retrieval workflow:
    1. Initial RAG query
    2. Quality assessment
    3. Speculative query reframing if needed
    4. Result merging and re-ranking
    """
    
    def __init__(self, context):
        self.context = context
        self.logger = context.logger.getChild("retrieve")
        self.rag_service = context.rag_service
        self.llm_client = context.llm_client
        
        # Create LangChain-compatible LLM
        self.llm = create_langchain_llm(self.llm_client)
        
        # Quality thresholds
        self.min_quality_threshold = 0.7
        self.min_results_count = 3
        
        # Initialize chains
        self._setup_chains()
        
    def _setup_chains(self):
        """Setup LangChain chains for different retrieval tasks"""
        
        # Chain for quality assessment
        self.quality_assessment_chain = LLMChain(
            llm=self.llm,
            prompt=ChatPromptTemplate.from_messages([
                SystemMessage(content="""You are a retrieval quality assessor. 
                Analyze the relevance of retrieved documents to the query.
                Score from 0 to 1, where 1 is perfect relevance."""),
                HumanMessage(content="""Query: {query}
                
Retrieved Documents:
{documents}

Provide a quality score (0-1) and brief explanation.
Format: SCORE: X.XX | REASON: ...""")
            ])
        )
        
        # Chain for query reframing
        self.query_reframing_chain = LLMChain(
            llm=self.llm,
            prompt=ChatPromptTemplate.from_messages([
                SystemMessage(content="""You are an expert at reformulating queries for better retrieval.
                When initial retrieval quality is poor, generate alternative queries that might yield better results."""),
                HumanMessage(content="""Original Query: {query}
                
Initial Results Quality: {quality_score}
Quality Issues: {quality_issues}

Generate 3 alternative query formulations that:
1. Use different terminology or perspectives
2. Are more specific or break down the concept
3. Target different aspects of the topic

Format each query on a new line starting with "QUERY:".""")
            ])
        )
        
        # Chain for result re-ranking
        self.reranking_chain = LLMChain(
            llm=self.llm,
            prompt=ChatPromptTemplate.from_messages([
                SystemMessage(content="""You are a document re-ranker. Score each document's relevance to the query."""),
                HumanMessage(content="""Query: {query}

Document: {document}

Score this document's relevance from 0 to 1.
Format: SCORE: X.XX""")
            ])
        )
    
    def _format_retrieval_output(self, results: List[RetrievalResult], strategy: str = "initial", no_results_suggestion: str = None) -> Dict[str, Any]:
        """Format retrieval results as JSON output matching the desired format"""
        if not results:
            return {
                "status": "no_results",
                "suggestion": no_results_suggestion or "Try rephrasing your query to be more specific or break it down into smaller concepts."
            }
        
        formatted_results = []
        for i, result in enumerate(results):
            formatted_results.append({
                "text": result.get('content', ''),
                "score": float(result.get('score', 0.0)),
                "source": result.get('source', 'unknown'),
                "retrieval_path": strategy
            })
        
        return formatted_results
    
    async def __call__(self, state: WorkflowState) -> WorkflowState:
        """Execute retrieval with speculative reframing"""
        start_time = time.time()
        
        try:
            self.logger.info("="*250)
            self.logger.info("RETRIEVE AGENT - ENHANCED RETRIEVAL")
            self.logger.info("="*250)
            
            query = state["query"]
            course_id = state["course_id"]
            
            # Stage 1: Initial RAG retrieval (matching legacy approach)
            self.logger.info(f"Query: '{query}'")
            self.logger.info(f"Course ID: {course_id}")
            self.logger.info("Performing initial retrieval...")
            
            # Debug chunks first (like legacy)
            await debug_course_chunks(self.rag_service, course_id, query, self.logger)
            
            # Perform RAG query using existing service
            initial_rag_result = await perform_rag_retrieval(
                self.rag_service, query, course_id, self.logger
            )
            
            if not initial_rag_result:
                self.logger.error("Initial RAG retrieval completely failed")
                state["error_messages"].append("Initial RAG retrieval failed")
                state["workflow_status"] = "failed"
                return state
            
            # Convert to our RetrievalResult format
            initial_results = self._convert_rag_to_retrieval_results(initial_rag_result)
            
            # Stage 2: Quality assessment using LangChain chain
            quality_score = await self._assess_quality_with_chain(state["query"], initial_results)
            self.logger.info(f"Quality Score: {quality_score:.3f}")
            
            # Stage 3: Speculative reframing if needed
            final_results = initial_results
            final_rag_result = initial_rag_result
            retrieval_strategy = "initial"
            speculative_queries = []
            
            if quality_score < self.min_quality_threshold and self.llm_client:
                self.logger.info("Quality too low - triggering speculative reframing")
                
                # Generate alternative queries using LangChain
                reframed_queries = await self._generate_reframed_queries(
                    query, quality_score, initial_rag_result
                )
                speculative_queries = reframed_queries
                
                if reframed_queries:
                    # Perform parallel retrieval for alternative queries
                    best_alternative = await self._parallel_retrieval_with_scoring(
                        reframed_queries, course_id, query
                    )
                    
                    if best_alternative:
                        # Store which query produced the best alternative for tracking
                        best_query_index = reframed_queries.index(best_alternative.get('query', reframed_queries[0])) if 'query' in best_alternative else 0
                        retrieval_strategy = f"refined_query_{best_query_index + 1}"
                        
                        # Merge results (like legacy)
                        final_rag_result = self._merge_rag_results(initial_rag_result, best_alternative)
                        final_results = self._convert_rag_to_retrieval_results(final_rag_result)
                        
                        # Recalculate quality using LangChain chain
                        quality_score = await self._assess_quality_with_chain(state["query"], final_results)
                        self.logger.info(f"Enhanced quality: {quality_score:.3f}")
                    else:
                        self.logger.info("No good alternatives found - using initial results")
                        retrieval_strategy = "initial_only"
            
            # Format output as JSON
            json_output = self._format_retrieval_output(
                final_results[:10],  # Top 10 results
                strategy=retrieval_strategy,
                no_results_suggestion=f"Try rephrasing '{query}' to be more specific about the course material."
            )
            
            # Log the JSON output
            self.logger.info("="*250)
            self.logger.info("RETRIEVAL OUTPUT (JSON)")
            self.logger.info("="*250)
            self.logger.info(json.dumps(json_output, indent=2))
            self.logger.info("="*250)
            
            # Update state
            state["retrieval_results"] = final_results[:10]  # Top 10 results
            state["retrieval_quality_score"] = quality_score
            state["retrieval_strategy"] = retrieval_strategy
            state["speculative_queries"] = speculative_queries
            state["workflow_status"] = "retrieving"
            
            # Add formatted JSON output to state for downstream agents
            if "formatted_retrieval_output" not in state:
                state["formatted_retrieval_output"] = json_output
            else:
                state["formatted_retrieval_output"] = json_output
            
            # Log execution
            processing_time = time.time() - start_time
            log_agent_execution(
                state=state,
                agent_name="Retrieve",
                input_summary=f"Query: {query[:100]}",
                output_summary=f"Retrieved {len(final_results)} chunks, quality: {quality_score:.3f}, JSON output logged",
                processing_time=processing_time,
                success=True
            )
            
            self.logger.info(f"Retrieval completed in {processing_time:.2f}s")
            
        except Exception as e:
            self.logger.error(f"Retrieval failed: {str(e)}")
            state["error_messages"].append(f"Retrieve agent error: {str(e)}")
            state["workflow_status"] = "failed"
            
            log_agent_execution(
                state=state,
                agent_name="Retrieve",
                input_summary=f"Query: {state['query'][:100]}",
                output_summary=f"Error: {str(e)}",
                processing_time=time.time() - start_time,
                success=False
            )
        
        return state
    
    def _convert_rag_to_retrieval_results(self, rag_result: Dict[str, Any]) -> List[RetrievalResult]:
        """Convert RAG service result to RetrievalResult format"""
        if not rag_result or not rag_result.get('success'):
            return []
        
        results = []
        sources = rag_result.get('sources', [])
        
        for source in sources:
            results.append(RetrievalResult(
                content=source.get('content', ''),
                score=source.get('score', 0.0),
                source=source.get('metadata', {}).get('source', 'unknown'),
                metadata=source.get('metadata', {})
            ))
        
        return results
    
    async def _assess_quality_with_chain(self, query: str, results: List[RetrievalResult]) -> float:
        """Assess retrieval quality using LangChain"""
        if not results:
            return 0.0
        
        try:
            # Format documents for assessment
            doc_text = "\n\n".join([
                f"Document {i+1} (score: {r['score']:.3f}):\n{r['content'][:500]}"
                for i, r in enumerate(results[:5])
            ])
            
            # Run quality assessment chain
            response = await self.quality_assessment_chain.arun(
                query=query,
                documents=doc_text
            )
            
            # Parse score from response
            if "SCORE:" in response:
                score_str = response.split("SCORE:")[1].split("|")[0].strip()
                return float(score_str)
            
            # Fallback to average document scores
            return sum(r["score"] for r in results[:5]) / min(len(results), 5)
            
        except Exception as e:
            self.logger.error(f"Quality assessment failed: {str(e)}")
            return 0.5
    
    async def _generate_reframed_queries(
        self, 
        query: str, 
        quality_score: float, 
        initial_rag_result: Dict[str, Any]
    ) -> List[str]:
        """Generate reframed queries using LangChain"""
        try:
            # Identify quality issues from RAG result
            quality_issues = self._analyze_rag_quality_issues(initial_rag_result)
            
            # Generate reframed queries
            response = await self.query_reframing_chain.arun(
                query=query,
                quality_score=quality_score,
                quality_issues=quality_issues
            )
            
            # Parse queries from response
            queries = []
            for line in response.split("\n"):
                if line.startswith("QUERY:"):
                    query = line.replace("QUERY:", "").strip()
                    # Filter out placeholder queries like {query_alternative_1}
                    if not (query.startswith("{") and query.endswith("}")):
                        queries.append(query)
            
            # If no valid queries from QUERY: format, try to parse the response differently
            if not queries:
                lines = [line.strip() for line in response.split("\n") if line.strip()]
                for line in lines:
                    # Skip numbered items, empty lines, or placeholder templates
                    if (line and 
                        not line.startswith(("1.", "2.", "3.", "#", "QUERY:", "Alternative")) and
                        not (line.startswith("{") and line.endswith("}")) and
                        len(line) > 10):  # Reasonable query length
                        queries.append(line)
                        if len(queries) >= 3:  # Limit to 3
                            break
            
            queries = queries[:3]  # Ensure we limit to 3 queries
            
            self.logger.info(f"Generated {len(queries)} reframed queries")
            for i, q in enumerate(queries, 1):
                self.logger.info(f"  {i}. {q}")
            
            return queries
            
        except Exception as e:
            self.logger.error(f"Query reframing failed: {str(e)}")
            return []
    
    async def _parallel_retrieval_with_scoring(
        self, 
        queries: List[str], 
        course_id: str,
        original_query: str
    ) -> Dict[str, Any]:
        """Perform parallel retrieval and find best alternative (like legacy)"""
        self.logger.info(f"\nPerforming parallel retrieval for {len(queries)} alternative queries:")
        for i, q in enumerate(queries, 1):
            self.logger.info(f"  {i}. '{q}'")
        
        # Perform parallel retrieval
        tasks = [
            perform_rag_retrieval(self.rag_service, q, course_id, self.logger)
            for q in queries
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Find best alternative (matching legacy logic)
        best_result = None
        best_score = 0.0
        best_query_idx = -1
        
        self.logger.info("\nEvaluating alternative query results:")
        for i, (result, query) in enumerate(zip(results, queries)):
            if isinstance(result, dict) and result.get('success'):
                # Convert to RetrievalResult format and use chain for quality assessment
                alternative_results = self._convert_rag_to_retrieval_results(result)
                score = await self._assess_quality_with_chain(original_query, alternative_results)
                sources_count = len(result.get('sources', []))
                self.logger.info(f"  Alternative {i+1}: Score={score:.3f}, Sources={sources_count}")
                
                if score > best_score:
                    best_score = score
                    best_result = result
                    best_query_idx = i
            else:
                self.logger.info(f"  Alternative {i+1}: FAILED")
        
        if best_result:
            self.logger.info(f"\nBEST ALTERNATIVE FOUND:")
            self.logger.info(f"  Query: '{queries[best_query_idx]}'")
            self.logger.info(f"  Score: {best_score:.3f}")
            self.logger.info(f"  Sources: {len(best_result.get('sources', []))}")
            # Add the query that produced the best result for tracking
            best_result['query'] = queries[best_query_idx]
            return best_result
        else:
            self.logger.info(f"\nNo successful alternative queries")
            return None
    
    def _merge_rag_results(
        self, 
        initial_result: Dict[str, Any], 
        alternative_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge RAG results (matching legacy logic)"""
        initial_sources = initial_result.get('sources', [])
        alternative_sources = alternative_result.get('sources', [])
        
        # Simple deduplication by content similarity (like legacy)
        merged_sources = initial_sources.copy()
        
        for new_source in alternative_sources:
            new_content = new_source.get('content', '')
            is_duplicate = False
            
            for existing_source in merged_sources:
                existing_content = existing_source.get('content', '')
                # Simple overlap check (like legacy)
                if len(set(new_content.split()) & set(existing_content.split())) > len(new_content.split()) * 0.7:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                merged_sources.append(new_source)
        
        # Return merged result
        return {
            "success": True,
            "answer": alternative_result.get('answer', initial_result.get('answer')),
            "sources": merged_sources
        }
    
    def _analyze_rag_quality_issues(self, rag_result: Dict[str, Any]) -> str:
        """Analyze what's wrong with RAG retrieval results"""
        issues = []
        sources = rag_result.get('sources', [])
        
        if len(sources) < self.min_results_count:
            issues.append(f"Too few results ({len(sources)} < {self.min_results_count})")
        
        if sources:
            # Calculate average score
            scores = []
            for source in sources[:5]:
                score = source.get('score', 0)
                if score and score != 'N/A':
                    try:
                        scores.append(float(score))
                    except (ValueError, TypeError):
                        continue
            
            if scores:
                avg_score = sum(scores) / len(scores)
                if avg_score < 0.5:
                    issues.append(f"Low average relevance score ({avg_score:.2f})")
            
            # Check content diversity
            contents = [s.get('content', '')[:100] for s in sources[:5]]
            if len(set(contents)) < 3:
                issues.append("Low content diversity - results too similar")
        
        return "; ".join(issues) if issues else "General low relevance"
    

