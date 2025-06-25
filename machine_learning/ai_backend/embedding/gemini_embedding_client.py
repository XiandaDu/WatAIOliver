from typing import List

try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover - if package not installed
    genai = None


class GeminiEmbeddingClient:
    def __init__(self, api_key: str, model: str = "models/embedding-001", transport: str = "rest"):
        self.api_key = api_key
        self.model = model
        if genai is not None:
            genai.configure(api_key=api_key, transport=transport)

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if genai is None:
            raise RuntimeError("google-generativeai not installed")
        results: List[List[float]] = []
        for text in texts:
            resp = await genai.embed_content_async(self.model, text, task_type="RETRIEVAL_DOCUMENT")
            results.append(resp["embedding"])
        return results

    async def embed_query(self, text: str) -> List[float]:
        if genai is None:
            raise RuntimeError("google-generativeai not installed")
        resp = await genai.embed_content_async(self.model, text, task_type="RETRIEVAL_QUERY")
        return resp["embedding"]
