import os
from anthropic import Anthropic


class AnthropicClient:
    """Wrapper for Anthropic Claude models with optional streaming."""

    def __init__(self, api_key: str | None = None, model: str = "claude-3-sonnet-20240229", temperature: float = 0.6, top_p: float = 0.95):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY must be provided")
        self.client = Anthropic(api_key=self.api_key)
        self.model = model
        self.temperature = temperature
        self.top_p = top_p

    def generate(self, prompt: str, stream: bool = False) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            temperature=self.temperature,
            top_p=self.top_p,
            system=None,
            messages=[{"role": "user", "content": prompt}],
            stream=stream,
        )
        if not stream:
            return response.content[0].text if response.content else ""
        content = ""
        for chunk in response:
            if chunk.delta and chunk.delta.text:
                content += chunk.delta.text
        return content

    async def generate_stream(self, prompt: str):
        """
        Generate streaming response from prompt using Anthropic Claude.
        """
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            temperature=self.temperature,
            top_p=self.top_p,
            system=None,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )
        
        # Stream chunks as they arrive from Anthropic API
        for chunk in response:
            if chunk.delta and chunk.delta.text:
                yield chunk.delta.text

    def get_llm_client(self):
        return self.client
