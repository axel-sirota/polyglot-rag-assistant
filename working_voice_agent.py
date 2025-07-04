#!/usr/bin/env python3
"""
Working LiveKit Voice Agent - Tested Configuration
"""

import asyncio
import logging
from typing import Annotated
from livekit import agents, rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
)
from livekit.plugins import openai, silero
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("voice-agent")
logger.setLevel(logging.INFO)


async def entrypoint(job: JobContext):
    """Main entry point for the agent."""
    logger.info(f"Agent started for room {job.room.name}")
    
    # Connect to the room with auto-subscribe
    await job.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    # Wait for a participant to connect
    participant = await job.wait_for_participant()
    logger.info(f"Participant connected: {participant.identity}")
    
    # Create initial chat context
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            "You are a helpful voice assistant. Your interface with users will be voice. "
            "You should use short and concise responses, and avoid using unpronounceable punctuation. "
            "You can help users find flight information between cities."
        ),
    )
    
    # Set up the voice pipeline agent
    assistant = agents.voice_pipeline.VoicePipelineAgent(
        vad=silero.VAD.load(),
        stt=openai.STT(model="whisper-1"),
        llm=openai.LLM(model="gpt-4o"),
        tts=openai.TTS(model="tts-1", voice="alloy"),
        chat_ctx=initial_ctx,
    )
    
    # Start the assistant
    assistant.start(job.room, participant)
    
    # Send initial greeting
    await assistant.say(
        "Hello! I'm your voice assistant. I can help you find flights. Just tell me where you'd like to go!",
        allow_interruptions=True
    )
    
    logger.info("Voice pipeline started successfully")


async def request_fnc(job: JobContext) -> None:
    """
    This function is called when a new job request is received.
    It decides whether to accept the job or not.
    """
    logger.info(f"Received job request for room {job.room.name}")
    # Accept all jobs for now
    await job.accept()


if __name__ == "__main__":
    # Run the worker
    cli.run_app(
        WorkerOptions(
            request_fnc=request_fnc,
            entrypoint_fnc=entrypoint,
            # Worker options
        )
    )