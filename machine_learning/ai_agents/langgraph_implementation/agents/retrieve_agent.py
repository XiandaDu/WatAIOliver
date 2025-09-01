"""
Retrieve Agent - LangChain Implementation

Enhanced retrieval with speculative query reframing using LangChain tools and chains.
"""

import asyncio
import time
from typing import Dict, Any, List
from langchain.schema import Document
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain.tools import Tool
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.messages import HumanMessage, SystemMessage

from ..state import WorkflowState, RetrievalResult, log_agent_execution


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
        self.llm = context.llm_client
        
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
    
    async def __call__(self, state: WorkflowState) -> WorkflowState:
        """Execute retrieval with speculative reframing"""
        start_time = time.time()
        
        try:
            self.logger.info("="*250)
            self.logger.info("RETRIEVE AGENT - ENHANCED RETRIEVAL")
            self.logger.info("="*250)
            
            query = state["query"]
            course_id = state["course_id"]
            
            # Stage 1: Initial RAG retrieval
            self.logger.info(f"Query: '{query}'")
            self.logger.info(f"Course ID: {course_id}")
            self.logger.info("Performing initial retrieval...")
            
            initial_results = await self._perform_initial_retrieval(query, course_id)
            
            # Stage 2: Quality assessment using LangChain
            quality_score = await self._assess_quality_with_chain(query, initial_results)
            self.logger.info(f"Quality Score: {quality_score:.3f}")
            
            # Stage 3: Speculative reframing if needed
            final_results = initial_results
            retrieval_strategy = "initial"
            speculative_queries = []
            
            if quality_score < self.min_quality_threshold:
                self.logger.info("Quality too low - triggering speculative reframing")
                
                # Generate alternative queries using chain
                reframed_queries = await self._generate_reframed_queries(
                    query, quality_score, initial_results
                )
                speculative_queries = reframed_queries
                
                # Perform parallel retrieval for all queries
                all_results = await self._parallel_retrieval(reframed_queries, course_id)
                
                # Merge and re-rank results
                final_results = await self._merge_and_rerank(
                    query, initial_results + all_results
                )
                retrieval_strategy = "speculative_reframing"
                
                # Recalculate quality
                quality_score = await self._assess_quality_with_chain(query, final_results)
                self.logger.info(f"Enhanced quality: {quality_score:.3f}")
            
            # Update state
            state["retrieval_results"] = final_results[:10]  # Top 10 results
            state["retrieval_quality_score"] = quality_score
            state["retrieval_strategy"] = retrieval_strategy
            state["speculative_queries"] = speculative_queries
            state["workflow_status"] = "retrieving"
            
            # Log execution
            processing_time = time.time() - start_time
            log_agent_execution(
                state=state,
                agent_name="Retrieve",
                input_summary=f"Query: {query[:100]}",
                output_summary=f"Retrieved {len(final_results)} chunks, quality: {quality_score:.3f}",
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
    
    async def _perform_initial_retrieval(self, query: str, course_id: str) -> List[RetrievalResult]:
        """Perform initial RAG query using existing service"""
        try:
            # Call existing RAG service
            if self.rag_service:
                response = await self.rag_service.retrieve(
                    query=query,
                    course_id=course_id,
                    k=self.context.config.retrieval_k
                )
                
                # Convert to our format
                results = []
                for source in response.get("sources", []):
                    results.append(RetrievalResult(
                        content=source.get("content", ""),
                        score=source.get("score", 0.0),
                        source=source.get("source", ""),
                        metadata=source.get("metadata", {})
                    ))
                return results
            else:
                # Fallback mock retrieval for testing
                return self._mock_retrieval(query)
                
        except Exception as e:
            self.logger.error(f"Initial retrieval failed: {str(e)}")
            return []
    
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
        initial_results: List[RetrievalResult]
    ) -> List[str]:
        """Generate reframed queries using LangChain"""
        try:
            # Identify quality issues
            quality_issues = self._analyze_quality_issues(initial_results)
            
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
                    queries.append(line.replace("QUERY:", "").strip())
            
            self.logger.info(f"Generated {len(queries)} reframed queries")
            for i, q in enumerate(queries, 1):
                self.logger.info(f"  {i}. {q}")
            
            return queries[:3]  # Limit to 3 queries
            
        except Exception as e:
            self.logger.error(f"Query reframing failed: {str(e)}")
            return []
    
    async def _parallel_retrieval(
        self, 
        queries: List[str], 
        course_id: str
    ) -> List[RetrievalResult]:
        """Perform parallel retrieval for multiple queries"""
        tasks = [
            self._perform_initial_retrieval(q, course_id)
            for q in queries
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten results
        all_results = []
        for result in results:
            if isinstance(result, list):
                all_results.extend(result)
        
        return all_results
    
    async def _merge_and_rerank(
        self, 
        query: str, 
        all_results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """Merge and re-rank results using LangChain"""
        
        # Remove duplicates based on content similarity
        unique_results = self._deduplicate_results(all_results)
        
        # Re-rank using chain
        reranked = []
        for result in unique_results[:20]:  # Re-rank top 20
            try:
                response = await self.reranking_chain.arun(
                    query=query,
                    document=result["content"][:1000]
                )
                
                # Parse score
                if "SCORE:" in response:
                    score_str = response.split("SCORE:")[1].strip()
                    result["score"] = float(score_str)
                
                reranked.append(result)
                
            except Exception as e:
                self.logger.error(f"Re-ranking failed for document: {str(e)}")
                reranked.append(result)
        
        # Sort by new scores
        reranked.sort(key=lambda x: x["score"], reverse=True)
        
        return reranked
    
    def _analyze_quality_issues(self, results: List[RetrievalResult]) -> str:
        """Analyze what's wrong with retrieval results"""
        issues = []
        
        if len(results) < self.min_results_count:
            issues.append(f"Too few results ({len(results)} < {self.min_results_count})")
        
        if results:
            avg_score = sum(r["score"] for r in results[:5]) / min(len(results), 5)
            if avg_score < 0.5:
                issues.append(f"Low average relevance score ({avg_score:.2f})")
            
            # Check content diversity
            contents = [r["content"][:100] for r in results[:5]]
            if len(set(contents)) < 3:
                issues.append("Low content diversity - results too similar")
        
        return "; ".join(issues) if issues else "General low relevance"
    
    def _deduplicate_results(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """Remove duplicate results based on content similarity"""
        seen_contents = set()
        unique = []
        
        for result in results:
            # Simple deduplication based on first 200 chars
            content_key = result["content"][:200]
            if content_key not in seen_contents:
                seen_contents.add(content_key)
                unique.append(result)
        
        return unique
    
    def _mock_retrieval(self, query: str) -> List[RetrievalResult]:
        """Mock retrieval for testing without RAG service"""
        return [
            RetrievalResult(
                content=f"Mock content for '{query}' - Result {i+1}",
                score=0.8 - (i * 0.1),
                source=f"mock_source_{i+1}.pdf",
                metadata={"page": i+1}
            )
            for i in range(5)
        ]
