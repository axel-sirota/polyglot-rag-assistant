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
import asyncio

from dotenv import load_dotenv
from livekit.agents import (
    Agent, AgentSession, JobContext, RunContext,
    WorkerOptions, cli, function_tool, JobProcess, AutoSubscribe,
    io, RoomInputOptions
)
from livekit.plugins import openai, silero, deepgram, cartesia
from livekit import rtc
import aiohttp
import asyncio
import numpy as np
import time
from typing import Dict, Optional

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

# Global dictionary to store session state outside of AgentSession
# This enables persistence across disconnections
PARTICIPANT_SESSIONS: Dict[str, Dict] = {}


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
    
    async def search_flights(self, origin: str, destination: str, date: str, preferred_airline: str = None, cabin_class: str = "economy") -> Dict[str, Any]:
        """Call our API server which uses Amadeus SDK"""
        try:
            params = {
                "origin": origin,
                "destination": destination,
                "departure_date": date,
                "cabin_class": cabin_class
            }
            if preferred_airline:
                params["preferred_airline"] = preferred_airline
                
            async with self.session.get(
                f"{self.base_url}/api/flights",
                params=params
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
    departure_date: str,
    preferred_airline: str = None,
    cabin_class: str = "economy"
) -> Dict[str, Any]:
    """Search for available flights between cities.
    
    Args:
        origin: City name or airport code (e.g., 'New York' or 'JFK')
        destination: City name or airport code (e.g., 'Los Angeles' or 'LAX')
        departure_date: Date in YYYY-MM-DD format
        preferred_airline: Specific airline requested by user (e.g., 'American Airlines', 'United', 'Delta')
        cabin_class: Class of service (economy, business, first)
    
    Returns:
        Flight search results with pricing and availability
    """
    logger.info(f"Searching flights: {origin} -> {destination} on {departure_date}, airline: {preferred_airline}, class: {cabin_class}")
    
    async with FlightAPIClient() as client:
        try:
            results = await client.search_flights(origin, destination, departure_date, preferred_airline, cabin_class)
            
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
                
                # Check if we found the preferred airline
                airline_found = False
                if preferred_airline:
                    airline_found = any(preferred_airline.lower() in flight.get('airline', '').lower() for flight in flights)
                
                # Separate nonstop and connecting flights
                nonstop_flights = [f for f in flights if f.get('stops', 0) == 0]
                connecting_flights = [f for f in flights if f.get('stops', 0) > 0]
                
                # Format response in human-friendly way
                response_parts = []
                
                if nonstop_flights:
                    response_parts.append("Non stop flights:")
                    for flight in nonstop_flights[:5]:
                        response_parts.append(
                            f"- Airline: {flight['airline']}, Price: {flight['price']}"
                        )
                
                if connecting_flights:
                    if nonstop_flights:
                        response_parts.append("\nFlights with layover:")
                    else:
                        response_parts.append("Flights with layover:")
                    
                    # Sort by price
                    connecting_sorted = sorted(connecting_flights, key=get_price)[:10]
                    for flight in connecting_sorted:
                        # Format stops information
                        stops_info = ""
                        if 'layovers' in flight and flight['layovers']:
                            stops_info = f", stops: {flight['layovers']}"
                        elif 'stops' in flight:
                            stops_info = f", {flight['stops']} stop(s)"
                        
                        response_parts.append(
                            f"- Airline: {flight['airline']}, price: {flight['price']}, "
                            f"duration: {flight.get('duration', 'TBD')}{stops_info}"
                        )
                
                # Add airline-specific message
                airline_msg = ""
                if preferred_airline and not airline_found:
                    airline_msg = f"I couldn't find any {preferred_airline} flights on this route. Here are alternative options. "
                elif preferred_airline and airline_found:
                    airline_msg = f"I found {preferred_airline} flights. "
                else:
                    airline_msg = "I found these flights:\n\n"
                
                # Build final message
                final_message = airline_msg + "\n".join(response_parts)
                
                # Add note about more options if needed
                if flight_count > 15:
                    final_message += f"\n\nShowing top results from {flight_count} total flights. Need specific times or airlines?"
                
                return {
                    "status": "success",
                    "message": final_message,
                    "flights": flights[:15],  # Return more for chat display
                    "nonstop_count": len(nonstop_flights),
                    "connecting_count": len(connecting_flights),
                    "preferred_airline_found": airline_found
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
    logger.info("="*50)
    logger.info("🔥 PREWARMING MODELS...")
    logger.info(f"🔧 Process ID: {os.getpid()}")
    logger.info("="*50)
    
    # Preload VAD with optimized settings
    logger.info("📊 Loading Silero VAD...")
    logger.info("   - min_speech_duration: 0.05s")
    logger.info("   - min_silence_duration: 0.55s")
    logger.info("   NOTE: Silero VAD only supports 8kHz and 16kHz")
    
    proc.userdata["vad"] = silero.VAD.load(
        min_speech_duration=0.05,
        min_silence_duration=0.55,
        prefix_padding_duration=0.5,
        activation_threshold=0.5,
        sample_rate=16000,  # Silero VAD limitation - will resample internally
        force_cpu=True  # Prevents GPU contention
    )
    
    logger.info("✅ VAD loaded and cached in process userdata")
    
    logger.info("="*50)
    logger.info("✅ PREWARM COMPLETE")
    logger.info("="*50)


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
    """Main entry point for the LiveKit agent with version-safe persistence"""
    logger.info("="*60)
    logger.info(f"🚀 AGENT STARTING - Room: {ctx.room.name}")
    logger.info(f"📋 Job ID: {ctx.job.id if hasattr(ctx.job, 'id') else 'N/A'}")
    logger.info(f"🔧 Process ID: {os.getpid()}")
    logger.info(f"📊 Job metadata: {ctx.job.metadata if hasattr(ctx.job, 'metadata') else 'None'}")
    logger.info(f"📊 Room metadata: {ctx.room.metadata}")
    logger.info("="*60)
    
    # Track if we've greeted participants already
    greeted_participants = set()
    
    # Note: You may see a 404 error from OpenAI during startup - this is harmless
    # It's just the OpenAI client library checking for available endpoints
    
    try:
        # Connect to the room with AUDIO_ONLY to prevent video processing overhead
        logger.info("🔌 Attempting to connect to LiveKit room...")
        logger.info(f"📡 Connection mode: AUDIO_ONLY subscription")
        await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
        logger.info("✅ Successfully connected to room!")
        logger.info(f"👥 Participants in room: {len(ctx.room.remote_participants)}")
        
        # Log all participants
        if ctx.room.remote_participants:
            for p_id, participant in ctx.room.remote_participants.items():
                logger.info(f"  - Participant: {participant.identity} (SID: {p_id})")
        
        # Get language preference from room metadata or participant metadata
        logger.info("🌐 LANGUAGE DETECTION STARTING...")
        language = "en"  # Default to English
        logger.info(f"📝 Default language: {language}")
        
        # Check room metadata
        logger.info(f"🏠 Room metadata: '{ctx.room.metadata}'")
        if ctx.room.metadata:
            try:
                room_metadata = json.loads(ctx.room.metadata)
                logger.info(f"📊 Parsed room metadata: {room_metadata}")
                room_language = room_metadata.get("language", "en")
                if room_language != "en":
                    language = room_language
                    logger.info(f"🎯 Language from room metadata: {language}")
            except Exception as e:
                logger.error(f"❌ Failed to parse room metadata: {e}")
                
        # Check for participants already in the room
        logger.info(f"👥 Checking {len(ctx.room.remote_participants)} participants for language preference...")
        for participant in ctx.room.remote_participants.values():
            logger.info(f"🔍 Checking participant: {participant.identity}")
            logger.info(f"   - Metadata: '{participant.metadata}'")
            logger.info(f"   - Metadata type: {type(participant.metadata)}")
            
            if participant.metadata:
                try:
                    participant_metadata = json.loads(participant.metadata)
                    logger.info(f"   ✅ Parsed metadata: {participant_metadata}")
                    participant_language = participant_metadata.get("language")
                    if participant_language:
                        language = participant_language
                        logger.info(f"   🎯 Got language from participant: {language}")
                        break
                except Exception as e:
                    logger.error(f"   ❌ Error parsing participant metadata: {e}")
        
        logger.info("="*40)
        logger.info(f"🌍 FINAL LANGUAGE SELECTION: {language}")
        logger.info("="*40)
        
        # Test tone option - DISABLED (was causing weird audio)
        # logger.info("🔊 Playing test tone to verify audio...")
        # await test_audio_tone(ctx.room, duration=1.0)
        
        # Get preloaded VAD from prewarm
        logger.info("🎤 VOICE ACTIVITY DETECTION SETUP...")
        vad = ctx.proc.userdata.get("vad")
        if not vad:
            logger.warning("⚠️  VAD not preloaded, loading now...")
            logger.info("📊 Loading Silero VAD with force_cpu=True")
            vad = silero.VAD.load(force_cpu=True)
            logger.info("✅ VAD loaded successfully")
        else:
            logger.info("✅ Using preloaded VAD from prewarm")
        
        # Initialize agent with flight booking instructions
        logger.info("🤖 INITIALIZING AGENT...")
        logger.info(f"📝 Agent language setting: {language}")
        agent = Agent(
            instructions=f"""You are a multilingual flight booking assistant powered by LiveKit and Amadeus.

LANGUAGE CONFIGURATION:
- The user has pre-selected their preferred language: {language}
- You MUST respond ONLY in this language throughout the conversation
- The speech recognition is configured for this specific language
- Do not switch languages even if the user appears to speak another language

IMPORTANT: This is a persistent session. If someone rejoins after disconnecting, welcome them back naturally and continue where you left off.

SUPPORTED LANGUAGES:
- English (en), Spanish (es), French (fr), German (de), Italian (it)
- Portuguese (pt), Chinese (zh), Japanese (ja), Korean (ko)
- Arabic (ar), Hindi (hi), Russian (ru), Dutch (nl), Swedish (sv)
- And 25+ more languages supported by Deepgram Nova-3

FLIGHT SEARCH:
- When users ask about flights, help them search using natural conversation
- Extract any airline preference from their request (e.g., "American Airlines flights", "United", "AA")
- Ask for any missing information (origin, destination, date) in their language
- Present results clearly and conversationally in their language
- Convert city names to appropriate format for search (e.g., "Nueva York" → "New York")

AIRLINE PREFERENCE:
- ALWAYS extract airline if mentioned and pass as preferred_airline parameter
- Common airlines: "Delta", "American Airlines", "United", "Southwest", "JetBlue", "Spirit", "Frontier", "Alaska"
- Also recognize airline codes: "AA" (American), "UA" (United), "DL" (Delta), "WN" (Southwest), etc.
- If specific airline requested but not found, MUST try fallback APIs and acknowledge the search

CABIN CLASS:
- ALWAYS extract cabin class from user request and pass it to search_flights
- Keywords to listen for:
  * "business" or "business class" → cabin_class="business"
  * "first" or "first class" → cabin_class="first"
  * "premium" or "premium economy" → cabin_class="premium_economy"
  * "economy" or no mention → cabin_class="economy"
- When user says "search for business class flights" → MUST pass cabin_class="business"
- When user says "what is the price in business class" → search again with cabin_class="business"
- Default to "economy" if not specified

CONVERSATION STYLE:
- Be friendly, helpful, and conversational
- If you don't find specific airlines, acknowledge it and show alternatives
- Format prices and times appropriately for their culture
- When presenting flights, list ALL options clearly, not just top 3
- Ask if they want to filter results when there are many options
- If user switches languages mid-conversation, continue responding but acknowledge the switch
- NEVER use markdown formatting like asterisks (*), hashes (#), or any other markdown symbols
- Your responses will be spoken aloud, so format them as natural speech only

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
        logger.info("="*50)
        logger.info("🎙️ CONFIGURING VOICE PIPELINE...")
        logger.info("="*50)
        
        # Now using LiveKit Agents 1.0.23 which has working audio publishing
        # Both OpenAI Realtime and STT-LLM-TTS pipeline should work
        # Set use_realtime = True to test OpenAI Realtime
        use_realtime = False  # STT-LLM-TTS is more reliable
        logger.info(f"📊 Pipeline selection: {'OpenAI Realtime' if use_realtime else 'STT-LLM-TTS'}")
        
        if use_realtime:
            # Testing OpenAI Realtime with LiveKit 1.0.23
            # This should work according to community reports
            logger.info("🔧 Attempting to configure OpenAI Realtime...")
            try:
                logger.info("   - Model: gpt-4o-realtime-preview-2024-12-17")
                logger.info("   - Voice: alloy")
                logger.info("   - Temperature: 0.8")
                session = AgentSession(
                    llm=openai.realtime.RealtimeModel(
                        voice="alloy",
                        model="gpt-4o-realtime-preview-2024-12-17",
                        temperature=0.8,
                        tool_choice="auto"
                    ),
                    vad=vad,
                )
                logger.info("✅ OpenAI Realtime configured successfully")
            except Exception as e:
                logger.error(f"❌ OpenAI Realtime failed: {e}")
                use_realtime = False
        
        if not use_realtime:
            # Use reliable STT-LLM-TTS pipeline that properly publishes audio tracks
            logger.info("🎵 Using STT-LLM-TTS pipeline for working audio output")
            # Map UI language codes to Deepgram language codes
            language_mapping = {
                "es": "es",  # Spanish
                "en": "en-US",  # English US
                "fr": "fr",  # French
                "de": "de",  # German
                "it": "it",  # Italian
                "pt": "pt",  # Portuguese
                "zh": "zh",  # Chinese
                "ja": "ja",  # Japanese
                "ko": "ko",  # Korean
            }
            deepgram_language = language_mapping.get(language, "en-US")
            logger.info(f"🔤 Language mapping: '{language}' -> '{deepgram_language}'")
            
            logger.info("🔧 Configuring STT-LLM-TTS components:")
            logger.info("📊 STT (Deepgram):")
            logger.info(f"   - Model: nova-3")
            logger.info(f"   - Language: {deepgram_language}")
            logger.info(f"   - Sample rate: 48000 Hz")
            
            logger.info("🧠 LLM (OpenAI):")
            logger.info(f"   - Model: gpt-4o")
            logger.info(f"   - Temperature: 0.7")
            
            logger.info("🔊 TTS (Cartesia):")
            logger.info(f"   - Using default voice settings")
            
            session = AgentSession(
                vad=vad,
                stt=deepgram.STT(
                    model="nova-3",
                    language=deepgram_language,  # Use the mapped language code
                    sample_rate=48000  # Match WebRTC requirement
                ),
                llm=openai.LLM(
                    model="gpt-4o",  # Use full GPT-4 for better multilingual support
                    temperature=0.7
                ),
                tts=cartesia.TTS(),  # Use default voice
                turn_detection="vad"
            )
            logger.info("✅ STT-LLM-TTS pipeline configured successfully!")
        
        # Create and configure custom audio output with resampling
        logger.info("="*50)
        logger.info("🔊 AUDIO OUTPUT CONFIGURATION...")
        logger.info("="*50)
        logger.info("🎵 Creating ResamplingAudioOutput for 48kHz WebRTC compatibility")
        custom_audio_output = ResamplingAudioOutput(ctx.room)
        await custom_audio_output.start()
        logger.info("✅ Audio output started")
        
        # Override the session's audio output
        logger.info("🔧 Overriding session audio output with resampler")
        session.output._audio = custom_audio_output
        logger.info("✅ Custom audio output with 48kHz resampling configured")
        
        # Add event handlers for debugging with proper error handling
        logger.info("📋 REGISTERING EVENT HANDLERS...")
        
        @session.on("user_state_changed")
        def on_user_state_changed(event):
            try:
                # UserStateChangedEvent has old_state and new_state properties
                logger.info(f"👤 USER STATE CHANGED: {event.old_state} -> {event.new_state}")
            except AttributeError as e:
                logger.error(f"❌ User state event error: {e}")
                logger.info(f"👤 Raw user state event: {event}")
        
        @session.on("agent_state_changed")
        def on_agent_state_changed(event):
            try:
                # AgentStateChangedEvent has old_state and new_state properties
                logger.info(f"🤖 AGENT STATE CHANGED: {event.old_state} -> {event.new_state}")
            except AttributeError as e:
                logger.error(f"❌ Agent state event error: {e}")
                logger.info(f"🤖 Raw agent state event: {event}")
        
        @session.on("function_call")
        def on_function_call(event):
            try:
                # FunctionCallEvent has function_call_id and function_name
                logger.info(f"🔧 FUNCTION CALLED: {event.function_name} (ID: {event.function_call_id})")
            except AttributeError as e:
                logger.error(f"❌ Function call event error: {e}")
                logger.info(f"🔧 Raw function call event: {event}")
        
        # Add handler for transcription events
        @session.on("input_speech_transcription_completed")
        def on_speech_transcribed(event):
            logger.info(f"💬 USER SAID: '{getattr(event, 'text', 'unknown')}'")
            # Send to data channel for chat UI
            try:
                data = json.dumps({
                    "type": "transcription",
                    "speaker": "user", 
                    "text": getattr(event, 'text', '')
                }).encode('utf-8')
                asyncio.create_task(ctx.room.local_participant.publish_data(data, reliable=True))
            except Exception as e:
                logger.error(f"Error sending user transcription: {e}")
        
        # Add handler for agent speech
        @session.on("agent_speech_committed") 
        def on_agent_speech(event):
            logger.info(f"🗣️ Agent speaking: {getattr(event, 'text', 'unknown')}")
            # Send to data channel for chat UI
            try:
                data = json.dumps({
                    "type": "transcription", 
                    "speaker": "assistant",
                    "text": getattr(event, 'text', '')
                }).encode('utf-8')
                asyncio.create_task(ctx.room.local_participant.publish_data(data, reliable=True))
            except Exception as e:
                logger.error(f"Error sending agent transcription: {e}")
        
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
            logger.info(f"📝 METADATA CHANGED for {participant.identity}")
            logger.info(f"   - Previous: '{prev_metadata}'")
            logger.info(f"   - Current: '{participant.metadata}'")
            if participant.metadata:
                try:
                    metadata = json.loads(participant.metadata)
                    new_language = metadata.get("language")
                    if new_language and new_language != language:
                        logger.info(f"🌐 Language preference updated to: {new_language}")
                        logger.warning("⚠️  Cannot update STT language after initialization - user should reconnect")
                except Exception as e:
                    logger.error(f"❌ Error parsing participant metadata: {e}")
        
        # Handle audio track subscription (must be sync callback)
        @ctx.room.on("track_subscribed")
        def on_track_subscribed(
            track: rtc.Track, 
            publication: rtc.TrackPublication, 
            participant: rtc.RemoteParticipant
        ):
            logger.info(f"📡 TRACK SUBSCRIBED: {track.kind} from {participant.identity}")
            if track.kind == rtc.TrackKind.KIND_AUDIO:
                logger.info(f"🎤 Audio track detected - checking participant metadata...")
                # Check if participant has language preference
                if participant.metadata:
                    try:
                        metadata = json.loads(participant.metadata)
                        participant_lang = metadata.get("language", "en")
                        logger.info(f"   - Participant language preference: {participant_lang}")
                    except Exception as e:
                        logger.error(f"   ❌ Error parsing metadata: {e}")
                else:
                    logger.info(f"   - No metadata found for participant")
        
        # Start the session with the room
        logger.info("="*50)
        logger.info("🚀 STARTING AGENT SESSION...")
        logger.info("="*50)
        logger.info("🔧 Starting session with default configuration")
        logger.info("   Agent will handle participants joining/leaving automatically")
        await session.start(
            agent=agent, 
            room=ctx.room
        )
        
        # The agent will now handle participants joining
        logger.info(f"✅ Agent session started successfully!")
        logger.info(f"🏠 Room: {ctx.room.name}")
        logger.info(f"🌍 Language: {language}")
        
        # ADD THESE NEW EVENT HANDLERS for persistence (MUST BE SYNC!)
        # Now that session exists, handlers can access it via closure
        @ctx.room.on("participant_connected")
        def on_participant_connected(participant: rtc.RemoteParticipant):
            """Handle new and returning participants - SYNC callback"""
            logger.info(f"👤 Participant connected: {participant.identity}")
            
            # Check if this is a returning participant
            if participant.identity in PARTICIPANT_SESSIONS:
                # They're back!
                session_data = PARTICIPANT_SESSIONS[participant.identity]
                reconnect_count = session_data.get('reconnect_count', 0) + 1
                session_data['reconnect_count'] = reconnect_count
                session_data['last_seen'] = time.time()
                
                logger.info(f"♻️ Welcome back {participant.identity}! Reconnection #{reconnect_count}")
                
                # Welcome them back after a short delay
                if participant.identity not in greeted_participants:
                    greeted_participants.add(participant.identity)
                    
                    async def send_welcome_back():
                        await asyncio.sleep(1.5)  # Wait for audio to establish
                        
                        welcome_messages = {
                            "en": "Welcome back! I'm still here. How can I continue helping you with your flight search?",
                            "es": "¡Bienvenido de nuevo! Sigo aquí. ¿Cómo puedo seguir ayudándote con tu búsqueda de vuelos?",
                            "fr": "Bon retour! Je suis toujours là. Comment puis-je continuer à vous aider avec votre recherche de vol?",
                            "de": "Willkommen zurück! Ich bin immer noch hier. Wie kann ich Ihnen weiterhin bei Ihrer Flugsuche helfen?",
                            "it": "Bentornato! Sono ancora qui. Come posso continuare ad aiutarti con la ricerca del volo?",
                            "pt": "Bem-vindo de volta! Ainda estou aqui. Como posso continuar ajudando com sua busca de voos?",
                        }
                        
                        message = welcome_messages.get(language, welcome_messages["en"])
                        session.say(message, allow_interruptions=True)
                    
                    asyncio.create_task(send_welcome_back())
            else:
                # New participant
                PARTICIPANT_SESSIONS[participant.identity] = {
                    'joined_at': time.time(),
                    'last_seen': time.time(),
                    'reconnect_count': 0,
                    'language': language
                }
                
                # Send initial greeting only to first participant
                if len(greeted_participants) == 0 and participant.identity not in greeted_participants:
                    greeted_participants.add(participant.identity)
                    
                    async def send_greeting():
                        await asyncio.sleep(1.5)
                        
                        # Language-specific greetings
                        greetings = {
                            "en": "Hello! I'm your multilingual flight search assistant. How can I help you find flights today?",
                            "es": "¡Hola! Soy tu asistente multilingüe de búsqueda de vuelos. ¿Cómo puedo ayudarte a encontrar vuelos hoy?",
                            "fr": "Bonjour! Je suis votre assistant multilingue de recherche de vols. Comment puis-je vous aider à trouver des vols aujourd'hui?",
                            "de": "Hallo! Ich bin Ihr mehrsprachiger Flugsuche-Assistent. Wie kann ich Ihnen heute bei der Flugsuche helfen?",
                            "it": "Ciao! Sono il tuo assistente multilingue per la ricerca di voli. Come posso aiutarti a trovare voli oggi?",
                            "pt": "Olá! Sou seu assistente multilíngue de busca de voos. Como posso ajudá-lo a encontrar voos hoje?",
                        }
                        
                        greeting_message = greetings.get(language, greetings["en"])
                        session.say(greeting_message, allow_interruptions=True)
                    
                    asyncio.create_task(send_greeting())
        
        @ctx.room.on("participant_disconnected")
        def on_participant_disconnected(participant: rtc.RemoteParticipant):
            """Handle disconnections but keep session data - SYNC callback"""
            logger.info(f"👤 Participant disconnected: {participant.identity}")
            
            # Update last seen but DON'T delete the session
            if participant.identity in PARTICIPANT_SESSIONS:
                PARTICIPANT_SESSIONS[participant.identity]['last_seen'] = time.time()
                
                # Clean up after 5 minutes
                identity_to_clean = participant.identity
                
                async def cleanup_old_session():
                    await asyncio.sleep(300)  # 5 minutes
                    if identity_to_clean in PARTICIPANT_SESSIONS:
                        last_seen = PARTICIPANT_SESSIONS[identity_to_clean]['last_seen']
                        if time.time() - last_seen > 299:
                            logger.info(f"🗑️ Cleaning up old session for {identity_to_clean}")
                            del PARTICIPANT_SESSIONS[identity_to_clean]
                            greeted_participants.discard(identity_to_clean)
                
                asyncio.create_task(cleanup_old_session())
        
        # Check for existing participants and trigger the connection event
        logger.info("👥 Checking for existing participants...")
        for participant in ctx.room.remote_participants.values():
            logger.info(f"   - Found participant: {participant.identity}")
            on_participant_connected(participant)  # Call sync function directly
        
    except Exception as e:
        logger.error("="*60)
        logger.error(f"❌ CRITICAL ERROR IN AGENT ENTRYPOINT")
        logger.error(f"   Error type: {type(e).__name__}")
        logger.error(f"   Error message: {str(e)}")
        logger.error("="*60)
        logger.error(f"Full traceback:", exc_info=True)
        raise


async def handle_job_request(request):
    """Debug handler to see if jobs are being offered"""
    logger.info("="*60)
    logger.info(f"🎯 JOB REQUEST RECEIVED!")
    logger.info(f"🎯 Room: {request.room}")
    
    # Try to accept the job using the accept method
    try:
        logger.info("✅ Calling request.accept()")
        await request.accept()
        logger.info("✅ Job accepted successfully")
    except Exception as e:
        logger.error(f"❌ Error accepting job: {e}")
        # If accept() doesn't work, try returning True
        logger.info("🔄 Falling back to returning True")
        return True
    
    logger.info("="*60)


if __name__ == "__main__":
    # Debug: Create WorkerOptions and check for agent_name
    logger.info("="*60)
    logger.info("🔧 CREATING WORKER OPTIONS...")
    
    options = WorkerOptions(
        entrypoint_fnc=entrypoint,
        prewarm_fnc=prewarm,
        # request_fnc removed - let LiveKit handle job acceptance automatically
        port=8082,
        host="0.0.0.0",
        ws_url=os.getenv("LIVEKIT_URL", "wss://polyglot-rag-assistant-3l6xagej.livekit.cloud"),
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET"),
        num_idle_processes=1,
        # Just add these three lines for session persistence:
        shutdown_process_timeout=90.0,  # Wait longer before shutdown
        drain_timeout=120,  # 2 minutes to drain
        initialize_process_timeout=30.0,
    )
    
    # Check if agent_name exists and is not empty
    if hasattr(options, 'agent_name') and options.agent_name:
        logger.warning(f"⚠️  agent_name is set to: '{options.agent_name}'")
        logger.warning("⚠️  This will PREVENT automatic dispatch!")
    else:
        logger.info("✅ agent_name not set or empty (good for automatic dispatch)")
    
    # Log all attributes of options
    logger.info("📋 WorkerOptions attributes:")
    for attr in dir(options):
        if not attr.startswith('_'):
            try:
                value = getattr(options, attr)
                if value is not None:
                    logger.info(f"   - {attr}: {value}")
            except:
                pass
    
    logger.info("="*60)
    logger.info("🚀 STARTING AGENT...")
    
    # Run the agent with LiveKit CLI
    cli.run_app(options)