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
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
    
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
    
    async def generate_stream(self, prompt: str, temperature: float = None):
        """
        Generate streaming response from prompt using Gemini via LangChain.
        
        Uses LangChain's astream method for async streaming.
        
        Args:
            prompt: Input prompt text
            temperature: Override temperature setting (creates temporary client if different)
        """
        # If temperature override is provided and different from current, create temporary client
        if temperature is not None and temperature != self.temperature:
            from langchain_google_genai import ChatGoogleGenerativeAI
            temp_llm = ChatGoogleGenerativeAI(
                model=self.model,
                google_api_key=self.api_key,
                temperature=temperature
            )
            async for chunk in temp_llm.astream(prompt):
                if chunk.content:
                    yield chunk.content
        else:
            # Use existing LLM instance with current temperature
            async for chunk in self.llm.astream(prompt):
                if chunk.content:
                    yield chunk.content
    
    def get_llm_client(self):
        """Get the underlying LangChain LLM client."""
        return self.llm 
