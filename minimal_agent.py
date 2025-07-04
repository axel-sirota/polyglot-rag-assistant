#!/usr/bin/env python3
"""
Minimal LiveKit Voice Agent
"""

import logging
from livekit.agents import JobContext, WorkerOptions, cli, llm
from livekit.agents.voice import Agent
from livekit.plugins import openai, silero

logging.basicConfig(level=logging.INFO)


async def entrypoint(ctx: JobContext):
    # Connect to room
    await ctx.connect()
    
    # Create and start agent
    agent = Agent(
        vad=silero.VAD.load(),
        stt=openai.STT(),
        llm=openai.LLM(),
        tts=openai.TTS(),
    )
    
    agent.start(ctx.room)
    
    # Greet when ready
    await agent.say("Hello! I can hear you now.")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))