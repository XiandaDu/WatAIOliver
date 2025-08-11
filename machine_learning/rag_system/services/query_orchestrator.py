from typing import Dict, Any

from langchain.chains import RetrievalQA

from rag_system.services.retrieval_service import RetrievalService
from rag_system.services.llm_service import LLMService


class QueryOrchestrator:
    """Coordinate retrieval and generation for a question."""

    def __init__(self, retrieval_service: RetrievalService, llm_service: LLMService):
        self.retrieval_service = retrieval_service
        self.llm_service = llm_service

    def answer_question(self, course_id: str, question: str) -> Dict[str, Any]:
        docs_with_scores = self.retrieval_service.search_documents(course_id, question)
        if docs_with_scores:
            context = "\n\n".join([doc.page_content for doc, _ in docs_with_scores[:4]])
            prompt = f"""Based on the following context, answer the question:\n\nContext:\n{context}\n\nQuestion: {question}\n\nAnswer:"""
            answer = self.llm_service.generate(prompt)
        else:
            answer = "I couldn't find relevant information to answer your question."
        sources = self.retrieval_service.format_sources(docs_with_scores)
        return {"answer": answer, "sources": sources, "success": True}
