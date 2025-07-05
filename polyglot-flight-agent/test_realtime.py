#!/usr/bin/env python3
"""
Test OpenAI Realtime API connection directly
"""
import os
import asyncio
import logging
from dotenv import load_dotenv
from livekit.plugins import openai
import json

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_realtime():
    """Test OpenAI Realtime model initialization"""
    try:
        # Check API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY not set!")
            return
        
        logger.info(f"API Key present: {api_key[:10]}...")
        
        # Try to create Realtime model
        logger.info("Creating OpenAI Realtime model...")
        model = openai.realtime.RealtimeModel(
            voice="alloy",
            model="gpt-4o-realtime-preview-2024-12-17",
            temperature=0.8,
            tool_choice="auto"
        )
        logger.info("Model created successfully")
        
        # Check model attributes
        logger.info(f"Model type: {type(model)}")
        logger.info(f"Model attributes: {dir(model)}")
        
        # Try to check if it has WebSocket URL
        if hasattr(model, '_url'):
            logger.info(f"WebSocket URL: {model._url}")
        
        if hasattr(model, '_api_key'):
            logger.info(f"API key configured: {bool(model._api_key)}")
            
    except Exception as e:
        logger.error(f"Failed to test Realtime: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_realtime())