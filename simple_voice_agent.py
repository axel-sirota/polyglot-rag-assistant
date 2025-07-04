#!/usr/bin/env python3
"""
Simple LiveKit Voice Agent - Working Implementation
"""

import logging
from livekit import agents
from livekit.agents import JobContext, WorkerOptions, cli, llm
from livekit.agents.voice import Agent
from livekit.plugins import openai, silero
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def entrypoint(ctx: JobContext):
    """Simple working entrypoint"""
    
    # Connect to room
    await ctx.connect()
    logger.info(f"Connected to room: {ctx.room.name}")
    
    # Create chat context
    initial_ctx = llm.ChatContext().append(
        role="system",
        text="You are a helpful voice assistant. Keep responses short and conversational."
    )
    
    # Create voice agent
    agent = Agent(
        vad=silero.VAD.load(),
        stt=openai.STT(model="whisper-1"),
        llm=openai.LLM(model="gpt-4o"),
        tts=openai.TTS(model="tts-1", voice="alloy"),
        chat_ctx=initial_ctx,
    )
    
    # Start agent
    agent.start(ctx.room)
    
    # Say hello
    await agent.say("Hello! I'm your voice assistant. How can I help you?", allow_interruptions=True)
    

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))