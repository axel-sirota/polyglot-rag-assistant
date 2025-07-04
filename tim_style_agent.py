#!/usr/bin/env python3
"""
LiveKit Voice Assistant - Tim's Style
Simple and working implementation
"""

import asyncio
import os
import logging
from livekit import agents
from livekit.agents import JobContext, WorkerOptions, cli, llm
from livekit.plugins import openai, silero
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def entrypoint(ctx: JobContext):
    """Main entrypoint following Tim's pattern"""
    
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            "You are a helpful voice assistant. Your interface with users will be voice. "
            "You should use short and concise responses, and avoid using unpronounceable punctuation."
        ),
    )
    
    logger.info(f"Connecting to room {ctx.room.name}")
    await ctx.connect()
    
    logger.info("Waiting for participant...")
    participant = await ctx.wait_for_participant()
    logger.info(f"Participant joined: {participant.identity}")
    
    # Create voice assistant
    assistant = agents.VoiceAssistant(
        vad=silero.VAD.load(),
        stt=openai.STT(model="whisper-1"),
        llm=openai.LLM(model="gpt-4o"),
        tts=openai.TTS(model="tts-1", voice="alloy"),
        chat_ctx=initial_ctx,
    )
    
    # Start the assistant
    assistant.start(ctx.room)
    
    # Initial greeting
    await assistant.say(
        "Hello! I'm your voice assistant. How can I help you today?",
        allow_interruptions=True
    )
    
    logger.info("Assistant started successfully")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))