import os
from cerebras.cloud.sdk import Cerebras
from langchain_core.language_models import LLM
from typing import List, Optional

# Class to wrap Cerebras LLM functionality in a LangChain-compatible format
class LangChainCerebras(LLM):
    """Cerebras LLM client for LangChain integration."""

    def __init__(self, api_key: str, model_name: str, temperature: float, top_p: float):
        """
        Initialize the LangChainCerebras client.

        Args:
            api_key (str): API key for authenticating with Cerebras cloud.
            model_name (str): Name of the Cerebras model to use.
            temperature (float): Sampling temperature for response generation.
            top_p (float): Nucleus sampling probability.
        """
        # Required to initialize LangChain's internal state
        super().__init__()
        # Store model configuration and initialize Cerebras API client
        self._model_name = model_name
        self._temperature = temperature
        self._top_p = top_p
        # Initialize the Cerebras client with the provided API key
        self._client = Cerebras(api_key=api_key)

    # Retrieve response from Cerebras API 
    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        """
        Generate a response from the Cerebras LLM given a prompt.

        Args:
            prompt (str): The input prompt to send to the model.

        Returns:
            str: The generated response from the model.
        """
        # Send the prompt to the Cerebras chat completion endpoint
        response = self._client.chat.completions.create(
            # Model's default reasoning behaviour is currently disabled, can remove by removing the "/no_think"
            messages=[{"role": "user", "content": prompt+ " /no_think"}],
            model=self._model_name, 
            temperature=self._temperature, 
            top_p=self._top_p 
        )

        # Print response (for debugging purposes)
        print(f"Response from Cerebras: {response.choices[0].message.content}")

        # Extract and return the generated content from the response
        return response.choices[0].message.content

    # Internal identifier for the LLM type
    @property
    def _llm_type(self) -> str:
        """
        Return the internal type identifier for this LLM.

        Returns:
            str: The string "cerebras".
        """
        return "cerebras"


class CerebrasClient:
    """Client for interacting with Cerebras AI services."""

    def __init__(self, api_key: str = None, model: str = "qwen-3-235b-a22b", temperature: float = 0.6, top_p: float = 0.95):
        """
        Initialize the CerebrasClient.

        Args:
            api_key (str, optional): API key for Cerebras. If not provided, will use the CEREBRAS_API_KEY environment variable.
            model (str, optional): Model name to use. Defaults to "qwen-3-235b-a22b".
            temperature (float, optional): Sampling temperature. Defaults to 0.6.
            top_p (float, optional): Nucleus sampling probability. Defaults to 0.95.

        Raises:
            ValueError: If no API key is provided or found in the environment.
        """
        # Use provided API key or fall back to environment variable
        api_key = api_key or os.getenv("CEREBRAS_API_KEY")
        if not api_key:
            raise ValueError("CEREBRAS_API_KEY must be provided.")

        # Initialize the LangChain Cerebras client with the provided API key, model, and parameters
        self.llm = LangChainCerebras(
            api_key=api_key,
            model_name=model,
            temperature=temperature,
            top_p=top_p
        )
    
    def get_llm_client(self):
        """
        Get the underlying LangChainCerebras LLM client.

        Returns:
            LangChainCerebras: The wrapped Cerebras LLM client.
        """
        return self.llm