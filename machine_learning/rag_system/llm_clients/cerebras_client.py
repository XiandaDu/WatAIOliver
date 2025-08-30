import os
from cerebras.cloud.sdk import Cerebras
from langchain_core.language_models import LLM
from typing import List, Optional


class LangChainCerebras(LLM):
    """Cerebras LLM client for LangChain integration."""

    def __init__(self, api_key: str, model_name: str, temperature: float, top_p: float):
        super().__init__()
        self._model_name = model_name
        self._temperature = temperature
        self._top_p = top_p
        self._client = Cerebras(api_key=api_key)

    def _call(self, prompt: str, stop: Optional[List[str]] = None, *args, **kwargs) -> str:
        # Extract temperature and top_p from kwargs if they exist, otherwise use instance defaults
        temperature = kwargs.pop("temperature", self._temperature)
        top_p = kwargs.pop("top_p", self._top_p)

        response = self._client.chat.completions.create(
            messages=[{"role": "user", "content": prompt + " /no_think"}],
            model=self._model_name,
            temperature=temperature,
            top_p=top_p,
            stop=stop if stop else [],
            **kwargs
        )
        return response.choices[0].message.content

    @property
    def _llm_type(self) -> str:
        return "cerebras"


class CerebrasClient:
    """Client for interacting with Cerebras AI services."""

    def __init__(self, api_key: str | None = None, model: str = "qwen-3-235b-a22b-instruct-2507", temperature: float = 0.6, top_p: float = 0.95):
        api_key = api_key or os.getenv("CEREBRAS_API_KEY")
        if not api_key:
            raise ValueError("CEREBRAS_API_KEY must be provided.")
        self.llm = LangChainCerebras(
            api_key=api_key,
            model_name=model,
            temperature=temperature,
            top_p=top_p,
        )

    def get_llm_client(self):
        return self.llm

    def generate(self, prompt: str, temperature: float = None) -> str:
        """
        Generate response from prompt using Cerebras LLM (non-streaming).
        
        Args:
            prompt: Input prompt text
            temperature: Override temperature setting
        """
        actual_temperature = temperature if temperature is not None else self.llm._temperature
        
        try:
            # Use direct API for consistent behavior
            response = self.llm._client.chat.completions.create(
                messages=[{"role": "user", "content": prompt + " /no_think"}],
                model=self.llm._model_name,
                temperature=actual_temperature,
                top_p=self.llm._top_p,
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            error_str = str(e).lower()
            # Handle rate limits gracefully - return helpful message
            if any(term in error_str for term in ['rate limit', 'quota']):
                return f"Cerebras API quota/rate limit reached: {str(e)}"
            # Handle other server-side errors that should be retried
            elif any(term in error_str for term in ['overloaded', '500', '502', '503', '504']):
                raise ConnectionError(f"Cerebras server error: {str(e)}")
            else:
                raise e

    async def generate_stream(self, prompt: str, temperature: float = None):
        """
        Generate streaming response from prompt using Cerebras LLM.
        
        Args:
            prompt: Input prompt text
            temperature: Override temperature setting
        """
        actual_temperature = temperature if temperature is not None else self.llm._temperature
        
        try:
            response_generator = self.llm._client.chat.completions.create(
                messages=[{"role": "user", "content": prompt + " /no_think"}],
                model=self.llm._model_name,
                temperature=actual_temperature,
                top_p=self.llm._top_p,
                stream=True
            )
            
            import asyncio
            chunk_count = 0
            for chunk in response_generator:
                if chunk.choices and chunk.choices[0].delta.content:
                    chunk_count += 1
                    yield chunk.choices[0].delta.content
                    # Only yield control periodically for maximum speed
                    if chunk_count % 5 == 0:  # Every 5th chunk
                        await asyncio.sleep(0)
        except Exception as e:
            error_str = str(e).lower()
            # Handle rate limits gracefully - yield helpful message
            if any(term in error_str for term in ['rate limit', 'quota']):
                yield f"Cerebras API quota/rate limit reached: {str(e)}"
                return
            # Handle other server-side errors that should be retried
            elif any(term in error_str for term in ['overloaded', '500', '502', '503', '504']):
                raise ConnectionError(f"Cerebras streaming error: {str(e)}")
            else:
                raise e
       
