#!/usr/bin/env python3
"""
LiveKit Agent for Polyglot Flight Search Assistant
Uses OpenAI Realtime API with correct 2025 patterns
"""
import os
import logging
from typing import Dict, Any
from datetime import datetime

from dotenv import load_dotenv
from livekit.agents import (
    Agent, AgentSession, JobContext, RunContext,
    WorkerOptions, cli, function_tool, JobProcess, AutoSubscribe
)
from livekit.plugins import openai, silero, deepgram, cartesia
from livekit import rtc
import aiohttp
import asyncio

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
                
                # Get cheapest flight
                cheapest = min(flights, key=lambda x: float(x.get('price', 999999)))
                
                # Format top 3 flights for voice response
                top_flights = []
                for i, flight in enumerate(flights[:3], 1):
                    top_flights.append(
                        f"Option {i}: {flight['airline']} for ${flight['price']}, "
                        f"departing at {flight['departure_time']}"
                    )
                
                return {
                    "status": "success",
                    "message": f"I found {flight_count} flights from {origin} to {destination}. "
                              f"The cheapest option is ${cheapest['price']} with {cheapest['airline']}. "
                              f"Here are the top options: " + " | ".join(top_flights),
                    "flights": flights[:5]  # Return top 5 for details
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
    proc.userdata["vad"] = silero.VAD.load(
        min_speech_duration=0.05,
        min_silence_duration=0.55,
        prefix_padding_duration=0.5,
        activation_threshold=0.5,
        sample_rate=16000,
        force_cpu=True  # Prevents GPU contention
    )
    
    logger.info("Models prewarmed successfully")


async def entrypoint(ctx: JobContext):
    """Main entry point for the LiveKit agent"""
    logger.info(f"Agent started for room {ctx.room.name}")
    
    try:
        # Connect to the room with AUDIO_ONLY to prevent video processing overhead
        logger.info("Connecting to room with AUDIO_ONLY subscription...")
        await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
        logger.info("Successfully connected to room")
        
        # Get preloaded VAD from prewarm
        vad = ctx.proc.userdata.get("vad")
        if not vad:
            logger.warning("VAD not preloaded, loading now...")
            vad = silero.VAD.load(force_cpu=True)
        
        # Initialize agent with flight booking instructions
        agent = Agent(
            instructions="""You are a multilingual flight booking assistant powered by LiveKit and Amadeus.

CRITICAL LANGUAGE RULES:
1. DETECT the language the user is speaking in (Spanish, English, French, Chinese, etc.)
2. ALWAYS respond in the EXACT SAME language the user used
3. If user speaks Spanish, respond ONLY in Spanish
4. If user speaks English, respond ONLY in English
5. Never mix languages in your response

LANGUAGE DETECTION:
- "buscar vuelos" or "quiero volar" = Spanish → Respond in Spanish
- "find flights" or "I want to fly" = English → Respond in English
- "chercher des vols" = French → Respond in French
- "查找航班" = Chinese → Respond in Chinese
- And so on for all languages

FLIGHT SEARCH:
- When users ask about flights, help them search using natural conversation
- Ask for any missing information (origin, destination, date) in their language
- Present results clearly and conversationally in their language
- Convert city names to appropriate format for search (e.g., "Nueva York" → "New York")

CONVERSATION STYLE:
- Be friendly, helpful, and conversational
- If you don't find specific airlines, acknowledge it and show alternatives
- Format prices and times appropriately for their culture
- Keep responses concise but informative

You can search for real flights using the search_flights function.
Always confirm important details like dates and destinations.""",
            tools=[search_flights]
        )
        
        # Configure session with multiple provider options for robustness
        logger.info("Initializing AgentSession with voice providers...")
        
        # Try OpenAI Realtime first, fallback to STT-LLM-TTS pipeline
        try:
            session = AgentSession(
                llm=openai.realtime.RealtimeModel(
                    voice="alloy",
                    model="gpt-4o-realtime-preview-2024-12-17",
                    temperature=0.8,
                    tool_choice="auto"
                ),
                vad=vad,
                turn_detection="vad"  # Critical for proper audio handling
            )
            logger.info("Using OpenAI Realtime model")
        except Exception as e:
            logger.warning(f"OpenAI Realtime failed, using STT-LLM-TTS pipeline: {e}")
            # Fallback to traditional pipeline
            session = AgentSession(
                vad=vad,
                stt=deepgram.STT(model="nova-3"),
                llm=openai.LLM(model="gpt-4o-mini"),
                tts=cartesia.TTS(),
                turn_detection="vad"
            )
        
        # Add event handlers for debugging
        @session.on("user_state_changed")
        def on_user_state_changed(event):
            logger.info(f"👤 User state changed: {event.state}")
        
        @session.on("agent_state_changed")
        def on_agent_state_changed(event):
            logger.info(f"🤖 Agent state changed: {event.state}")
        
        @session.on("function_call")
        def on_function_call(event):
            logger.info(f"🔧 Function called: {event.function_name}")
        
        # Handle audio track subscription
        @ctx.room.on("track_subscribed")
        async def on_track_subscribed(
            track: rtc.Track, 
            publication: rtc.TrackPublication, 
            participant: rtc.RemoteParticipant
        ):
            if track.kind == rtc.TrackKind.KIND_AUDIO:
                logger.info(f"🎤 Audio track subscribed from {participant.identity}")
                # The AgentSession will automatically handle the audio stream
        
        # Start the session with the room
        logger.info("Starting agent session...")
        await session.start(agent=agent, room=ctx.room)
        
        # The agent will now handle participants joining
        logger.info(f"✅ Agent session started successfully for room {ctx.room.name}")
        
    except Exception as e:
        logger.error(f"❌ Error in entrypoint: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    # Run the agent with LiveKit CLI
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm
        )
    )