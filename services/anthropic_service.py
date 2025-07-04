from anthropic import AsyncAnthropic
from typing import List, Dict, Optional
import os
import logging

logger = logging.getLogger(__name__)

class AnthropicService:
    def __init__(self):
        self.client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.default_model = "claude-3-5-sonnet-20241022"
        
    async def create_message(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> str:
        """
        Create a message using Claude.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            system: System prompt
            model: Model to use (defaults to Claude 3.5 Sonnet)
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            
        Returns:
            Generated text response
        """
        try:
            response = await self.client.messages.create(
                model=model or self.default_model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                messages=messages
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Error calling Anthropic API: {e}")
            raise
    
    async def stream_message(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7
    ):
        """
        Stream a message response from Claude.
        
        Yields:
            Text chunks as they're generated
        """
        try:
            async with self.client.messages.stream(
                model=model or self.default_model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                messages=messages
            ) as stream:
                async for text in stream.text_stream:
                    yield text
                    
        except Exception as e:
            logger.error(f"Error streaming from Anthropic API: {e}")
            raise