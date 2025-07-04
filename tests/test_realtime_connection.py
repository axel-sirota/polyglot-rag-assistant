#!/usr/bin/env python3
"""Test Realtime API connection"""
import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.realtime_client import RealtimeClient, check_realtime_access
from services.functions import REALTIME_FUNCTIONS
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_connection():
    """Test basic Realtime API connection"""
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("No OPENAI_API_KEY found in environment")
        return
    
    # Check access
    logger.info("Checking Realtime API access...")
    has_access = await check_realtime_access(api_key)
    logger.info(f"Realtime API access check: {has_access}")
    
    # Try to connect
    logger.info("Creating Realtime client...")
    client = RealtimeClient(api_key)
    
    try:
        logger.info("Connecting to Realtime API...")
        await client.connect()
        
        if client.is_connected:
            logger.info("✅ Successfully connected to Realtime API!")
            logger.info(f"Session ID: {client.session_id}")
            
            # Test sending a simple text message
            logger.info("Sending test message...")
            await client.send_text("Hello, can you hear me?")
            
            # Listen for a few events
            logger.info("Listening for events...")
            event_count = 0
            timeout = 10  # seconds
            
            async def process_events():
                nonlocal event_count
                async for event in client.process_events():
                    event_count += 1
                    logger.info(f"Event {event_count}: {event['type']}")
                    
                    if event["type"] == "response_done":
                        logger.info("Response completed!")
                        break
                        
                    if event_count > 20:  # Safety limit
                        break
            
            try:
                await asyncio.wait_for(process_events(), timeout=timeout)
            except asyncio.TimeoutError:
                logger.warning(f"Timeout after {timeout} seconds")
            
            logger.info(f"Received {event_count} events")
            
        else:
            logger.error("❌ Failed to connect to Realtime API")
            
    except Exception as e:
        logger.error(f"❌ Connection error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if client.is_connected:
            logger.info("Disconnecting...")
            await client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_connection())