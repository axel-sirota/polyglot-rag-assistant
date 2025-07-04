#!/usr/bin/env python3

import asyncio
import logging
from livekit import agents, rtc
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.plugins import openai, silero
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("voice-agent")


async def entrypoint(ctx: JobContext):
    """Main entrypoint for the agent"""
    
    # Initial chat context
    initial_ctx = agents.llm.ChatContext().append(
        role="system",
        text=(
            "You are a helpful multilingual flight assistant. "
            "Your interface with users will be voice. "
            "You should use short and concise responses, and avoid using unpronounceable punctuation. "
            "When users ask about flights, help them find flight information."
        ),
    )
    
    logger.info(f"Connecting to room {ctx.room.name}")
    await ctx.connect()
    
    logger.info("Setting up voice pipeline")
    
    # Create the agent
    agent = agents.voice_pipeline.VoicePipelineAgent(
        vad=silero.VAD.load(),
        stt=openai.STT(),
        llm=openai.LLM(),
        tts=openai.TTS(),
        chat_ctx=initial_ctx,
    )
    
    # Handle participant connection
    @ctx.room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant):
        logger.info(f"Participant connected: {participant.identity}")
    
    # Start the agent
    agent.start(ctx.room)
    
    # Initial greeting
    await agent.say("Hello! I'm your multilingual flight assistant. How can I help you today?")
    
    logger.info("Agent started and ready")


if __name__ == "__main__":
    # Run with proper worker options
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        )
    )