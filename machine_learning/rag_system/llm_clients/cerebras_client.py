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

    def generate(self, prompt: str) -> str:
        """
        Generate response from prompt using Cerebras LLM.
        """
        # Delegate to the underlying LangChain LLM instance
        return self.llm(prompt)
       

    async def generate_stream(self, prompt: str):
        """Generate streaming response from prompt using Cerebras LLM."""
        response_generator = self.llm._client.chat.completions.create(
            messages=[{"role": "user", "content": prompt + " /no_think"}],
            model=self.llm._model_name,
            temperature=self.llm._temperature,
            top_p=self.llm._top_p,
            stream=True  # Ensure streaming is enabled for this method
        )
        
        for chunk in response_generator:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def generate(self, prompt: str) -> str:
        """
        Generate response from prompt using Cerebras LLM.
        """
        # Ensure non-streaming for agent usage
        response = self.llm._client.chat.completions.create(
            messages=[{"role": "user", "content": prompt + " /no_think"}],
            model=self.llm._model_name,
            temperature=self.llm._temperature,
            top_p=self.llm._top_p,
            stream=False  # Explicitly disable streaming for the non-streaming generate method
        )
        return response.choices[0].message.content
       
