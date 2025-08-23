import os
from openai import OpenAI


class OpenAIClient:
    """
    Wrapper for OpenAI chat models with comprehensive streaming and async support.
    
    This client provides three interfaces for OpenAI API interaction:
    1. Synchronous generation (generate) - for backward compatibility
    2. Asynchronous generation (generate_async) - for agent system integration
    3. Streaming generation (generate_stream) - for real-time response streaming
    
    All methods include robust error handling for quota limits and API failures
    to ensure graceful degradation rather than system crashes.
    """

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o", temperature: float = 0.6, top_p: float = 0.95):
        """
        Initialize OpenAI client with authentication and model parameters.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY environment variable)
            model: OpenAI model name (e.g., "gpt-4.1-mini", "gpt-4o-mini")
            temperature: Sampling temperature (0.0-2.0, higher = more creative)
            top_p: Nucleus sampling parameter (0.0-1.0, alternative to temperature)
            
        Raises:
            ValueError: If no API key is provided via parameter or environment variable
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY must be provided")
        
        # Initialize OpenAI client with authentication
        self.client = OpenAI(api_key=self.api_key)
        
        # Store model parameters for use in API calls
        self.model = model
        self.temperature = temperature
        self.top_p = top_p

    def generate(self, prompt: str, stream: bool = False, temperature: float = None) -> str:
        """
        Generate response synchronously (for backward compatibility).
        
        This method provides synchronous access to OpenAI API for legacy code
        that doesn't support async operations. It handles both streaming and
        non-streaming modes, collecting all content before returning.
        
        Args:
            prompt: Input prompt text to send to the model
            stream: Whether to use streaming internally (content is still collected and returned as complete text)
            temperature: Override temperature setting (None uses instance default)
        
        Returns:
            Complete response text from the model
            
        Raises:
            Exception: Re-raises non-quota API errors for handling by caller
        """
        # Use provided temperature or fall back to instance default
        actual_temperature = temperature if temperature is not None else self.temperature
        
        try:
            # Make API call to OpenAI with specified parameters
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=actual_temperature,
                top_p=self.top_p,
                stream=stream,
            )
            
            # Handle response based on streaming mode
            if not stream:
                # Non-streaming: return complete response immediately
                return response.choices[0].message.content
            else:
                # Streaming: collect all chunks into complete response
                content = ""
                for chunk in response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        content += chunk.choices[0].delta.content
                return content
        except Exception as e:
            # Handle quota errors and other OpenAI API issues gracefully
            # This ensures synchronous calls don't crash the system
            error_msg = str(e)
            if "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                # For quota/rate limit errors, return a clean helpful message without exposing request details
                return "OpenAI API quota exceeded. This is a temporary limitation. Please check your OpenAI billing or try a different model."
            # Handle other server-side errors that should be retried
            elif any(term in error_msg.lower() for term in ['500', '502', '503', '504', 'overloaded', 'connection', 'timeout']):
                raise ConnectionError(f"OpenAI server error: {str(e)}")
            else:
                # Re-raise other errors that might indicate code issues
                raise e

    async def generate_async(self, prompt: str, temperature: float = None) -> str:
        """
        Generate response asynchronously for agent system compatibility.
        
        This method provides the async interface expected by the agent system's
        fallback path. It wraps the synchronous OpenAI client in a thread pool
        to avoid blocking the main async event loop, ensuring proper integration
        with the multi-agent system's async architecture.
        
        Args:
            prompt: Input prompt text to send to the model
            temperature: Override temperature setting (None uses instance default)
            
        Returns:
            Complete response text from the model
            
        Raises:
            Exception: Re-raises non-quota API errors for handling by agent system
        """
        # Use provided temperature or fall back to instance default
        actual_temperature = temperature if temperature is not None else self.temperature
        
        # Use synchronous client in thread pool for true async behavior
        # This prevents blocking the main event loop
        import asyncio
        import concurrent.futures
        
        def _sync_generate():
            """
            Inner synchronous function to be executed in thread pool.
            
            This function encapsulates the OpenAI API call so it can be run
            in a separate thread, preventing blocking of the async event loop.
            """
            try:
                # Make synchronous API call to OpenAI
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=actual_temperature,
                    top_p=self.top_p,
                    stream=False,  # Non-streaming for async wrapper
                )
                return response.choices[0].message.content
            except Exception as e:
                # Handle quota errors and other OpenAI API issues gracefully
                # This prevents the entire agent system from crashing due to API limitations
                error_msg = str(e)
                if "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                    # For quota/rate limit errors, return a clean helpful message without exposing request details
                    return "OpenAI API quota exceeded. This is a temporary limitation. Please check your OpenAI billing or try a different model."
                # Handle other server-side errors that should be retried
                elif any(term in error_msg.lower() for term in ['500', '502', '503', '504', 'overloaded', 'connection', 'timeout']):
                    raise ConnectionError(f"OpenAI server error: {str(e)}")
                else:
                    # Re-raise other errors that might be code-related
                    raise e
        
        # Execute the synchronous function in a thread pool to maintain async behavior
        # This allows the main event loop to continue processing other tasks
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(executor, _sync_generate)
        
        return result

    async def generate_stream(self, prompt: str, temperature: float = None):
        """
        Generate streaming response from prompt using OpenAI API.
        
        This method provides real-time streaming of the model's response,
        yielding content chunks as they arrive from the OpenAI API.
        Optimized for maximum throughput with minimal delays while maintaining
        proper async behavior through periodic event loop yielding.
        
        Args:
            prompt: Input prompt text to send to the model
            temperature: Override temperature setting (None uses instance default)
            
        Yields:
            str: Content chunks as they arrive from OpenAI API
            
        Note:
            In case of quota/rate limit errors, yields an error message
            instead of crashing, maintaining the streaming interface.
        """
        # Use provided temperature or fall back to instance default
        actual_temperature = temperature if temperature is not None else self.temperature
        
        try:
            # Create streaming response from OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=actual_temperature,
                top_p=self.top_p,
                stream=True  # Enable streaming mode
            )
            
            # Process and yield streaming chunks as they arrive
            # Optimized for speed with minimal event loop yielding
            import asyncio
            chunk_count = 0
            for chunk in response:
                # Check if chunk contains actual content (not metadata)
                if chunk.choices and chunk.choices[0].delta.content:
                    chunk_count += 1
                    yield chunk.choices[0].delta.content
                    
                    # Periodically yield control to the event loop for other async tasks
                    # Only every 5 chunks to maximize throughput while maintaining responsiveness
                    if chunk_count % 5 == 0:
                        await asyncio.sleep(0)  # Minimal yield without actual delay
                        
        except Exception as e:
            # Handle quota errors in streaming by yielding error message as streaming content
            # This maintains the streaming interface even when API calls fail
            error_msg = str(e)
            if "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                # For quota/rate limit errors, yield a clean helpful message without exposing request details
                yield "OpenAI API quota exceeded. This is a temporary limitation. Please check your OpenAI billing or try a different model."
            # Handle other server-side errors that should be retried
            elif any(term in error_msg.lower() for term in ['500', '502', '503', '504', 'overloaded', 'connection', 'timeout']):
                raise ConnectionError(f"OpenAI streaming error: {str(e)}")
            else:
                # For other errors, yield generic error message and stop streaming
                yield f"OpenAI API Error: {str(e)}"

    def get_llm_client(self):
        """
        Get the underlying OpenAI client instance.
        
        This method provides access to the raw OpenAI client for advanced usage
        or integration with systems that expect direct OpenAI client access.
        Used by the agent system to access the underlying client for compatibility
        with different LLM client interfaces.
        
        Returns:
            OpenAI: The underlying OpenAI client instance
        """
        return self.client
