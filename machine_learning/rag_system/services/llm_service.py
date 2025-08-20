from rag_system.app.config import Settings
from rag_system.llm_clients.gemini_client import GeminiClient
from rag_system.llm_clients.cerebras_client import CerebrasClient
from rag_system.llm_clients.openai_client import OpenAIClient
from rag_system.llm_clients.anthropic_client import AnthropicClient
from machine_learning.constants import ModelConfig


class LLMService:
    """Wrapper around the LLM client used for generation."""

    def __init__(self, settings: Settings):
        self.settings = settings
        if settings.llm_provider == "cerebras":
            self.llm_client = CerebrasClient(
                api_key=settings.cerebras_api_key,
                model="qwen-3-235b-a22b-instruct-2507",
                temperature=0.6,
                top_p=0.95,
            )
        elif settings.llm_provider == "openai":
            self.llm_client = OpenAIClient(
                api_key=settings.openai_api_key,
                model="gpt-4o",
                temperature=0.6,
                top_p=0.95,
            )
        elif settings.llm_provider == "anthropic":
            self.llm_client = AnthropicClient(
                api_key=settings.anthropic_api_key,
                model="claude-3-sonnet-20240229",
                temperature=0.6,
                top_p=0.95,
            )
        else:
            self.llm_client = GeminiClient(
                api_key=settings.google_api_key,
                model="gemini-2.5-flash",  # Changed from Pro to Flash as default
                temperature=ModelConfig.DEFAULT_TEMPERATURE,
            )

    def generate(self, prompt: str) -> str:
        return self.llm_client.generate(prompt)

    def get_llm_client(self):
        return self.llm_client.get_llm_client()

