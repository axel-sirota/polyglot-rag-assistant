#!/usr/bin/env python3
"""
Test script to verify LiveKit audio track publishing issue
This tests if TTS audio is properly published as LiveKit tracks
"""
import asyncio
import logging
import os
from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import AgentSession, cli, WorkerOptions
from livekit.plugins import openai, deepgram, cartesia, silero

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_entrypoint(ctx: agents.JobContext):
    """Test agent that verifies audio publishing"""
    logger.info(f"🔬 Test agent started for room {ctx.room.name}")
    
    # Connect to room
    await ctx.connect(auto_subscribe=agents.AutoSubscribe.AUDIO_ONLY)
    logger.info("✅ Connected to room")
    
    # Monitor track publishing
    track_published = asyncio.Event()
    published_tracks = []
    
    @ctx.room.on("track_published")
    def on_track_published(publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
        logger.info(f"📡 Remote track published: {publication.kind} by {participant.identity}")
        published_tracks.append((publication, participant))
    
    @ctx.room.on("local_track_published")
    def on_local_track_published(publication: rtc.LocalTrackPublication, track: rtc.Track):
        logger.info(f"📡 LOCAL TRACK PUBLISHED: {publication.kind} (sid: {publication.sid})")
        published_tracks.append((publication, track))
        if publication.kind == rtc.TrackKind.KIND_AUDIO:
            track_published.set()
    
    # Create agent with minimal configuration
    agent = agents.Agent(
        instructions="You are a test agent. Just say hello.",
        tools=[]
    )
    
    # Use STT-LLM-TTS pipeline
    vad = silero.VAD.load(force_cpu=True)
    
    session = AgentSession(
        vad=vad,
        stt=deepgram.STT(model="nova-3"),
        llm=openai.LLM(model="gpt-4o"),
        tts=cartesia.TTS(),  # or openai.TTS(model="tts-1")
        turn_detection="vad"
    )
    
    # Monitor speech events
    @session.on("speech_created")
    def on_speech_created(event):
        logger.info(f"🎵 Speech created: {event}")
    
    @session.on("metrics_collected")
    def on_metrics(event):
        if hasattr(event.metrics, 'audio_duration'):
            logger.info(f"📊 TTS Metrics: audio_duration={event.metrics.audio_duration}")
    
    # Start the session
    logger.info("🚀 Starting agent session...")
    await session.start(agent=agent, room=ctx.room)
    
    # Test 1: Direct say() call
    logger.info("🧪 Test 1: Testing direct say() call...")
    handle = session.say("Hello from the test agent. This is a test of audio publishing.")
    await handle
    
    # Wait a bit to see if track gets published
    logger.info("⏳ Waiting for audio track to be published...")
    try:
        await asyncio.wait_for(track_published.wait(), timeout=5.0)
        logger.info("✅ SUCCESS: Audio track was published!")
    except asyncio.TimeoutError:
        logger.error("❌ FAIL: No audio track published within 5 seconds")
    
    # Test 2: Check session output configuration
    logger.info(f"🔍 Session output audio: {session.output.audio}")
    logger.info(f"🔍 Session output audio enabled: {session.output.audio_enabled}")
    
    # Test 3: Check if RoomIO was created
    logger.info(f"🔍 Session has RoomIO: {hasattr(session, '_room_io') and session._room_io is not None}")
    
    # List all published tracks
    logger.info(f"📋 Total published tracks: {len(published_tracks)}")
    for track in published_tracks:
        logger.info(f"  - {track}")
    
    # Keep agent alive for manual testing
    logger.info("🎤 Agent ready for manual testing. Join the room to test.")
    await asyncio.sleep(300)  # 5 minutes


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=test_entrypoint,
            port=8082  # Different port to avoid conflicts
        )
    )