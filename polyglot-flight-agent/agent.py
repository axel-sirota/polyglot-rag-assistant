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
import re

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

# Import language configuration
from language_config import get_deepgram_config, log_language_configuration, get_language_name, get_greeting, get_welcome_back_message

# Load environment variables
load_dotenv()

# Configure logging with more detail
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def strip_markdown(text: str) -> str:
    """Remove all markdown formatting from text for TTS"""
    # Remove bold/italic markers
    text = re.sub(r'\*+([^*]+)\*+', r'\1', text)
    # Remove headers
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    # Remove links [text](url)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Remove bare URLs
    text = re.sub(r'https?://[^\s]+', '', text)
    # Remove any remaining brackets
    text = text.replace('[', '').replace(']', '')
    # Remove code blocks
    text = re.sub(r'```[^```]+```', '', text, flags=re.DOTALL)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    return text.strip()

# Global dictionary to store session state outside of AgentSession
# This enables persistence across disconnections
PARTICIPANT_SESSIONS: Dict[str, Dict] = {}

# Global flag to track if we're waiting for text display confirmation
WAITING_FOR_TEXT_DISPLAY: Dict[str, bool] = {}


class SynchronizedSpeechController:
    """Controls text-audio synchronization for TTS playback"""
    
    def __init__(self, session: AgentSession, room: rtc.Room):
        self.session = session
        self.room = room
        self.pending_speeches = asyncio.Queue()
        self.text_display_confirmations = {}
        self.default_delay = 0.5  # Default delay before audio if no confirmation
        self.message_sequence = 0  # Track message sequence for ordering
        self.min_text_render_delay = 0.2  # Minimum 200ms for text to render
        self.interruptions_enabled = True  # Default to allowing interruptions
        self.last_synchronized_text = None  # Track last text sent via synchronized_say
        
    async def synchronized_say(self, text: str, allow_interruptions: bool = True) -> Any:
        """Send text first, then play audio with proper synchronization"""
        self.message_sequence += 1
        speech_id = f"speech_{self.message_sequence}_{time.time()}"
        
        # Track this text so we know it was sent via synchronized_say
        self.last_synchronized_text = text
        
        # Send text to data channel immediately with sequence number
        try:
            data = json.dumps({
                "type": "pre_speech_text",
                "speaker": "assistant",
                "text": text,
                "speech_id": speech_id,
                "sequence": self.message_sequence  # Add sequence for message ordering
            }).encode('utf-8')
            await self.room.local_participant.publish_data(data, reliable=True)
            logger.info(f"📤 Sent pre-speech text to data channel (ID: {speech_id}, seq: {self.message_sequence})")
        except Exception as e:
            logger.error(f"Error sending pre-speech text: {e}")
        
        # ALWAYS wait minimum time for text to render in UI
        await asyncio.sleep(self.min_text_render_delay)
        logger.info(f"⏱️ Waited {self.min_text_render_delay}s for text rendering")
        
        # Then wait for confirmation or additional timeout
        confirmation_received = False
        try:
            # Wait up to 300ms more for confirmation
            await asyncio.wait_for(
                self._wait_for_confirmation(speech_id),
                timeout=0.3
            )
            confirmation_received = True
            logger.info(f"✅ Text display confirmed for speech {speech_id}")
        except asyncio.TimeoutError:
            # No confirmation received, add safety delay
            logger.info(f"⏱️ No text display confirmation, adding {self.default_delay}s safety delay")
            await asyncio.sleep(self.default_delay)
        
        # Now generate and play TTS - text has definitely been displayed
        logger.info(f"🎵 Starting TTS playback for speech {speech_id} after total delay")
        # Override allow_interruptions based on user preference
        actual_allow_interruptions = allow_interruptions and self.interruptions_enabled
        logger.info(f"🤚 Interruptions: requested={allow_interruptions}, enabled={self.interruptions_enabled}, actual={actual_allow_interruptions}")
        handle = self.session.say(text, allow_interruptions=actual_allow_interruptions)
        return handle
    
    async def _wait_for_confirmation(self, speech_id: str):
        """Wait for text display confirmation from frontend"""
        while speech_id not in self.text_display_confirmations:
            await asyncio.sleep(0.05)
        return self.text_display_confirmations.pop(speech_id)
    
    def confirm_text_displayed(self, speech_id: str):
        """Mark text as displayed by frontend"""
        self.text_display_confirmations[speech_id] = True


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
    
    async def search_flights(self, origin: str, destination: str, date: str, preferred_airline: str = None, cabin_class: str = "economy", return_date: str = None) -> Dict[str, Any]:
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
            if return_date:
                params["return_date"] = return_date
                
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
    return_date: str | None = None,
    preferred_airline: str | None = None,
    cabin_class: str | None = "economy"
) -> Dict[str, Any]:
    """Search for available flights between cities.
    
    Args:
        origin: City name or airport code (e.g., 'New York' or 'JFK')
        destination: City name or airport code (e.g., 'Los Angeles' or 'LAX')
        departure_date: Date in YYYY-MM-DD format
        return_date: Optional return date in YYYY-MM-DD format for round trips
        preferred_airline: Specific airline requested by user (e.g., 'American Airlines', 'United', 'Delta')
        cabin_class: Class of service (economy, business, first)
    
    Returns:
        Flight search results with pricing and availability
    """
    trip_type = "roundtrip" if return_date else "oneway"
    logger.info(f"Searching {trip_type} flights: {origin} -> {destination} on {departure_date}" + 
                (f", returning {return_date}" if return_date else "") + 
                f", airline: {preferred_airline}, class: {cabin_class}")
    
    async with FlightAPIClient() as client:
        try:
            results = await client.search_flights(origin, destination, departure_date, preferred_airline, cabin_class, return_date)
            
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
                        # Handle cases where price is not a number
                        if price.lower() in ['check website', 'n/a', 'not available', '']:
                            return 999999.0
                        try:
                            return float(price)
                        except ValueError:
                            return 999999.0
                    return float(price)
                
                cheapest = min(flights, key=get_price)
                
                # Check if we found the preferred airline
                airline_found = False
                if preferred_airline:
                    airline_found = any(preferred_airline.lower() in flight.get('airline', '').lower() for flight in flights)
                
                # Separate nonstop and connecting flights
                nonstop_flights = [f for f in flights if f.get('stops', 0) == 0]
                connecting_flights = [f for f in flights if f.get('stops', 0) > 0]
                
                # Track airlines with unavailable prices
                airlines_without_prices = set()
                
                # Helper to format price for display
                def format_price(flight):
                    price = flight.get('price', '')
                    airline = flight.get('airline', '')
                    if isinstance(price, str):
                        price_lower = price.lower()
                        if price_lower in ['check website', 'n/a', 'not available', '']:
                            airlines_without_prices.add(airline)
                            return "price not available"
                    return price
                
                # Format response in human-friendly way
                response_parts = []
                
                if nonstop_flights:
                    response_parts.append("Non stop flights:")
                    for flight in nonstop_flights[:5]:
                        response_parts.append(
                            f"- Airline: {flight['airline']}, Price: {format_price(flight)}"
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
                            f"- Airline: {flight['airline']}, price: {format_price(flight)}, "
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
                
                # Add note about airlines without prices
                if airlines_without_prices:
                    airlines_list = list(airlines_without_prices)
                    if len(airlines_list) == 1:
                        final_message += f"\n\nNote: I couldn't fetch the price for {airlines_list[0]} flights. You may need to check their website directly."
                    else:
                        final_message += f"\n\nNote: I couldn't fetch prices for these airlines: {', '.join(airlines_list)}. You may need to check their websites directly."
                
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
    
    # Define VAD configurations for different environments
    vad_configs = {
        "quiet": {
            "min_speech_duration": 0.05,
            "min_silence_duration": 0.6,  # 600ms - shorter pauses ok in quiet
            "prefix_padding_duration": 0.4,
            "activation_threshold": 0.25,  # More sensitive in quiet
            "sample_rate": 16000,
            "force_cpu": True
        },
        "medium": {
            "min_speech_duration": 0.05,
            "min_silence_duration": 1.0,  # 1000ms - relaxed from 800ms to avoid interrupting greetings
            "prefix_padding_duration": 0.5,
            "activation_threshold": 0.35,  # Slightly less sensitive (was 0.3)
            "sample_rate": 16000,
            "force_cpu": True
        },
        "noisy": {
            "min_speech_duration": 0.05,
            "min_silence_duration": 1.2,  # 1200ms - relaxed from 1000ms for very noisy environments
            "prefix_padding_duration": 0.6,
            "activation_threshold": 0.45,  # Less sensitive (was 0.4)
            "sample_rate": 16000,
            "force_cpu": True
        }
    }
    
    # Store VAD configs for runtime switching
    proc.userdata["vad_configs"] = vad_configs
    
    # Load default VAD with medium settings
    logger.info("📊 Loading Silero VAD with MEDIUM (default) settings...")
    logger.info("   - min_speech_duration: 0.05s")
    logger.info("   - min_silence_duration: 1.0s (1000ms for natural pauses)")
    logger.info("   - activation_threshold: 0.35 (balanced sensitivity)")
    logger.info("   NOTE: Silero VAD only supports 8kHz and 16kHz")
    
    proc.userdata["vad"] = silero.VAD.load(**vad_configs["medium"])
    proc.userdata["current_environment"] = "medium"
    
    logger.info("✅ VAD loaded with adaptive configuration support")
    logger.info("🌍 Environments: quiet (600ms), medium (1000ms), noisy (1200ms)")
    
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
    
    # Log environment type
    livekit_url = os.getenv('LIVEKIT_URL', '')
    if 'polyglot-rag-dev' in livekit_url:
        logger.info("🟢 ENVIRONMENT: DEVELOPMENT (polyglot-rag-dev)")
        logger.info("🔒 Safe for testing - using dev LiveKit project")
    elif 'polyglot-rag-assistant' in livekit_url:
        logger.info("🔴 ENVIRONMENT: PRODUCTION (polyglot-rag-assistant)")
        logger.info("⚠️  Be careful - this is the production environment!")
    else:
        logger.info(f"🟡 ENVIRONMENT: UNKNOWN - LiveKit URL: {livekit_url}")
    
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

CRITICAL FORMATTING RULES FOR TEXT-TO-SPEECH:
- NEVER use ANY markdown formatting whatsoever
- NO asterisks (*) for bold or italics
- NO hashes (#) for headers
- NO brackets [] or parentheses () for links
- NO URLs or web addresses
- NO booking links
- Your responses will be SPOKEN ALOUD by TTS, so format as natural speech only

REQUIRED FLIGHT RESULT FORMAT:
When presenting flight results, you MUST use EXACTLY this format:

Non stop flights:
- Airline: American Airlines, Price: 450 dollars
- Airline: United, Price: 520 dollars

Flights with layover:
- Airline: Delta, Price: 380 dollars, Duration: 8 hours, stops: 1
- Airline: Southwest, Price: 295 dollars, Duration: 10 hours, stops: 2

DO NOT deviate from this format. DO NOT add any additional information like booking links, websites, or formatting.

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
            
            # Get proper Deepgram configuration for the language
            deepgram_config = get_deepgram_config(language)
            
            if not deepgram_config:
                # Language not supported - fallback to multilingual mode
                logger.warning(f"❌ Language '{language}' ({get_language_name(language)}) not supported by Deepgram")
                logger.warning(f"🔄 Falling back to multilingual mode")
                deepgram_config = {"model": "nova-3", "language": "multi"}
                
                # Update agent instructions to acknowledge the fallback
                logger.info("📝 Note: Agent will be informed about multilingual mode")
            
            # Log the language configuration details
            log_language_configuration(language, deepgram_config)
            
            logger.info("🔧 Configuring STT-LLM-TTS components:")
            logger.info("📊 STT (Deepgram):")
            logger.info(f"   - Model: {deepgram_config['model']}")
            logger.info(f"   - Language: {deepgram_config['language']}")
            logger.info(f"   - Sample rate: 48000 Hz")
            
            logger.info("🧠 LLM (OpenAI):")
            logger.info(f"   - Model: gpt-4o")
            logger.info(f"   - Temperature: 0.7")
            
            logger.info("🔊 TTS (Cartesia):")
            logger.info(f"   - Using default voice settings")
            
            session = AgentSession(
                vad=vad,
                stt=deepgram.STT(
                    model=deepgram_config["model"],
                    language=deepgram_config["language"],
                    sample_rate=48000,  # Match WebRTC requirement
                    detect_language=False  # CRITICAL: Prevent language nullification
                ),
                llm=openai.LLM(
                    model="gpt-4o",  # Use full GPT-4 for better multilingual support
                    temperature=0.7
                ),
                tts=cartesia.TTS(),  # Use default voice
                turn_detection="vad"
            )
            logger.info("✅ STT-LLM-TTS pipeline configured successfully!")
            
            # Debug: Log actual STT configuration
            if hasattr(session.stt, '_opts'):
                logger.info(f"🔍 Actual STT options after creation:")
                logger.info(f"   - model: {getattr(session.stt._opts, 'model', 'unknown')}")
                logger.info(f"   - language: {getattr(session.stt._opts, 'language', 'unknown')}")
                logger.info(f"   - detect_language: {getattr(session.stt._opts, 'detect_language', 'unknown')}")
        
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
                logger.info(f"📋 USER_STATE_CHANGED Event Structure:")
                logger.info(f"   - Type: {type(event)}")
                logger.info(f"   - Attributes: {[attr for attr in dir(event) if not attr.startswith('_')]}")
                logger.info(f"   - Old State: {event.old_state}")
                logger.info(f"   - New State: {event.new_state}")
            except AttributeError as e:
                logger.error(f"❌ User state event error: {e}")
                logger.info(f"👤 Raw user state event: {event}")
        
        @session.on("agent_state_changed")
        def on_agent_state_changed(event):
            try:
                # AgentStateChangedEvent has old_state and new_state properties
                logger.info(f"🤖 AGENT STATE CHANGED: {event.old_state} -> {event.new_state}")
                logger.info(f"📋 AGENT_STATE_CHANGED Event Structure:")
                logger.info(f"   - Type: {type(event)}")
                logger.info(f"   - Attributes: {[attr for attr in dir(event) if not attr.startswith('_')]}")
            except AttributeError as e:
                logger.error(f"❌ Agent state event error: {e}")
                logger.info(f"🤖 Raw agent state event: {event}")
        
        @session.on("function_call")
        def on_function_call(event):
            try:
                # FunctionCallEvent has function_call_id and function_name
                logger.info(f"🔧 FUNCTION CALLED: {event.function_name} (ID: {event.function_call_id})")
                logger.info(f"📋 FUNCTION_CALL Event Structure:")
                logger.info(f"   - Type: {type(event)}")
                logger.info(f"   - Attributes: {[attr for attr in dir(event) if not attr.startswith('_')]}")
                if hasattr(event, 'arguments'):
                    logger.info(f"   - Arguments: {event.arguments}")
            except AttributeError as e:
                logger.error(f"❌ Function call event error: {e}")
                logger.info(f"🔧 Raw function call event: {event}")
        
        # Enhanced event monitoring for debugging text injection
        @session.on("function_tools_executed")
        def on_function_tools_executed(event):
            """Monitor when tools are executed"""
            try:
                logger.info(f"🛠️ FUNCTION TOOLS EXECUTED")
                # Debug the event structure
                logger.info(f"   Event type: {type(event)}")
                logger.info(f"   Event attributes: {[attr for attr in dir(event) if not attr.startswith('_')]}")
                
                # Try different ways to access the data
                if hasattr(event, 'tool_calls'):
                    for tool_call in event.tool_calls:
                        logger.info(f"   - Tool: {tool_call.tool_name}")
                        logger.info(f"   - Result: {tool_call.result}")
                elif hasattr(event, 'called_functions'):
                    for call_info, result in event.called_functions:
                        logger.info(f"   - Tool: {call_info.name}")
                        logger.info(f"   - Result: {result}")
                else:
                    logger.info(f"   Raw event: {event}")
            except Exception as e:
                logger.error(f"❌ Error in function_tools_executed handler: {e}")
        
        # Add handler for user speech transcriptions (v1.0.23)
        @session.on("user_input_transcribed")
        def on_user_input_transcribed(event):
            if event.is_final:  # Only send final transcriptions
                logger.info(f"💬 USER SAID: '{event.transcript}'")
                # Send to data channel for chat UI
                try:
                    data = json.dumps({
                        "type": "transcription",
                        "speaker": "user", 
                        "text": event.transcript
                    }).encode('utf-8')
                    asyncio.create_task(ctx.room.local_participant.publish_data(data, reliable=True))
                    logger.info(f"✅ Sent user transcription to data channel")
                    
                    # OPTION 3: Send immediate "thinking" message for early text display
                    thinking_data = json.dumps({
                        "type": "thinking",
                        "speaker": "assistant",
                        "text": "Agent is thinking...",
                        "speech_id": f"thinking_{time.time()}"
                    }).encode('utf-8')
                    asyncio.create_task(ctx.room.local_participant.publish_data(thinking_data, reliable=True))
                    logger.info(f"💭 Sent thinking indicator to UI")
                except Exception as e:
                    logger.error(f"Error sending user transcription: {e}")
        
        # Add handler for conversation items (agent responses) - v1.0.23
        @session.on("conversation_item_added") 
        def on_conversation_item_added(event):
            logger.info(f"📋 CONVERSATION_ITEM_ADDED Event Structure:")
            logger.info(f"   - Type: {type(event)}")
            logger.info(f"   - Attributes: {[attr for attr in dir(event) if not attr.startswith('_')]}")
            logger.info(f"   - Item type: {type(event.item)}")
            logger.info(f"   - Item attributes: {[attr for attr in dir(event.item) if not attr.startswith('_')]}")
            logger.info(f"   - Item role: {event.item.role}")
            
            if event.item.role == "assistant":
                # Strip any markdown that might have slipped through
                clean_text = strip_markdown(event.item.text_content)
                logger.info(f"🗣️ Agent speaking: {clean_text}")
                
                # Log if markdown was detected and removed
                if clean_text != event.item.text_content:
                    logger.warning(f"⚠️ Markdown detected and removed from agent response")
                    logger.debug(f"Original: {event.item.text_content}")
                    logger.debug(f"Cleaned: {clean_text}")
                
                # Skip empty messages
                if not clean_text or clean_text.strip() == '':
                    logger.warning(f"⚠️ Skipping empty assistant message")
                    return
                
                # Check if this text was already sent via synchronized_say
                if hasattr(speech_controller, 'last_synchronized_text') and speech_controller.last_synchronized_text == clean_text:
                    logger.info(f"🔄 Text already sent via synchronized_say, skipping duplicate")
                    # Reset the tracking
                    speech_controller.last_synchronized_text = None
                else:
                    # OPTION 3: Send as pre_speech_text for immediate display
                    # This ensures text appears before TTS starts generating audio
                    try:
                        # For regular conversation_item_added, we don't need sequence numbering
                        # Only synchronized_say uses sequence numbers
                        
                        # Send as pre_speech_text for early display
                        data = json.dumps({
                            "type": "pre_speech_text",
                            "speaker": "assistant",
                            "text": clean_text,
                            "speech_id": f"response_{time.time()}",
                            "is_final": True  # This is the actual response
                        }).encode('utf-8')
                        asyncio.create_task(ctx.room.local_participant.publish_data(data, reliable=True))
                        logger.info(f"✅ Sent agent response as pre_speech_text for early display")
                    except Exception as e:
                        logger.error(f"Error sending agent response: {e}")
        
        
        # Add handler for speech creation (audio initialization)
        @session.on("speech_created")
        def on_speech_created(event):
            logger.info(f"🎵 Speech created - Audio channel active: {event}")
            logger.info(f"📋 SPEECH_CREATED Event Structure:")
            logger.info(f"   - Type: {type(event)}")
            logger.info(f"   - Attributes: {[attr for attr in dir(event) if not attr.startswith('_')]}")
            if hasattr(event, 'speech_handle'):
                handle = event.speech_handle
                logger.info(f"   - Speech Handle type: {type(handle)}")
                logger.info(f"   - Speech Handle attributes: {[attr for attr in dir(handle) if not attr.startswith('_')]}")
                
            # Send notification that speech is starting
            async def notify_speech_starting():
                try:
                    speech_id = f"speech_{time.time()}"
                    data = json.dumps({
                        "type": "speech_starting",
                        "speech_id": speech_id
                    }).encode('utf-8')
                    await ctx.room.local_participant.publish_data(data, reliable=True)
                    logger.info(f"📢 Notified frontend that speech is starting")
                except Exception as e:
                    logger.error(f"Error notifying speech start: {e}")
            
            asyncio.create_task(notify_speech_starting())
            
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
        
        # Create synchronized speech controller
        logger.info("🔄 Creating synchronized speech controller...")
        speech_controller = SynchronizedSpeechController(session, ctx.room)
        logger.info("✅ Speech controller initialized")
        
        # TEST: Send a test message immediately after session start
        logger.info("📨 Sending test data message...")
        try:
            test_data = json.dumps({
                "type": "transcription",
                "speaker": "system",
                "text": "Agent connected and ready to chat!"
            }).encode('utf-8')
            await ctx.room.local_participant.publish_data(test_data, reliable=True)
            logger.info("✅ Test data message sent successfully!")
        except Exception as e:
            logger.error(f"❌ Failed to send test data: {e}")
        
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
                        await asyncio.sleep(1.0)  # Wait for data channel to establish
                        
                        # Get language-specific welcome back message from comprehensive language config
                        message = get_welcome_back_message(language)
                        logger.info(f"🗣️ Sending welcome-back message in {language}: {message[:50]}...")
                        
                        # Use synchronized speech controller
                        await speech_controller.synchronized_say(message, allow_interruptions=True)
                        logger.info("✅ Welcome-back message sent with synchronization")
                    
                    asyncio.create_task(send_welcome_back())
                else:
                    logger.info(f"⚠️ Participant {participant.identity} already in greeted_participants, skipping welcome-back")
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
                        await asyncio.sleep(1.0)  # Wait for data channel to establish
                        
                        # Get language-specific greeting from comprehensive language config
                        greeting_message = get_greeting(language)
                        logger.info(f"🗣️ Sending greeting in {language}: {greeting_message[:50]}...")
                        
                        # Use synchronized speech controller
                        await speech_controller.synchronized_say(greeting_message, allow_interruptions=True)
                    
                    asyncio.create_task(send_greeting())
        
        @ctx.room.on("participant_disconnected")
        def on_participant_disconnected(participant: rtc.RemoteParticipant):
            """Handle disconnections but keep session data - SYNC callback"""
            logger.info(f"👤 Participant disconnected: {participant.identity}")
            
            # Remove from greeted_participants so they get welcomed back on reconnect
            greeted_participants.discard(participant.identity)
            
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
        
        # Test Harness for text injection testing
        class TestHarness:
            def __init__(self, session: AgentSession):
                self.session = session
                self.test_cases = []
                self.tools_executed = []
                
            async def add_test(self, input_text: str, expected_tool: str = None):
                """Add a test case with expected behavior"""
                self.test_cases.append({
                    "input": input_text,
                    "expected_tool": expected_tool
                })
            
            async def run_tests(self):
                """Execute all test cases"""
                logger.info("🧪 STARTING TEST HARNESS")
                logger.info(f"🧪 Running {len(self.test_cases)} tests")
                
                for i, test in enumerate(self.test_cases):
                    logger.info(f"\n🧪 Test {i+1}: {test['input']}")
                    
                    # Clear any existing state
                    self.session.interrupt()
                    await asyncio.sleep(0.5)
                    
                    # Reset tools tracking
                    self.tools_executed = []
                    
                    # Track tool executions
                    @self.session.on("function_tools_executed")
                    def track_tools(event):
                        for tool_call in event.tool_calls:
                            self.tools_executed.append(tool_call.tool_name)
                    
                    # Inject test input
                    speech_handle = await self.session.generate_reply(
                        user_input=test["input"]
                    )
                    
                    # Wait for completion
                    await speech_handle.wait_for_playout()
                    
                    # Verify expected behavior
                    if test["expected_tool"]:
                        if test["expected_tool"] in self.tools_executed:
                            logger.info(f"✅ Test passed - {test['expected_tool']} was called")
                        else:
                            logger.error(f"❌ Test failed - Expected {test['expected_tool']}, got {self.tools_executed}")
                    else:
                        logger.info(f"✅ Test completed - Tools executed: {self.tools_executed}")
                    
                    # Wait between tests
                    await asyncio.sleep(2.0)
                
                logger.info("\n🧪 TEST HARNESS COMPLETE")
        
        # Create test harness instance for this session
        test_harness = TestHarness(session)
        
        # Add data channel handler for test mode
        @ctx.room.on("data_received")
        def on_data_received(packet):
            """Handle text input for testing without microphone using session.generate_reply()
            
            This handler uses the official generate_reply() method to inject text directly
            into the STT-LLM-TTS pipeline, maintaining full conversation context and tool functionality.
            """
            # Log packet structure for documentation
            logger.info(f"📦 DATA_RECEIVED Packet Structure:")
            logger.info(f"   - Type: {type(packet)}")
            logger.info(f"   - Attributes: {[attr for attr in dir(packet) if not attr.startswith('_')]}")
            
            # Extract data and participant from the DataPacket object
            data = packet.data  # bytes containing the JSON payload
            participant = packet.participant  # RemoteParticipant who sent it
            
            logger.info(f"   - Data length: {len(data)} bytes")
            logger.info(f"   - Participant: {participant.identity if participant else 'None'}")
            if hasattr(packet, 'kind'):
                logger.info(f"   - Kind: {packet.kind}")
            if hasattr(packet, 'topic'):
                logger.info(f"   - Topic: {packet.topic}")
            
            try:
                message = json.loads(data.decode('utf-8'))
                
                # Handle config updates
                if message.get('type') == 'config_update':
                    if 'interruptions_enabled' in message:
                        if hasattr(ctx.room, 'speech_controller'):
                            ctx.room.speech_controller.interruptions_enabled = message['interruptions_enabled']
                            logger.info(f"🤚 Interruptions {'enabled' if message['interruptions_enabled'] else 'disabled'} by user")
                
                # Check if this is test input (not regular transcriptions)
                elif message.get('type') == 'test_user_input' and message.get('text'):
                    text = message['text']
                    participant_id = participant.identity if participant else "unknown"
                    logger.info(f"🧪 TEST INPUT received from {participant_id}: {text}")
                    
                    async def inject_text_input():
                        try:
                            logger.info(f"🧪 Using session.generate_reply() to inject text: {text}")
                            
                            # Interrupt any ongoing speech
                            session.interrupt()
                            
                            # Send transcription to data channel for UI display
                            try:
                                trans_data = json.dumps({
                                    "type": "transcription",
                                    "speaker": "user", 
                                    "text": text
                                }).encode('utf-8')
                                await ctx.room.local_participant.publish_data(trans_data, reliable=True)
                                logger.info("✅ Sent user transcription to data channel")
                            except Exception as e:
                                logger.error(f"Error sending transcription: {e}")
                            
                            # Inject text as if user spoke it using the official method
                            speech_handle = await session.generate_reply(
                                user_input=text,
                                allow_interruptions=True
                            )
                            
                            logger.info("🧪 Text injected into pipeline, waiting for completion...")
                            
                            # Wait for agent to complete response
                            await speech_handle.wait_for_playout()
                            
                            logger.info("🧪 Agent response completed")
                            
                        except Exception as e:
                            logger.error(f"❌ Error injecting text input: {e}")
                            # Fallback error message
                            session.say("I'm having trouble processing that request. Please try again.", 
                                       allow_interruptions=True)
                    
                    asyncio.create_task(inject_text_input())
                
                # Check for test harness commands
                elif message.get('type') == 'run_test_harness':
                    logger.info("🧪 Running automated test harness")
                    
                    async def run_automated_tests():
                        # Add test cases
                        await test_harness.add_test(
                            "Find flights from New York to London", 
                            expected_tool="search_flights"
                        )
                        await test_harness.add_test(
                            "What about morning flights only?",
                            expected_tool="search_flights"
                        )
                        await test_harness.add_test(
                            "Show me business class options",
                            expected_tool="search_flights"
                        )
                        
                        # Run all tests
                        await test_harness.run_tests()
                    
                    asyncio.create_task(run_automated_tests())
                
                # Handle text display confirmations from frontend
                elif message.get('type') == 'text_displayed' and message.get('speech_id'):
                    speech_id = message['speech_id']
                    logger.info(f"✅ Frontend confirmed text display for speech {speech_id}")
                    speech_controller.confirm_text_displayed(speech_id)
                
                # Handle environment updates from frontend
                elif message.get('type') == 'environment_update':
                    new_environment = message.get('environment', 'medium')
                    logger.info(f"🌍 ENVIRONMENT UPDATE: {new_environment}")
                    
                    # Get VAD configs from prewarm
                    vad_configs = ctx.proc.userdata.get("vad_configs", {})
                    
                    if new_environment in vad_configs:
                        # Reload VAD with new configuration
                        logger.info(f"🔄 Reloading VAD with {new_environment} settings...")
                        new_config = vad_configs[new_environment]
                        
                        # Log the new settings
                        logger.info(f"   - min_silence_duration: {new_config['min_silence_duration']}s")
                        logger.info(f"   - activation_threshold: {new_config['activation_threshold']}")
                        
                        # Create new VAD with updated settings
                        new_vad = silero.VAD.load(**new_config)
                        
                        # Update the VAD in the agent session
                        session._vad = new_vad
                        
                        # Store current environment
                        ctx.proc.userdata["current_environment"] = new_environment
                        
                        logger.info(f"✅ VAD updated to {new_environment} environment settings")
                        
                        # Send confirmation to chat only (no voice announcement)
                        confirmation_text = f"Voice detection adjusted for {new_environment} environment."
                        # Don't announce via voice - just send to chat
                        confirmation_data = json.dumps({
                            "type": "system_message",
                            "speaker": "system",
                            "text": confirmation_text,
                            "timestamp": datetime.now().isoformat()
                        }).encode('utf-8')
                        asyncio.create_task(ctx.room.local_participant.publish_data(
                            confirmation_data, 
                            reliable=True
                        ))
                    else:
                        logger.warning(f"⚠️ Unknown environment: {new_environment}")
                    
            except Exception as e:
                logger.debug(f"Data received (not test input): {e}")
        
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