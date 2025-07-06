#!/usr/bin/env python3
"""
LiveKit Agent for Polyglot Flight Search Assistant
Uses OpenAI Realtime API with correct 2025 patterns
"""
import os
import logging
from typing import Dict, Any
from datetime import datetime, date
import json

from dotenv import load_dotenv
from livekit.agents import (
    Agent, AgentSession, JobContext, RunContext,
    WorkerOptions, cli, function_tool, JobProcess, AutoSubscribe,
    io
)
from livekit.plugins import openai, silero, deepgram, cartesia
from livekit import rtc
import aiohttp
import asyncio
import numpy as np

# Import our audio utilities
from audio_utils import resample_audio, create_audio_frame_48khz, generate_test_tone, AudioFrameBuffer

# Load environment variables
load_dotenv()

# Configure logging with more detail
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FlightAPIClient:
    """Client for calling our flight search API"""
    
    def __init__(self):
        self.base_url = os.getenv('API_SERVER_URL', 'http://localhost:8000')
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def search_flights(self, origin: str, destination: str, date: str) -> Dict[str, Any]:
        """Call our API server which uses Amadeus SDK"""
        try:
            async with self.session.get(
                f"{self.base_url}/api/flights",
                params={
                    "origin": origin,
                    "destination": destination,
                    "departure_date": date
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logger.error(f"API error: {response.status}")
                    return {"error": f"API returned {response.status}"}
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return {"error": str(e)}


@function_tool
async def search_flights(
    context: RunContext,
    origin: str,
    destination: str,
    departure_date: str
) -> Dict[str, Any]:
    """Search for available flights between cities.
    
    Args:
        origin: City name or airport code (e.g., 'New York' or 'JFK')
        destination: City name or airport code (e.g., 'Los Angeles' or 'LAX')
        departure_date: Date in YYYY-MM-DD format
    
    Returns:
        Flight search results with pricing and availability
    """
    logger.info(f"Searching flights: {origin} -> {destination} on {departure_date}")
    
    async with FlightAPIClient() as client:
        try:
            results = await client.search_flights(origin, destination, departure_date)
            
            if "error" in results:
                return {
                    "status": "error",
                    "message": f"I'm having trouble searching for flights: {results['error']}"
                }
            
            flights = results.get('flights', [])
            
            if flights:
                flight_count = len(flights)
                
                # Get cheapest flight (handle price strings with currency symbols)
                def get_price(flight):
                    price = flight.get('price', '999999')
                    # Remove currency symbols and convert to float
                    if isinstance(price, str):
                        price = price.replace('$', '').replace(',', '').strip()
                    return float(price)
                
                cheapest = min(flights, key=get_price)
                
                # Format all flights for voice response with better formatting
                flight_list = []
                for i, flight in enumerate(flights[:10], 1):  # Show up to 10 flights
                    flight_list.append(
                        f"Option {i}: {flight['airline']} flight for {flight['price']}, "
                        f"departing at {flight['departure_time']}"
                    )
                
                # Create a more conversational response
                if flight_count > 10:
                    additional_msg = f" I'm showing you the first 10 options. Would you like to filter by airline, time, or price?"
                else:
                    additional_msg = ""
                
                return {
                    "status": "success",
                    "message": f"I found {flight_count} flights from {origin} to {destination}. "
                              f"The cheapest is {cheapest['airline']} for {cheapest['price']}. "
                              f"Here are all available options: " + ". ".join(flight_list) + additional_msg,
                    "flights": flights[:10],  # Return top 10 for details
                    "formatted_flights": flight_list  # For potential UI display
                }
            else:
                return {
                    "status": "no_flights",
                    "message": f"I couldn't find any flights from {origin} to {destination} "
                              f"on {departure_date}. Would you like to try different dates?"
                }
                
        except Exception as e:
            logger.error(f"Search error: {e}")
            return {
                "status": "error",
                "message": "I'm having trouble searching for flights right now. Please try again."
            }


def prewarm(proc: JobProcess):
    """Preload models to prevent performance issues"""
    logger.info("Prewarming models...")
    
    # Preload VAD with optimized settings
    # NOTE: Silero VAD only supports 8kHz and 16kHz
    proc.userdata["vad"] = silero.VAD.load(
        min_speech_duration=0.05,
        min_silence_duration=0.55,
        prefix_padding_duration=0.5,
        activation_threshold=0.5,
        sample_rate=16000,  # Silero VAD limitation - will resample internally
        force_cpu=True  # Prevents GPU contention
    )
    
    logger.info("Models prewarmed successfully")


class ResamplingAudioOutput(io.AudioOutput):
    """Audio output that resamples TTS audio from 24kHz to 48kHz"""
    
    def __init__(self, room: rtc.Room):
        super().__init__()
        self.room = room
        self.audio_source = rtc.AudioSource(sample_rate=48000, num_channels=1)
        self.track_published = False
        self.frame_buffer = AudioFrameBuffer(sample_rate=48000)
        logger.info("Created ResamplingAudioOutput with 48kHz AudioSource")
        
    async def start(self):
        """Start the audio output and publish track"""
        await self.publish_track()
        
    async def publish_track(self):
        """Publish the audio track with proper options"""
        if not self.track_published:
            track = rtc.LocalAudioTrack.create_audio_track(
                "agent_tts_audio", 
                self.audio_source
            )
            
            options = rtc.TrackPublishOptions(
                source=rtc.TrackSource.SOURCE_MICROPHONE,
                dtx=False,  # Disable DTX for TTS
                red=True    # Enable redundancy
            )
            
            publication = await self.room.local_participant.publish_track(track, options)
            logger.info(f"✅ Published audio track with 48kHz: {publication}")
            self.track_published = True
    
    def capture_frame(self, frame: rtc.AudioFrame):
        """Capture audio frame, resampling if necessary"""
        if frame.sample_rate != 48000:
            # Resample to 48kHz
            resampled_data = resample_audio(
                frame.data, 
                original_rate=frame.sample_rate,
                target_rate=48000
            )
            
            # Create frames from resampled data
            frames = self.frame_buffer.add_data(resampled_data)
            for new_frame in frames:
                self.audio_source.capture_frame(new_frame)
                logger.debug(f"Captured resampled frame: {frame.sample_rate}Hz → 48kHz")
        else:
            # Already at 48kHz
            self.audio_source.capture_frame(frame)
    
    async def aclose(self):
        """Close the audio output"""
        pass
    
    def clear_buffer(self):
        """Clear any buffered audio"""
        if hasattr(self, 'frame_buffer'):
            self.frame_buffer.buffer.clear()
    
    async def flush(self):
        """Flush any remaining audio"""
        if hasattr(self, 'frame_buffer'):
            frames = self.frame_buffer.flush()
            for frame in frames:
                self.audio_source.capture_frame(frame)


async def test_audio_tone(room: rtc.Room, duration: float = 1.0):
    """Generate and publish a test tone at 48kHz"""
    logger.info("🔊 Generating test tone at 440Hz...")
    
    # Create audio source at 48kHz
    audio_source = rtc.AudioSource(sample_rate=48000, num_channels=1)
    
    # Create and publish track
    track = rtc.LocalAudioTrack.create_audio_track("test_tone", audio_source)
    options = rtc.TrackPublishOptions(
        source=rtc.TrackSource.SOURCE_MICROPHONE,
        dtx=False
    )
    await room.local_participant.publish_track(track, options)
    
    # Generate test tone
    audio_data = await generate_test_tone(frequency=440, duration=duration, sample_rate=48000)
    
    # Send in 10ms chunks
    chunk_size = 480 * 2  # 480 samples * 2 bytes per sample
    for i in range(0, len(audio_data), chunk_size):
        chunk = audio_data[i:i+chunk_size]
        if len(chunk) == chunk_size:
            frame = rtc.AudioFrame(
                data=chunk,
                sample_rate=48000,
                num_channels=1,
                samples_per_channel=480
            )
            await audio_source.capture_frame(frame)
            await asyncio.sleep(0.01)  # 10ms
    
    logger.info("✅ Test tone complete - you should have heard a beep!")


async def entrypoint(ctx: JobContext):
    """Main entry point for the LiveKit agent"""
    logger.info(f"Agent started for room {ctx.room.name}")
    
    try:
        # Connect to the room with AUDIO_ONLY to prevent video processing overhead
        logger.info("Connecting to room with AUDIO_ONLY subscription...")
        await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
        logger.info("Successfully connected to room")
        
        # Get language preference from room metadata or participant metadata
        language = "en"  # Default to English
        if ctx.room.metadata:
            try:
                room_metadata = json.loads(ctx.room.metadata)
                language = room_metadata.get("language", "en")
                logger.info(f"Language from room metadata: {language}")
            except:
                pass
                
        # Check participant metadata when they join
        for participant in ctx.room.participants.values():
            if participant.metadata:
                try:
                    participant_metadata = json.loads(participant.metadata)
                    language = participant_metadata.get("language", language)
                    logger.info(f"Language from participant {participant.identity}: {language}")
                except:
                    pass
        
        # Test tone option - DISABLED (was causing weird audio)
        # logger.info("🔊 Playing test tone to verify audio...")
        # await test_audio_tone(ctx.room, duration=1.0)
        
        # Get preloaded VAD from prewarm
        vad = ctx.proc.userdata.get("vad")
        if not vad:
            logger.warning("VAD not preloaded, loading now...")
            vad = silero.VAD.load(force_cpu=True)
        
        # Initialize agent with flight booking instructions
        agent = Agent(
            instructions=f"""You are a multilingual flight booking assistant powered by LiveKit and Amadeus.

LANGUAGE CONFIGURATION:
- The user has pre-selected their preferred language: {language}
- You MUST respond ONLY in this language throughout the conversation
- The speech recognition is configured for this specific language
- Do not switch languages even if the user appears to speak another language

SUPPORTED LANGUAGES:
- English (en), Spanish (es), French (fr), German (de), Italian (it)
- Portuguese (pt), Chinese (zh), Japanese (ja), Korean (ko)
- Arabic (ar), Hindi (hi), Russian (ru), Dutch (nl), Swedish (sv)
- And 25+ more languages supported by Deepgram Nova-3

FLIGHT SEARCH:
- When users ask about flights, help them search using natural conversation
- Ask for any missing information (origin, destination, date) in their language
- Present results clearly and conversationally in their language
- Convert city names to appropriate format for search (e.g., "Nueva York" → "New York")

CONVERSATION STYLE:
- Be friendly, helpful, and conversational
- If you don't find specific airlines, acknowledge it and show alternatives
- Format prices and times appropriately for their culture
- When presenting flights, list ALL options clearly, not just top 3
- Ask if they want to filter results when there are many options
- If user switches languages mid-conversation, continue responding but acknowledge the switch

You can search for real flights using the search_flights function.
Always confirm important details like dates and destinations.

DATE HANDLING:
- When users mention dates without a year, assume they mean the current year (2025) or the next occurrence of that date
- For example, if today is July 2025 and user says "October 7", they mean October 7, 2025
- If the date has already passed this year, assume they mean next year
- Always use YYYY-MM-DD format when calling search_flights""",
            tools=[search_flights]
        )
        
        # Configure session with multiple provider options for robustness
        logger.info("Initializing AgentSession with voice providers...")
        
        # Now using LiveKit Agents 1.0.23 which has working audio publishing
        # Both OpenAI Realtime and STT-LLM-TTS pipeline should work
        # Set use_realtime = True to test OpenAI Realtime
        use_realtime = False  # STT-LLM-TTS is more reliable
        
        if use_realtime:
            # Testing OpenAI Realtime with LiveKit 1.0.23
            # This should work according to community reports
            try:
                session = AgentSession(
                    llm=openai.realtime.RealtimeModel(
                        voice="alloy",
                        model="gpt-4o-realtime-preview-2024-12-17",
                        temperature=0.8,
                        tool_choice="auto"
                    ),
                    vad=vad,
                )
                logger.info("🎤 Using OpenAI Realtime with LiveKit 1.0.23")
            except Exception as e:
                logger.warning(f"OpenAI Realtime failed: {e}")
                use_realtime = False
        
        if not use_realtime:
            # Use reliable STT-LLM-TTS pipeline that properly publishes audio tracks
            logger.info("🎵 Using STT-LLM-TTS pipeline for working audio output")
            session = AgentSession(
                vad=vad,
                stt=deepgram.STT(
                    model="nova-3",
                    language=language,  # Use the language from metadata
                    sample_rate=48000  # Match WebRTC requirement
                ),
                llm=openai.LLM(
                    model="gpt-4o",  # Use full GPT-4 for better multilingual support
                    temperature=0.7
                ),
                tts=cartesia.TTS(),  # Use default voice
                turn_detection="vad"
            )
            logger.info("✅ STT-LLM-TTS pipeline configured with Deepgram STT + GPT-4 + Cartesia TTS")
        
        # Create and configure custom audio output with resampling
        custom_audio_output = ResamplingAudioOutput(ctx.room)
        await custom_audio_output.start()
        
        # Override the session's audio output
        session.output._audio = custom_audio_output
        logger.info("✅ Custom audio output with 48kHz resampling configured")
        
        # Add event handlers for debugging with proper error handling
        @session.on("user_state_changed")
        def on_user_state_changed(event):
            try:
                # UserStateChangedEvent has old_state and new_state properties
                logger.info(f"👤 User state changed: {event.old_state} -> {event.new_state}")
            except AttributeError as e:
                logger.error(f"User state event error: {e}")
                logger.info(f"👤 User state event: {event}")
        
        @session.on("agent_state_changed")
        def on_agent_state_changed(event):
            try:
                # AgentStateChangedEvent has old_state and new_state properties
                logger.info(f"🤖 Agent state changed: {event.old_state} -> {event.new_state}")
            except AttributeError as e:
                logger.error(f"Agent state event error: {e}")
                logger.info(f"🤖 Agent state event: {event}")
        
        @session.on("function_call")
        def on_function_call(event):
            try:
                # FunctionCallEvent has function_call_id and function_name
                logger.info(f"🔧 Function called: {event.function_name} (ID: {event.function_call_id})")
            except AttributeError as e:
                logger.error(f"Function call event error: {e}")
                logger.info(f"🔧 Function call event: {event}")
        
        # Add handler for transcription events
        @session.on("input_speech_transcription_completed")
        def on_speech_transcribed(event):
            logger.info(f"💬 User said: {getattr(event, 'text', 'unknown')}")
        
        # Add handler for agent speech
        @session.on("agent_speech_committed") 
        def on_agent_speech(event):
            logger.info(f"🗣️ Agent speaking: {getattr(event, 'text', 'unknown')}")
        
        # Add handler for speech creation (audio initialization)
        @session.on("speech_created")
        def on_speech_created(event):
            logger.info(f"🎵 Speech created - Audio channel active: {event}")
            
        # Monitor TTS events
        @session.on("tts_started")
        def on_tts_started(event):
            logger.info("🎵 TTS STARTED: Generating audio...")
        
        @session.on("tts_stopped") 
        def on_tts_stopped(event):
            logger.info("🎵 TTS STOPPED")
            
        # Monitor when audio is actually being sent
        @session.on("metrics_collected")
        def on_metrics(event):
            if hasattr(event, 'metrics') and hasattr(event.metrics, 'type'):
                if event.metrics.type == 'tts_metrics':
                    logger.info(f"📊 TTS Metrics: duration={getattr(event.metrics, 'audio_duration', 'unknown')}s")
                elif event.metrics.type == 'stt_metrics':
                    logger.debug(f"📊 STT Metrics: {event.metrics}")
                else:
                    logger.debug(f"📊 Metrics: {event.metrics.type}")
        
        # Monitor track publishing
        @ctx.room.on("track_published")
        def on_track_published(publication: rtc.LocalTrackPublication, participant: rtc.LocalParticipant):
            logger.info(f"📡 Track published: {publication.kind} by {participant.identity}")
        
        # Handle participant metadata updates
        @ctx.room.on("participant_metadata_changed")
        def on_participant_metadata_changed(participant: rtc.Participant, prev_metadata: str):
            if participant.metadata:
                try:
                    metadata = json.loads(participant.metadata)
                    new_language = metadata.get("language")
                    if new_language and new_language != language:
                        logger.info(f"Language preference updated to: {new_language}")
                        # Note: Cannot update STT language after initialization
                        # User should reconnect with new language preference
                except Exception as e:
                    logger.error(f"Error parsing participant metadata: {e}")
        
        # Handle audio track subscription (must be sync callback)
        @ctx.room.on("track_subscribed")
        def on_track_subscribed(
            track: rtc.Track, 
            publication: rtc.TrackPublication, 
            participant: rtc.RemoteParticipant
        ):
            if track.kind == rtc.TrackKind.KIND_AUDIO:
                logger.info(f"🎤 Audio track subscribed from {participant.identity}")
                # Check if participant has language preference
                if participant.metadata:
                    try:
                        metadata = json.loads(participant.metadata)
                        participant_lang = metadata.get("language", "en")
                        logger.info(f"Participant {participant.identity} language: {participant_lang}")
                    except:
                        pass
        
        # Start the session with the room
        logger.info("Starting agent session...")
        await session.start(agent=agent, room=ctx.room)
        
        # The agent will now handle participants joining
        logger.info(f"✅ Agent session started successfully for room {ctx.room.name}")
        
        # Initialize conversation with a greeting
        # With STT-LLM-TTS pipeline, we can use session.say() for the initial greeting
        logger.info("Sending initial greeting...")
        try:
            if use_realtime:
                # For Realtime, use generate_reply
                speech_handle = session.generate_reply(
                    instructions="Greet the user warmly in a brief, natural way and ask how you can help them find flights today.",
                    allow_interruptions=True
                )
                logger.info(f"Speech handle created: {speech_handle}")
            else:
                # For STT-LLM-TTS, we can use say() which works properly
                speech_handle = session.say(
                    "Hello! I'm your multilingual flight search assistant. How can I help you find flights today?",
                    allow_interruptions=True
                )
                logger.info(f"Speech handle created: {speech_handle}")
            logger.info("✅ Initial greeting sent")
        except Exception as e:
            logger.error(f"Failed to send greeting: {e}")
            # Continue anyway - the agent will still respond to user input
        
    except Exception as e:
        logger.error(f"❌ Error in entrypoint: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    # Run the agent with LiveKit CLI
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            port=8082,  # Set static debug server port
            host="0.0.0.0",
            ws_url=os.getenv("LIVEKIT_URL", "wss://polyglot-rag-assistant-3l6xagej.livekit.cloud"),
            api_key=os.getenv("LIVEKIT_API_KEY"),
            api_secret=os.getenv("LIVEKIT_API_SECRET")
        )
    )