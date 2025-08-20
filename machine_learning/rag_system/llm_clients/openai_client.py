import os
from openai import OpenAI


class OpenAIClient:
    """Wrapper for OpenAI chat models with optional streaming."""

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o", temperature: float = 0.6, top_p: float = 0.95):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY must be provided")
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        self.temperature = temperature
        self.top_p = top_p

    def generate(self, prompt: str, stream: bool = False) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            top_p=self.top_p,
            stream=stream,
        )
        if not stream:
            return response.choices[0].message.content
        content = ""
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                content += chunk.choices[0].delta.content
        return content

    async def generate_stream(self, prompt: str):
        """
        Generate streaming response from prompt using OpenAI.
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            top_p=self.top_p,
            stream=True
        )
        
        # Stream chunks as they arrive from OpenAI API
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def get_llm_client(self):
        return self.client
