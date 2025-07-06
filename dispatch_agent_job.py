#!/usr/bin/env python3
"""Dispatch a job to the LiveKit agent"""
import os
import asyncio
from dotenv import load_dotenv
from livekit import api
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def dispatch_job():
    """Dispatch a job to the agent"""
    # Get credentials
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    ws_url = os.getenv("LIVEKIT_URL", "wss://polyglot-rag-assistant-3l6xagej.livekit.cloud")
    
    logger.info(f"Dispatching job to: {ws_url}")
    
    # Create agent dispatch request
    agent_service = api.AgentService(ws_url, api_key, api_secret)
    
    try:
        # Create job for the agent
        job = await agent_service.create_agent_dispatch(
            api.CreateAgentDispatchRequest(
                room="flight-demo",
                # Optional: specify agent name if you have multiple
                # agent_name="polyglot-flight-agent",
                metadata="{'auto_join': true}"
            )
        )
        
        logger.info(f"✅ Job dispatched successfully!")
        logger.info(f"Job ID: {job.agent_dispatch.id if hasattr(job, 'agent_dispatch') else 'Unknown'}")
        logger.info(f"Room: flight-demo")
        logger.info(f"Check your browser - the agent should join shortly!")
        
    except Exception as e:
        logger.error(f"Failed to dispatch job: {e}")
        logger.info("\nAlternative: Try joining with metadata in the browser:")
        logger.info("Add to your connection options: ")
        logger.info('  metadata: {"agent": true}')

if __name__ == "__main__":
    asyncio.run(dispatch_job())