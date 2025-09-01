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
        try:
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
        except Exception as e:
            error_str = str(e).lower()
            # Handle rate limits gracefully - return helpful message
            if any(term in error_str for term in ['rate limit', 'quota']):
                return f"Anthropic API quota/rate limit reached: {str(e)}"
            # Handle other server-side errors that should be retried
            elif any(term in error_str for term in ['overloaded', '500', '502', '503', '504']):
                raise ConnectionError(f"Anthropic server error: {str(e)}")
            else:
                raise e

    async def generate_stream(self, prompt: str, temperature: float = None):
        """
        Generate streaming response from prompt using Anthropic Claude.
        
        Args:
            prompt: Input prompt text
            temperature: Override temperature setting
        """
        actual_temperature = temperature if temperature is not None else self.temperature
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                temperature=actual_temperature,
                top_p=self.top_p,
                system=None,
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )
            
            # Stream chunks as they arrive from Anthropic API
            import asyncio
            chunk_count = 0
            for chunk in response:
                if chunk.delta and chunk.delta.text:
                    chunk_count += 1
                    yield chunk.delta.text
                    # Only yield control periodically for maximum speed
                    if chunk_count % 5 == 0:  # Every 5th chunk
                        await asyncio.sleep(0)
        except Exception as e:
            error_str = str(e).lower()
            # Handle rate limits gracefully - yield helpful message
            if any(term in error_str for term in ['rate limit', 'quota']):
                yield f"Anthropic API quota/rate limit reached: {str(e)}"
                return
            # Handle other server-side errors that should be retried
            elif any(term in error_str for term in ['overloaded', '500', '502', '503', '504']):
                raise ConnectionError(f"Anthropic streaming error: {str(e)}")
            else:
                raise e

    def get_llm_client(self):
        return self.client
