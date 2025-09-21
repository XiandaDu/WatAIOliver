"""
Retrieve Agent - LangChain Implementation

Enhanced retrieval with speculative query reframing using proper LangChain chaining.
Implements a true chain workflow where outputs flow seamlessly between stages.
"""

import asyncio
import time
import json
from typing import Dict, Any, List, Optional
from langchain.schema import Document, BaseRetriever
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain, SequentialChain, TransformChain
from langchain.chains.base import Chain
from langchain.callbacks.manager import CallbackManagerForChainRun
from langchain.tools import Tool
from langchain.agents import AgentExecutor, create_openai_tools_agent
from pydantic import BaseModel, Field

from ai_agents.state import WorkflowState, RetrievalResult, log_agent_execution
from ai_agents.utils import (
    create_langchain_llm, 
    perform_rag_retrieval, 
    debug_course_chunks,
    format_rag_results_for_agents
)

# Import simple logger for backup logging
try:
    from ai_agents.simple_logger import simple_log
except:
    # Fallback if import fails
    class SimpleLogFallback:
        def info(self, msg, data=None): pass
        def error(self, msg, data=None): pass
        def debug(self, msg, data=None): pass
    simple_log = SimpleLogFallback()


class RetrievalChainOutput(BaseModel):
    """Output schema for the retrieval chain"""
    results: List[Dict[str, Any]] = Field(description="Retrieved results")
    quality_score: float = Field(description="Quality assessment score")
    strategy: str = Field(description="Retrieval strategy used")
    speculative_queries: List[str] = Field(default_factory=list, description="Alternative queries generated")
    
    
class SpeculativeRetrievalChain(Chain):
    """
    Custom chain that implements the full retrieval workflow:
    1. Initial retrieval -> 2. Quality assessment -> 3. Conditional reframing -> 4. Merge & rerank
    
    This is a true chain where outputs flow between stages.
    """
    
    # Required chain components
    initial_retrieval_func: Any  # RAG service function
    reframing_chain: LLMChain
    reranking_chain: Optional[LLMChain] = None  # Made optional since we're not using it
    expansion_chain: Optional[SequentialChain] = None  # The sequential expansion chain (built lazily)
    
    # Configuration
    min_quality_threshold: float = 0.7  # Adjusted to match actual embedding scores
    course_id: str = ""
    logger: Any = None
    rag_service: Any = None
    
    @property
    def input_keys(self) -> List[str]:
        return ["query", "course_id"]
    
    @property
    def output_keys(self) -> List[str]:
        return ["results", "quality_score", "strategy", "speculative_queries"]
    
    def _call(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[CallbackManagerForChainRun] = None
    ) -> Dict[str, Any]:
        """Synchronous version - wraps async call"""
        import asyncio
        return asyncio.run(self._acall(inputs, run_manager))
    
    async def _acall(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[CallbackManagerForChainRun] = None
    ) -> Dict[str, Any]:
        """
        Execute the chained retrieval workflow.
        Each stage's output flows into the next stage.
        """
        query = inputs["query"]
        course_id = inputs.get("course_id", self.course_id)
        
        if self.logger:
            self.logger.info("="*80)
            simple_log.info("="*80)
            self.logger.info("SPECULATIVE RETRIEVAL CHAIN - Starting")
            simple_log.info("SPECULATIVE RETRIEVAL CHAIN - Starting")
            self.logger.info(f"Query: {query}")
            simple_log.info(f"Query: {query}")
            self.logger.info("="*80)
            simple_log.info("="*80)
            
            # Also log to simple logger
            simple_log.info("RETRIEVAL CHAIN START", {
                "query": query,
                "course_id": course_id,
                "threshold": self.min_quality_threshold
            })
        
        # Stage 1: Initial Retrieval
        initial_results = await self._stage_initial_retrieval(query, course_id)
        
        # Stage 2: Quality Assessment (receives initial_results as input)
        quality_output = await self._stage_quality_assessment(query, initial_results)
        quality_score = quality_output["score"]
        
        # Simple log quality assessment
        simple_log.info("QUALITY ASSESSMENT", {
            "query": query,
            "score": quality_score,
            "threshold": self.min_quality_threshold,
            "will_expand": quality_score < self.min_quality_threshold,
            "issues": quality_output.get("issues", [])
        })
        
        # Stage 3: Conditional Reframing using SequentialChain
        if quality_score < self.min_quality_threshold:
            if self.logger:
                self.logger.info("\n[TRIGGERING SEQUENTIAL EXPANSION CHAIN]")
                simple_log.info("\n[TRIGGERING SEQUENTIAL EXPANSION CHAIN]")
                self.logger.info(f"Quality score {quality_score:.3f} < threshold {self.min_quality_threshold}")
                simple_log.info(f"Quality score {quality_score:.3f} < threshold {self.min_quality_threshold}")
                simple_log.info("TRIGGERING EXPANSION", {
                    "quality_score": quality_score,
                    "threshold": self.min_quality_threshold
                })
            
            # Build the expansion chain if not already built
            if self.expansion_chain is None:
                self.expansion_chain = self._build_expansion_sequential_chain()
            
            # Run the 3-stage SequentialChain
            chain_inputs = {
                "query": query,
                "quality_score": quality_output["score"],
                "quality_issues": "; ".join(quality_output["issues"]),
                "course_id": course_id,
                "initial_results": initial_results
            }
            
            if self.logger:
                self.logger.info("="*80)
                simple_log.info("="*80)
                self.logger.info("Executing SequentialChain: Reframing → Alternative Retrieval → Merge & Rerank")
                simple_log.info("Executing SequentialChain: Reframing → Alternative Retrieval → Merge & Rerank")
                self.logger.info("="*80)
                simple_log.info("="*80)
                self.logger.info("[DEBUG] Chain inputs:")
                simple_log.info("[DEBUG] Chain inputs:")
                self.logger.info(f"  - Query: {query}")
                simple_log.info(f"  - Query: {query}")
                self.logger.info(f"  - Quality Score: {quality_output['score']}")
                simple_log.info(f"  - Quality Score: {quality_output['score']}")
                self.logger.info(f"  - Quality Issues: {'; '.join(quality_output['issues'])}")
                simple_log.info(f"  - Quality Issues: {'; '.join(quality_output['issues'])}")
                self.logger.info(f"  - Course ID: {course_id}")
                simple_log.info(f"  - Course ID: {course_id}")
            
            # Execute the chain synchronously using invoke (not deprecated __call__)
            simple_log.info("EXPANSION CHAIN START", {
                "query": query,
                "quality_score": quality_output["score"],
                "issues": quality_output["issues"]
            })
            
            chain_result = self.expansion_chain.invoke(chain_inputs)
            
            simple_log.info("EXPANSION CHAIN COMPLETE", {
                "final_score": chain_result.get("final_score", 0),
                "strategy": f"refined_with_{len(chain_result.get('alternative_queries', []))}_alternatives"
            })
            
            # Extract alternative queries from the results
            speculative_queries = chain_result.get("alternative_queries", [])
            
            return {
                "results": chain_result["final_results"],
                "quality_score": chain_result["final_score"],
                "strategy": f"refined_with_{len(speculative_queries)}_alternatives",
                "speculative_queries": speculative_queries
            }
        else:
            # Quality good enough - skip reframing
            return {
                "results": self._format_results(initial_results),
                "quality_score": quality_score,
                "strategy": "initial_sufficient",
                "speculative_queries": []
            }
    
    async def _stage_initial_retrieval(self, query: str, course_id: str) -> Dict[str, Any]:
        """Stage 1: Initial RAG retrieval"""
        if self.logger:
            self.logger.info("\n[CHAIN STAGE 1] Initial Retrieval")
            simple_log.info("\n[CHAIN STAGE 1] Initial Retrieval")
            self.logger.info(f"Input: query='{query}', course_id={course_id}")
            simple_log.info(f"Input: query='{query}', course_id={course_id}")
        
        result = await perform_rag_retrieval(
            self.rag_service, query, course_id, self.logger
        )
        
        if self.logger:
            sources_count = len(result.get('sources', [])) if result else 0
            self.logger.info(f"Output: {sources_count} sources retrieved")
            simple_log.info(f"Output: {sources_count} sources retrieved")
            simple_log.info("INITIAL RETRIEVAL DONE", {
                "sources_count": sources_count,
                "has_results": bool(result)
            })
    
        return result
    
    async def _stage_quality_assessment(
        self, query: str, retrieval_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Stage 2: Assess quality of retrieval results using score-based approach"""
        if self.logger:
            self.logger.info("\n[CHAIN STAGE 2] Quality Assessment")
            simple_log.info("\n[CHAIN STAGE 2] Quality Assessment")
            self.logger.info(f"Input: {len(retrieval_results.get('sources', []))} sources")
            simple_log.info(f"Input: {len(retrieval_results.get('sources', []))} sources")
        
        sources = retrieval_results.get('sources', [])
        
        # Simple score-based quality assessment
        if not sources:
            score = 0.0
            issues = ["No sources retrieved"]
        else:
            # Average the similarity scores
            scores = [s.get('score', 0.0) for s in sources]
            score = sum(scores) / len(scores)
            
            issues = []
            if len(sources) < 3:
                issues.append(f"Too few results ({len(sources)})")
                score *= 0.8  # Penalty for insufficient results
            
            if score < 0.3:
                issues.append("Very low similarity scores")
            elif score < 0.5:
                issues.append("Low similarity scores")
        
        output = {
            "score": score,
            "issues": issues,
            "raw_response": f"Score-based assessment: average similarity = {score:.3f}"
        }
        
        if self.logger:
            self.logger.info(f"Quality assessment final result:")
            simple_log.info(f"Quality assessment final result:")
            self.logger.info(f"  - Average similarity score: {score:.3f} (threshold: {self.min_quality_threshold})")
            simple_log.info(f"  - Average similarity score: {score:.3f} (threshold: {self.min_quality_threshold})")
            self.logger.info(f"  - Will trigger query expansion: {score < self.min_quality_threshold}")
            simple_log.info(f"  - Will trigger query expansion: {score < self.min_quality_threshold}")
            self.logger.info(f"  - Source scores: {[s.get('score', 0.0) for s in sources]}")
            simple_log.info(f"  - Source scores: {[s.get('score', 0.0) for s in sources]}")
            self.logger.info(f"  - Issues: {issues}")
            simple_log.info(f"  - Issues: {issues}")
        
        return output
    
    def _build_expansion_sequential_chain(self):
        """Build a SequentialChain for the 3-stage expansion process"""
        
        # Stage 1: Query Reframing LLMChain (already defined in init)
        # Set the output key to match what the parser expects
        self.reframing_chain.output_key = "reframing_output"
        
        # We'll create a wrapper to parse the output
        reframing_parser = TransformChain(
            input_variables=["reframing_output"],
            output_variables=["alternative_queries"],
            transform=self._parse_reframing_output
        )
        
        # Stage 2: Alternative Retrieval TransformChain
        retrieval_chain = TransformChain(
            input_variables=["alternative_queries", "course_id"],
            output_variables=["alternative_results"],
            transform=self._perform_alternative_retrievals
        )
        
        # Stage 3: Merge & Rerank TransformChain
        merge_chain = TransformChain(
            input_variables=["query", "initial_results", "alternative_results"],
            output_variables=["final_results", "final_score"],
            transform=self._merge_and_rerank_sync
        )
        
        # Combine into SequentialChain
        # First chain the reframing LLM with its parser
        reframing_sequence = SequentialChain(
            chains=[self.reframing_chain, reframing_parser],
            input_variables=["query", "quality_score", "quality_issues"],
            output_variables=["alternative_queries"],
            verbose=True  # Always verbose to debug the issue
        )
        
        # Then chain all three stages together
        expansion_chain = SequentialChain(
            chains=[reframing_sequence, retrieval_chain, merge_chain],
            input_variables=["query", "quality_score", "quality_issues", "course_id", "initial_results"],
            output_variables=["final_results", "final_score", "alternative_queries"],
            verbose=True  # Always verbose to debug the issue
        )
        
        return expansion_chain
    
    def _parse_reframing_output(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Parse the LLM reframing output to extract queries"""
        reframing_output = inputs.get("reframing_output", inputs.get("text", ""))
        
        if self.logger:
            self.logger.info("="*80)
            simple_log.info("="*80)
            self.logger.info("[CHAIN] REFRAMING PARSER - DEBUG")
            simple_log.info("[CHAIN] REFRAMING PARSER - DEBUG")
            self.logger.info("="*80)
            simple_log.info("="*80)
            self.logger.info(f"[DEBUG] Raw inputs to parser: {inputs.keys()}")
            simple_log.info(f"[DEBUG] Raw inputs to parser: {inputs.keys()}")
            self.logger.info(f"[DEBUG] Reframing output to parse:\n{reframing_output}")
            simple_log.info(f"[DEBUG] Reframing output to parse:\n{reframing_output}")
            self.logger.info("="*80)
            simple_log.info("="*80)
        
        # Parse queries from the LLM response
        queries = []
        for line in str(reframing_output).split("\n"):
            if line.strip().startswith("QUERY:"):
                q = line.replace("QUERY:", "").strip()
                if not (q.startswith("{") and q.endswith("}")):
                    queries.append(q)
        
        # Fallback parsing
        if not queries:
            lines = [l.strip() for l in str(reframing_output).split("\n") if l.strip()]
            queries = [l for l in lines if len(l) > 10 and not l.startswith(("#", "1.", "2.", "3."))]  # All queries
        
        if self.logger:
            self.logger.info(f"[CHAIN] Extracted {len(queries)} alternative queries")
            simple_log.info(f"[CHAIN] Extracted {len(queries)} alternative queries")
            for i, q in enumerate(queries[:3], 1):
                self.logger.info(f"  Query {i}: {q}")
                simple_log.info(f"  Query {i}: {q}")
            if len(queries) == 0:
                self.logger.warning("[WARNING] No queries extracted from reframing output!")
        
        return {"alternative_queries": queries[:3]}
    
    def _perform_alternative_retrievals(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Perform RAG retrievals for alternative queries (sync wrapper)"""
        queries = inputs["alternative_queries"]
        course_id = inputs["course_id"]
        
        if self.logger:
            self.logger.info("="*80)
            simple_log.info("="*80)
            self.logger.info("[CHAIN] ALTERNATIVE RETRIEVAL - DEBUG")
            simple_log.info("[CHAIN] ALTERNATIVE RETRIEVAL - DEBUG")
            self.logger.info("="*80)
            simple_log.info("="*80)
            self.logger.info(f"[DEBUG] Alternative queries to retrieve:")
            simple_log.info(f"[DEBUG] Alternative queries to retrieve:")
            for i, q in enumerate(queries, 1):
                self.logger.info(f"  {i}. {q}")
                simple_log.info(f"  {i}. {q}")
            self.logger.info(f"[DEBUG] Course ID: {course_id}")
            simple_log.info(f"[DEBUG] Course ID: {course_id}")
            self.logger.info("="*80)
            simple_log.info("="*80)
        
        # Use a thread executor to run async code from sync context
        import asyncio
        import concurrent.futures
        from threading import Thread
        
        results = []
        
        def run_async_retrieval(query):
            """Helper to run async retrieval in a new thread with its own event loop"""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    perform_rag_retrieval(self.rag_service, query, course_id, self.logger)
                )
            finally:
                loop.close()
        
        # Use ThreadPoolExecutor to run async retrievals
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            for q in queries:
                if self.logger:
                    self.logger.info(f"[DEBUG] Submitting retrieval for: {q}")
                    simple_log.info(f"[DEBUG] Submitting retrieval for: {q}")
                future = executor.submit(run_async_retrieval, q)
                futures.append((future, q))
            
            # Collect results
            for future, q in futures:
                try:
                    result = future.result(timeout=30)  # 30 second timeout
                    results.append(result)
                    if self.logger:
                        sources_count = len(result.get('sources', [])) if result else 0
                        self.logger.info(f"[DEBUG] Retrieved {sources_count} sources for: {q}")
                        simple_log.info(f"[DEBUG] Retrieved {sources_count} sources for: {q}")
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"[ERROR] Failed to retrieve for query '{q}': {e}")
                    results.append({"success": False, "error": str(e)})
        
        # Filter successful results
        valid_results = []
        for r, q in zip(results, queries):
            if isinstance(r, dict) and r.get('success'):
                r['query_used'] = q
                valid_results.append(r)
        
        if self.logger:
            self.logger.info(f"[CHAIN] Retrieved {len(valid_results)} successful results")
            simple_log.info(f"[CHAIN] Retrieved {len(valid_results)} successful results")
        
        return {"alternative_results": valid_results}
    
    def _merge_and_rerank_sync(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Merge and rerank results (sync version)"""
        query = inputs["query"]
        initial_results = inputs["initial_results"]
        alternative_results = inputs["alternative_results"]
        
        if self.logger:
            self.logger.info(f"[CHAIN] Merging initial + {len(alternative_results)} alternative results")
            simple_log.info(f"[CHAIN] Merging initial + {len(alternative_results)} alternative results")
        
        # Collect all unique sources
        all_sources = initial_results.get('sources', []).copy()
        seen_content = {s.get('content', '') for s in all_sources}
        
        for alt_result in alternative_results:
            for source in alt_result.get('sources', []):
                content_snippet = source.get('content', '')
                if content_snippet not in seen_content:
                    all_sources.append(source)
                    seen_content.add(content_snippet)
        
        # Use original vector retrieval scores (no LLM reranking)
        if self.logger:
            self.logger.info(f"[CHAIN] Merging {len(all_sources)} sources using vector scores...")
            simple_log.info(f"[CHAIN] Merging {len(all_sources)} sources using vector scores...")
        
        # Sort by original retrieval score
        ranked_sources = sorted(all_sources, key=lambda x: x.get('score', 0), reverse=True)
        
        # Take top 10 and calculate final score
        top_sources = ranked_sources[:10]
        scores = [s.get('score', 0.5) for s in top_sources]
        final_score = sum(scores) / len(scores) if scores else 0.0
        
        final_results = self._format_results({"sources": top_sources})
        
        if self.logger:
            self.logger.info(f"[CHAIN] Final: {len(top_sources)} results, score={final_score:.3f}")
            simple_log.info(f"[CHAIN] Final: {len(top_sources)} results, score={final_score:.3f}")
        
        return {
            "final_results": final_results,
            "final_score": final_score
        }
    
    async def _rerank_sources(self, query: str, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rerank sources using the reranking chain"""
        # Score each source
        scored_sources = []
        for source in sources:
            try:
                response = await self.reranking_chain.arun(
                    query=query,
                    document=source.get('content', '')
                )
                
                score = 0.5  # default
                if "SCORE:" in response:
                    score_str = response.split("SCORE:")[1].strip()
                    try:
                        score = float(score_str)
                    except:
                        pass
                
                source['reranked_score'] = score
                scored_sources.append(source)
            except:
                source['reranked_score'] = source.get('score', 0.5)
                scored_sources.append(source)
        
        # Sort by reranked score
        return sorted(scored_sources, key=lambda x: x.get('reranked_score', 0), reverse=True)
    
    async def _calculate_final_quality(self, query: str, top_sources: List[Dict[str, Any]]) -> float:
        """Calculate final quality score after merging"""
        if not top_sources:
            return 0.0
        
        # Average of reranked scores
        scores = [s.get('reranked_score', s.get('score', 0.5)) for s in top_sources]
        return sum(scores) / len(scores) if scores else 0.0
    
    def _format_results(self, rag_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format RAG results for output"""
        results = []
        for source in rag_result.get('sources', []):
            metadata = source.get('metadata', {})
            # Construct source from document_id and chunk_index
            doc_id = metadata.get('document_id', 'unknown')
            chunk_idx = metadata.get('chunk_index', '')
            
            # Format source as "doc_id:chunk_index" or fall back to metadata source
            if doc_id != 'unknown' and chunk_idx != '':
                source_str = f"{doc_id}:chunk_{chunk_idx}"
            else:
                source_str = metadata.get('source', 'unknown')
            
            results.append({
                "content": source.get('content', ''),
                "score": source.get('reranked_score', source.get('score', 0.0)),
                "source": source_str,
                "metadata": metadata
            })
        return results


class RetrieveAgent:
    """
    Speculative Retriever using a proper LangChain composite chain.
    
    Now uses SpeculativeRetrievalChain which properly chains together:
    1. Initial retrieval -> 2. Quality assessment -> 3. Conditional reframing -> 4. Merge & rerank
    
    Each stage's output flows into the next stage as true chaining.
    """
    
    def __init__(self, context):
        self.context = context
        self.logger = context.logger.getChild("retrieve")
        self.rag_service = context.rag_service
        self.llm_client = context.llm_client
        
        # Create LangChain-compatible LLM
        self.llm = create_langchain_llm(self.llm_client)
        
        # Quality thresholds
        self.min_quality_threshold = 0.7  # Adjusted to match actual embedding scores (typically 0.49-0.52)
        self.rerank_threshold = 0.6  # Add reranking step for scores above this
        self.min_results_count = 3
        
        # Initialize the composite chain
        self._setup_composite_chain()
        
    def _setup_composite_chain(self):
        """Setup the composite retrieval chain that chains all operations together"""
        
        # We use score-based quality assessment, no LLM needed for that
        
        # Query reframing chain (only runs if quality is low)
        reframing_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at reformulating educational queries for better retrieval from course materials.
When initial retrieval quality is poor, generate alternative queries that might yield better results.
Keep the queries closely related to the original intent and topic."""),
            ("human", """Original Query: {query}

Initial Results Quality Score: {quality_score}
Quality Issues: {quality_issues}

The original query didn't match well with the course materials. Generate 3 alternative query formulations that:
1. Use different terminology or perspectives while staying on the same topic
2. Are more specific or break down the concept
3. Focus on different aspects of the SAME topic as the original query

IMPORTANT: 
- Keep all alternative queries closely related to the original query's topic
- Generate CONCRETE queries without placeholders or brackets
- If the query mentions "yesterday" or "recent", rephrase to be about "recent topics" or "latest materials"

Format each query on a new line starting with "QUERY:".

Example for "What was covered in yesterday's lesson?":
QUERY: recent topics covered in class
QUERY: latest lecture materials and concepts
QUERY: most recent course content and examples""")
        ])
        
        self.reframing_chain = LLMChain(
            llm=self.llm,
            prompt=reframing_prompt,
            verbose=True  # Enable verbose to see what's being sent to LLM
        )
        
        # Create the composite chain that chains everything together
        self.retrieval_chain = SpeculativeRetrievalChain(
            reframing_chain=self.reframing_chain,
            initial_retrieval_func=perform_rag_retrieval,
            min_quality_threshold=self.min_quality_threshold,
            logger=self.logger,
            rag_service=self.rag_service
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
            # Check if source needs to be constructed from metadata
            source_str = result.get('source', 'unknown')
            if source_str == 'unknown' and 'metadata' in result:
                metadata = result.get('metadata', {})
                doc_id = metadata.get('document_id', 'unknown')
                chunk_idx = metadata.get('chunk_index', '')
                if doc_id != 'unknown' and chunk_idx != '':
                    source_str = f"{doc_id}:chunk_{chunk_idx}"
            
            formatted_results.append({
                "text": result.get('content', ''),
                "score": float(result.get('score', 0.0)),
                "source": source_str,
                "retrieval_path": strategy,
                "metadata": result.get('metadata', {})  # Include metadata in output
            })
        
        return formatted_results
    
    async def __call__(self, state: WorkflowState) -> WorkflowState:
        """Execute retrieval using the composite chain"""
        start_time = time.time()
        
        try:
            self.logger.info("="*250)
            simple_log.info("="*250)
            self.logger.info("RETRIEVE AGENT - CHAINED RETRIEVAL WORKFLOW")
            simple_log.info("RETRIEVE AGENT - CHAINED RETRIEVAL WORKFLOW")
            self.logger.info("="*250)
            simple_log.info("="*250)
            
            query = state["query"]
            course_id = state["course_id"]
            
            self.logger.info(f"Query: '{query}'")
            simple_log.info(f"Query: '{query}'")
            self.logger.info(f"Course ID: {course_id}")
            simple_log.info(f"Course ID: {course_id}")
            
            # Debug chunks first (for logging purposes)
            await debug_course_chunks(self.rag_service, course_id, query, self.logger)
            
            # Execute the complete retrieval chain
            # The chain internally handles:
            # 1. Initial retrieval
            # 2. Quality assessment  
            # 3. Conditional reframing
            # 4. Alternative retrieval
            # 5. Merging and reranking
            
            self.logger.info("\nExecuting composite retrieval chain...")
            simple_log.info("\nExecuting composite retrieval chain...")
            chain_output = await self.retrieval_chain._acall({
                "query": query,
                "course_id": course_id
            })
            
            # Extract results from chain output
            results = chain_output.get("results", [])
            quality_score = chain_output.get("quality_score", 0.0)
            strategy = chain_output.get("strategy", "unknown")
            speculative_queries = chain_output.get("speculative_queries", [])
            
            # Log what we got
            self.logger.info(f"Chain output type: {type(chain_output)}")
            simple_log.info(f"Chain output type: {type(chain_output)}")
            self.logger.info(f"Results type: {type(results)}, length: {len(results) if isinstance(results, list) else 'N/A'}")
            simple_log.info(f"Results type: {type(results)}, length: {len(results) if isinstance(results, list) else 'N/A'}")
            
            # Convert to RetrievalResult format for state
            retrieval_results = []
            for r in results:
                # Ensure r is a dictionary
                if not isinstance(r, dict):
                    self.logger.warning(f"Unexpected result type: {type(r)}, value: {r}")
                    continue
                # Construct source from metadata if needed
                metadata = r.get("metadata", {})
                source_str = r.get("source", "unknown")
                if source_str == "unknown" and metadata:
                    doc_id = metadata.get('document_id', 'unknown')
                    chunk_idx = metadata.get('chunk_index', '')
                    if doc_id != 'unknown' and chunk_idx != '':
                        source_str = f"{doc_id}:chunk_{chunk_idx}"
                
                retrieval_results.append(RetrievalResult(
                    content=r.get("content", ""),
                    score=r.get("score", 0.0),
                    source=source_str,
                    metadata=metadata
                ))
            
            # Format output as JSON
            json_output = self._format_retrieval_output(
                retrieval_results[:10],  # Top 10 results
                strategy=strategy,
                no_results_suggestion=f"Try rephrasing '{query}' to be more specific about the course material."
            )
            
            # Log the JSON output
            self.logger.info("="*250)
            simple_log.info("="*250)
            self.logger.info("CHAIN OUTPUT (JSON)")
            simple_log.info("CHAIN OUTPUT (JSON)")
            self.logger.info("="*250)
            simple_log.info("="*250)
            self.logger.info(json.dumps(json_output, indent=2))
            simple_log.info(json.dumps(json_output, indent=2))
            self.logger.info("="*250)
            simple_log.info("="*250)
            
            # Update state with chain results
            state["retrieval_results"] = retrieval_results[:10]
            state["retrieval_quality_score"] = quality_score
            state["retrieval_strategy"] = strategy
            state["speculative_queries"] = speculative_queries
            state["workflow_status"] = "retrieving"
            state["formatted_retrieval_output"] = json_output
            
            # Log execution
            processing_time = time.time() - start_time
            log_agent_execution(
                state=state,
                agent_name="Retrieve",
                input_summary=f"Query: {query}",
                output_summary=f"Chain retrieved {len(retrieval_results)} chunks, quality: {quality_score:.3f}, strategy: {strategy}",
                processing_time=processing_time,
                success=True
            )
            
            self.logger.info(f"Chained retrieval completed in {processing_time:.2f}s")
            simple_log.info(f"Chained retrieval completed in {processing_time:.2f}s")
            
        except Exception as e:
            self.logger.error(f"Chained retrieval failed: {str(e)}")
            state["error_messages"].append(f"Retrieve agent error: {str(e)}")
            state["workflow_status"] = "failed"
            
            log_agent_execution(
                state=state,
                agent_name="Retrieve",
                input_summary=f"Query: {state['query']}",
                output_summary=f"Error: {str(e)}",
                processing_time=time.time() - start_time,
                success=False
            )
        
        return state
    

    

