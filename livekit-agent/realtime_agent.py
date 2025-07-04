#!/usr/bin/env python3
"""
LiveKit Agent using OpenAI Realtime API
Production-ready implementation with proper interruption handling
"""
import os
import logging
from typing import Optional, Callable
from datetime import datetime

from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
    stt,
    tts,
    utils,
)
from livekit.plugins import openai
import aiohttp
import json

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


class FlightSearchFunction(llm.FunctionContext):
    """Flight search functionality for the agent"""
    
    def __init__(self):
        super().__init__()
        self.base_url = os.getenv("API_SERVER_URL", "http://localhost:8000")
    
    @llm.ai_callable(
        description="Search for flights between airports with real-time pricing and availability"
    )
    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        passengers: int = 1
    ):
        """
        Search for flights between airports.
        
        Args:
            origin: Origin airport IATA code or city name (e.g., 'JFK' or 'New York')
            destination: Destination airport IATA code or city name (e.g., 'LAX' or 'Los Angeles')  
            departure_date: Departure date in YYYY-MM-DD format
            return_date: Optional return date for round trip in YYYY-MM-DD format
            passengers: Number of passengers (default: 1)
        
        Returns:
            Flight search results with pricing and availability
        """
        logger.info(f"Searching flights: {origin} -> {destination} on {departure_date}")
        
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "origin": origin,
                    "destination": destination,
                    "departure_date": departure_date,
                    "passengers": passengers
                }
                
                if return_date:
                    params["return_date"] = return_date
                
                async with session.get(f"{self.base_url}/api/flights", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        flights = data.get("flights", [])
                        
                        if not flights:
                            return "I couldn't find any flights for that route and date. Would you like me to search for different dates?"
                        
                        # Format the results
                        result = f"I found {len(flights)} flights for you:\n\n"
                        
                        for i, flight in enumerate(flights[:5], 1):  # Show top 5
                            result += f"{i}. **{flight['airline']}** - ${flight['price']}\n"
                            result += f"   Departure: {flight['departure_time']}\n"
                            result += f"   Arrival: {flight['arrival_time']}\n"
                            if flight.get('stops', 0) > 0:
                                result += f"   Stops: {flight['stops']}\n"
                            result += "\n"
                        
                        if len(flights) > 5:
                            result += f"... and {len(flights) - 5} more flights available."
                        
                        return result
                    else:
                        logger.error(f"Flight search failed: {response.status}")
                        return "I'm having trouble searching for flights right now. Please try again in a moment."
                        
        except Exception as e:
            logger.error(f"Flight search error: {str(e)}")
            return f"I encountered an error while searching: {str(e)}"


async def entrypoint(ctx: JobContext):
    """Main entry point for the LiveKit agent"""
    logger.info(f"Agent started for room {ctx.room.name}")
    
    # Initial system instructions
    initial_ctx = llm.ChatContext().append(
        role="system",
        text="""You are a multilingual flight search assistant powered by LiveKit and OpenAI Realtime API.

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

INTERRUPTION HANDLING:
- If the user interrupts you, stop immediately and listen
- Be responsive to user input at all times"""
    )
    
    # Connect to the room with audio-only subscription
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    # Participant info for logging
    participant = await ctx.wait_for_participant()
    logger.info(f"Participant joined: {participant.identity}")
    
    # Create the assistant with OpenAI Realtime
    fnc_ctx = FlightSearchFunction()
    
    assistant = agents.VoiceAssistant(
        vad=openai.VAD(
            min_speech_duration=0.2,
            min_silence_duration=0.5,
            padding_duration=0.3,
            sample_rate=24000,
        ),
        stt=openai.STT(
            model="whisper-1",
            language=None,  # Auto-detect language
        ),
        llm=openai.LLM.with_realtime(
            model="gpt-4o-realtime-preview-2024-12-17",
            voice="alloy",
            temperature=0.8,
            instructions=initial_ctx.messages[0].content,
            turn_detection=openai.realtime.ServerVadOptions(
                threshold=0.5,
                prefix_padding_ms=300,
                silence_duration_ms=200,
            ),
        ),
        tts=openai.TTS(
            model="tts-1",
            voice="alloy",
        ),
        chat_ctx=initial_ctx,
        fnc_ctx=fnc_ctx,
        interrupt_min_words=1,  # Allow interruption after just 1 word
        allow_interruptions=True,
        preemptive_synthesis=False,  # Don't synthesize ahead
        transcription=agents.AssistantTranscriptionOptions(
            user_transcription=True,
            agent_transcription=True,
        ),
    )
    
    # Handle transcription updates for better UX
    @assistant.on("user_speech_committed")
    def on_user_speech_committed(msg: llm.ChatMessage):
        logger.info(f"User ({participant.identity}): {msg.content}")
    
    @assistant.on("agent_speech_committed")
    def on_agent_speech_committed(msg: llm.ChatMessage):
        logger.info(f"Assistant: {msg.content}")
    
    @assistant.on("function_calls_finished")
    def on_function_calls_finished(msg: llm.ChatMessage):
        logger.info(f"Function calls completed: {msg.tool_calls}")
    
    # Start the assistant
    assistant.start(ctx.room, participant)
    
    # Send initial greeting based on participant metadata or default to English
    initial_chat_ctx = assistant.chat_ctx.copy()
    initial_chat_ctx.append(
        role="assistant",
        text="Hello! I'm your multilingual flight assistant. How can I help you find flights today? You can speak in any language!"
    )
    await assistant.say(
        "Hello! I'm your multilingual flight assistant. How can I help you find flights today? You can speak in any language!",
        allow_interruptions=True
    )


if __name__ == "__main__":
    # Run the agent
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            api_key=os.getenv("LIVEKIT_API_KEY"),
            api_secret=os.getenv("LIVEKIT_API_SECRET"),
            ws_url=os.getenv("LIVEKIT_URL", "wss://polyglot-rag.livekit.cloud"),
            num_idle_processes=1,  # Keep 1 process ready
            shutdown_process_after_idle_timeout=60.0,  # Shutdown after 60s idle
            prewarm=True,  # Prewarm processes
        )
    )