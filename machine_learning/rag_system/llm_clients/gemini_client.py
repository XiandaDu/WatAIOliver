from langchain_google_genai import ChatGoogleGenerativeAI


class GeminiClient:
    """Google Gemini LLM client."""
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash", temperature: float = 0.1):
        """
        Initialize GeminiClient with API key, model name, and temperature.
        
        Args:
            api_key: Google API key for authentication
            model: Gemini model name (default set to gemini-1.5-flash)
            temperature: Sampling temperature for generation (default set to 0.1)
        """
        self.llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=temperature
        )
    
    def generate(self, prompt: str) -> str:
        """
        Generate response from prompt using Gemini LLM.
        
        Args:
            prompt: Input prompt string
        
        Returns:
            Generated response content as string
        """
        response = self.llm.invoke(prompt)
        return response.content
    
    def get_llm_client(self):
        """Get the underlying LangChain LLM client."""
        return self.llm 
