from langchain_google_genai import ChatGoogleGenerativeAI


class GeminiClient:
    """Google Gemini LLM client supporting multiple models including Gemini 2.5 Pro."""
    
    def __init__(self, api_key: str, model: str = "gemini-2.5-pro", temperature: float = 0.1):
        # Map frontend model names to actual Gemini model names
        model_mapping = {
            "gemini-2.5-pro": "gemini-2.5-pro",
            "gemini-1.5-flash": "gemini-1.5-flash",
            "gemini-1.5-pro": "gemini-1.5-pro"
        }
        
        # Use the mapped model name, fallback to original if not found
        actual_model = model_mapping.get(model, model)
        
        self.model_name = actual_model
        self.llm = ChatGoogleGenerativeAI(
            model=actual_model,
            google_api_key=api_key,
            temperature=temperature
        )
    
    def generate(self, prompt: str) -> str:
        """Generate response from prompt."""
        response = self.llm.invoke(prompt)
        return str(response.content)
    
    def get_llm_client(self):
        """Get the underlying LangChain LLM client."""
        return self.llm
    
    def get_model_name(self) -> str:
        """Get the current model name."""
        return self.model_name 