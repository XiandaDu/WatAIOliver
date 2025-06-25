try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover - if package not installed
    genai = None


class GeminiClient:
    def __init__(self, api_key: str, model: str = "gemini-pro", transport: str = "rest"):
        self.api_key = api_key
        self.model_name = model
        if genai is not None:
            genai.configure(api_key=api_key, transport=transport)
            self.model = genai.GenerativeModel(model)

    async def generate(self, question: str, context: str) -> str:
        if genai is None:
            raise RuntimeError("google-generativeai not installed")
        prompt = f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
        response = await self.model.generate_content_async(prompt)
        return response.text
