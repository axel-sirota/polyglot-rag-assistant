#!/usr/bin/env python3
"""
LiveKit Agent for Polyglot RAG Flight Assistant
Uses OpenAI Realtime API for voice processing
"""
import os
import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli
from livekit.agents.realtime import RealtimeModel
from livekit.agents.turn_detector import MultilingualModel
from livekit.plugins import openai, silero
import aiohttp
import json

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class FlightSearchTool:
    """Flight search functionality for the agent"""
    
    def __init__(self):
        self.base_url = os.getenv("API_SERVER_URL", "http://localhost:8000")
    
    async def search_flights(self, origin: str, destination: str, departure_date: str) -> Dict[str, Any]:
        """Search for flights using our backend API"""
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "origin": origin,
                    "destination": destination,
                    "departure_date": departure_date
                }
                
                async with session.get(f"{self.base_url}/api/flights", params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Flight search failed: {response.status}")
                        return {"error": f"Flight search failed: {response.status}"}
                        
        except Exception as e:
            logger.error(f"Flight search error: {str(e)}")
            return {"error": str(e)}


async def entrypoint(ctx: JobContext):
    """Main entry point for the LiveKit agent"""
    logger.info(f"Agent started for room {ctx.room.name}")
    
    # Initialize flight search tool
    flight_tool = FlightSearchTool()
    
    # Configure the agent with OpenAI Realtime API
    initial_ctx = rtc.ChatContext().append(
        role="system",
        text="""You are a multilingual flight search assistant powered by LiveKit.

CRITICAL LANGUAGE RULES:
1. DETECT the language the user is speaking in (Spanish, English, French, Chinese, etc.)
2. ALWAYS respond in the EXACT SAME language the user used
3. If user speaks Spanish, respond ONLY in Spanish
4. If user speaks English, respond ONLY in English
5. Never mix languages in your response

LANGUAGE DETECTION:
- "buscar vuelos" or "quiero encontrar" = Spanish → Respond in Spanish
- "find flights" or "I want" = English → Respond in English
- "chercher des vols" = French → Respond in French
- And so on for all languages

FLIGHT SEARCH:
When users ask about flights, help them search using natural conversation.
Ask for any missing information (origin, destination, date) in their language.
Present results clearly in their language.

IMPORTANT: 
- Be conversational and natural
- If you don't find specific airlines, acknowledge it and show alternatives
- Format prices and times appropriately for their culture"""
    )
    
    # Connect to the room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    # Create the agent session with OpenAI Realtime
    assistant = agents.VoiceAssistant(
        model=RealtimeModel(
            # OpenAI Realtime configuration
            instructions=initial_ctx.messages[0].content,
            turn_detection=openai.realtime.TurnDetection(
                type="server_vad",
                threshold=0.5,
                prefix_padding_ms=300,
                silence_duration_ms=200,
                create_response=True
            ),
            modalities=["text", "audio"],
            voice="alloy"
        ),
        transcription=openai.STT(
            model="whisper-1",
            language=None  # Auto-detect language
        )
    )
    
    # Function to handle flight searches
    @assistant.function_call("search_flights")
    async def search_flights_handler(
        origin: str,
        destination: str, 
        departure_date: str
    ):
        """Search for flights between airports"""
        logger.info(f"Searching flights: {origin} -> {destination} on {departure_date}")
        
        # Call our backend API
        results = await flight_tool.search_flights(origin, destination, departure_date)
        
        if "error" in results:
            return f"I encountered an error searching for flights: {results['error']}"
        
        if not results.get("flights"):
            return "I couldn't find any flights for that route and date."
        
        # Format the results
        flights = results["flights"][:5]  # Show top 5 flights
        
        response = f"I found {len(results['flights'])} flights. Here are the best options:\n\n"
        
        for i, flight in enumerate(flights, 1):
            response += f"{i}. {flight['airline']} - ${flight['price']}\n"
            response += f"   Departure: {flight['departure_time']}\n"
            response += f"   Arrival: {flight['arrival_time']}\n"
            if flight.get('stops', 0) > 0:
                response += f"   Stops: {flight['stops']}\n"
            response += "\n"
        
        return response
    
    # Start the assistant
    assistant.start(ctx.room)
    
    # Handle participant events
    @ctx.room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant):
        logger.info(f"Participant connected: {participant.identity}")
    
    @ctx.room.on("participant_disconnected")
    def on_participant_disconnected(participant: rtc.RemoteParticipant):
        logger.info(f"Participant disconnected: {participant.identity}")
    
    # Keep the agent running
    try:
        await asyncio.Future()  # Run forever
    except asyncio.CancelledError:
        logger.info("Agent cancelled")
    finally:
        await assistant.aclose()
        logger.info("Agent stopped")


if __name__ == "__main__":
    # Run the agent
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            api_key=os.getenv("LIVEKIT_API_KEY"),
            api_secret=os.getenv("LIVEKIT_API_SECRET"),
            ws_url=os.getenv("LIVEKIT_URL", "wss://polyglot-rag.livekit.cloud"),
        )
    )