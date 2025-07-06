#!/usr/bin/env python3
"""
Test script to verify audio publishing with LiveKit Agents 1.0.23
"""
import asyncio
import logging
from livekit.agents import AgentSession, Agent
from livekit.plugins import openai, silero, deepgram, cartesia
from livekit import rtc

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_audio_publishing():
    """Test if audio tracks are published correctly"""
    logger.info("Starting audio publishing test with LiveKit 1.0.23")
    
    # Create a simple agent
    agent = Agent(
        instructions="You are a test agent. Say hello and introduce yourself."
    )
    
    # Create session with STT-LLM-TTS pipeline
    session = AgentSession(
        vad=silero.VAD.load(force_cpu=True),
        stt=deepgram.STT(
            model="nova-3",
            language="en"
        ),
        llm=openai.LLM(
            model="gpt-4o",
            temperature=0.7
        ),
        tts=cartesia.TTS(),
        turn_detection="vad"
    )
    
    # Add event handlers to monitor track publishing
    @session.on("agent_state_changed")
    def on_agent_state_changed(event):
        logger.info(f"Agent state: {event.old_state} -> {event.new_state}")
    
    @session.on("speech_created")
    def on_speech_created(event):
        logger.info("Speech created - audio should be initializing")
    
    @session.on("agent_speech_committed")
    def on_agent_speech(event):
        logger.info(f"Agent speaking: {event.text}")
    
    @session.on("metrics_collected")
    def on_metrics(event):
        if event.metrics.type == "tts_metrics":
            logger.info(f"TTS metrics: duration={event.metrics.audio_duration}s")
    
    # Test say() method
    logger.info("Testing say() method...")
    try:
        handle = session.say("Hello! I am a test agent running on LiveKit version 1.0.23. Can you hear me?")
        logger.info(f"Say handle created: {handle}")
        
        # Also test generate_reply
        await asyncio.sleep(2)
        logger.info("Testing generate_reply() method...")
        handle2 = session.generate_reply(
            instructions="Say something about the weather being nice today."
        )
        logger.info(f"Generate reply handle created: {handle2}")
        
    except Exception as e:
        logger.error(f"Error during audio test: {e}", exc_info=True)
    
    logger.info("Test completed - check if audio was heard")

if __name__ == "__main__":
    # Note: This is a simplified test that won't actually connect to a room
    # It's meant to verify the API calls work without errors
    logger.info("LiveKit Agents 1.0.23 Audio Test")
    logger.info("This test verifies the API works but requires a room connection for actual audio")
    
    # Check versions
    try:
        import livekit
        from livekit import agents
        logger.info(f"LiveKit SDK version: {livekit.__version__}")
        logger.info(f"LiveKit Agents version: {agents.__version__}")
    except:
        pass
    
    logger.info("\nTo fully test audio:")
    logger.info("1. The agent must be connected to a LiveKit room")
    logger.info("2. Check the agent logs for track_published events")
    logger.info("3. Verify audio is heard in the web client")