from langchain_google_genai import ChatGoogleGenerativeAI


class GeminiClient:
    """Google Gemini LLM client."""
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash", temperature: float = 0.1):
        self.llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=temperature
        )
    
    def generate(self, prompt: str) -> str:
        """Generate response from prompt."""
        response = self.llm.invoke(prompt)
        return response.content
    
    def get_llm_client(self):
        """Get the underlying LangChain LLM client."""
        return self.llm 