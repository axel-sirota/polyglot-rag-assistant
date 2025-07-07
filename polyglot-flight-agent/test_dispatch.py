#!/usr/bin/env python3
"""
Minimal test agent to debug LiveKit dispatch issues
Tests if job requests are being received at all
"""
import os
import logging
import asyncio
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli

load_dotenv()
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_request(request):
    """Log all job requests"""
    logger.info("="*50)
    logger.info(f"JOB REQUEST RECEIVED!")
    logger.info(f"Room: {request.room}")
    logger.info(f"Job ID: {request.job_id}")
    logger.info(f"Participant count: {request.participant_count}")
    
    # Log all attributes of request
    logger.info("Request attributes:")
    for attr in dir(request):
        if not attr.startswith('_'):
            try:
                value = getattr(request, attr)
                logger.info(f"  {attr}: {value}")
            except:
                pass
    logger.info("="*50)
    
    return True  # Accept all jobs

async def test_entrypoint(ctx: JobContext):
    logger.info(f"✅ ENTRYPOINT CALLED for room: {ctx.room.name}")
    await ctx.connect()
    logger.info("✅ Connected successfully")
    # Keep alive for 1 hour
    await asyncio.sleep(3600)

if __name__ == "__main__":
    logger.info("Starting minimal test agent...")
    logger.info(f"LiveKit URL: {os.getenv('LIVEKIT_URL')}")
    logger.info(f"API Key: {os.getenv('LIVEKIT_API_KEY')[:10]}...")
    
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=test_entrypoint,
            request_fnc=test_request,
            ws_url=os.getenv("LIVEKIT_URL"),
            api_key=os.getenv("LIVEKIT_API_KEY"),
            api_secret=os.getenv("LIVEKIT_API_SECRET"),
            num_idle_processes=1
        )
    )