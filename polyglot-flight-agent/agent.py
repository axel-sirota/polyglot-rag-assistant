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
    WorkerOptions, cli, function_tool
)
from livekit.plugins import openai, silero
import aiohttp
import asyncio

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
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


async def entrypoint(ctx: JobContext):
    """Main entry point for the LiveKit agent"""
    logger.info(f"Agent started for room {ctx.room.name}")
    
    # Connect to the room
    await ctx.connect()
    
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
    
    # Configure RealtimeModel with correct 2025 syntax
    session = AgentSession(
        llm=openai.realtime.RealtimeModel(
            voice="alloy",  # or "coral", "sage", etc.
            model="gpt-4o-realtime-preview-2024-12-17",
            temperature=0.8,
            tool_choice="auto"
        ),
        vad=silero.VAD.load()  # Voice activity detection
    )
    
    # Start the session immediately with the room
    await session.start(agent=agent, room=ctx.room)
    
    # The agent will now handle participants joining
    logger.info(f"Agent session started for room {ctx.room.name}")


if __name__ == "__main__":
    # Run the agent with LiveKit CLI
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint
        )
    )