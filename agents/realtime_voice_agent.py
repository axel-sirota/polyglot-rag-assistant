"""
LiveKit Agent using OpenAI Realtime API for voice conversations
Based on: https://docs.livekit.io/agents/plugins/openai/
"""
import json
import logging
import os
import sys
from typing import Dict, Any, Optional

from livekit import agents, rtc
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import openai

from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logging_config import setup_logging
from services.flight_api import FlightAPIWrapper

load_dotenv()
logger = setup_logging('realtime_voice_agent')

# Flight search tool definition for OpenAI
flight_search_tool = {
    "type": "function",
    "function": {
        "name": "search_flights",
        "description": "Search for flights between two locations",
        "parameters": {
            "type": "object",
            "properties": {
                "origin": {
                    "type": "string",
                    "description": "Departure city or airport code (e.g., 'New York' or 'JFK')"
                },
                "destination": {
                    "type": "string",
                    "description": "Arrival city or airport code (e.g., 'London' or 'LHR')"
                },
                "departure_date": {
                    "type": "string",
                    "description": "Departure date in YYYY-MM-DD format"
                },
                "return_date": {
                    "type": "string",
                    "description": "Return date in YYYY-MM-DD format (optional for one-way)"
                },
                "passengers": {
                    "type": "integer",
                    "description": "Number of passengers",
                    "default": 1
                },
                "cabin_class": {
                    "type": "string",
                    "description": "Cabin class: economy, business, or first",
                    "default": "economy"
                }
            },
            "required": ["origin", "destination", "departure_date"]
        }
    }
}

class RealtimeVoiceAgent:
    """Voice agent using OpenAI Realtime API"""
    
    def __init__(self):
        self.flight_api = FlightAPIWrapper()
        
    async def initialize(self):
        """Initialize services"""
        await self.flight_api.initialize()
        logger.info("RealtimeVoiceAgent initialized")
    
    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        passengers: int = 1,
        cabin_class: str = "economy"
    ) -> Dict[str, Any]:
        """Search for flights using the Flight API"""
        try:
            logger.info(f"Searching flights: {origin} -> {destination} on {departure_date}")
            
            flights = await self.flight_api.search_flights(
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                return_date=return_date,
                passengers=passengers,
                cabin_class=cabin_class,
                currency="USD"
            )
            
            if flights:
                logger.info(f"Found {len(flights)} flights")
                # Format for voice response
                summary = f"I found {len(flights)} flights from {origin} to {destination}. "
                
                # Describe top 3 options
                for i, flight in enumerate(flights[:3], 1):
                    summary += f"Option {i}: {flight.get('airline', 'Unknown')} "
                    summary += f"flight {flight.get('flight_number', '')} "
                    summary += f"departing at {flight.get('departure_time', 'unknown time')} "
                    summary += f"for {flight.get('price', 'price unavailable')}. "
                
                return {
                    "success": True,
                    "count": len(flights),
                    "flights": flights,
                    "summary": summary
                }
            else:
                return {
                    "success": False,
                    "message": "No flights found for the specified route and date.",
                    "flights": []
                }
                
        except Exception as e:
            logger.error(f"Error searching flights: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "I encountered an error while searching for flights. Please try again."
            }

async def entrypoint(ctx: JobContext):
    """Main entry point for the LiveKit agent"""
    await ctx.connect()
    logger.info(f"Room name: {ctx.room.name}")
    
    # Initialize our custom agent
    custom_agent = RealtimeVoiceAgent()
    await custom_agent.initialize()
    
    # Create the voice pipeline agent with OpenAI Realtime
    initial_ctx = agents.llm.ChatContext().append(
        role="system",
        text=(
            "You are a helpful multilingual travel assistant specializing in flight search. "
            "You can search for flights in real-time and speak multiple languages fluently. "
            "When users ask about flights, use the search_flights function to find real flight data. "
            "Always provide helpful travel tips and suggestions. "
            "Respond in the same language the user speaks to you."
        ),
    )
    
    # Configure OpenAI Realtime model
    model = openai.realtime.RealtimeModel(
        instructions=(
            "You are a helpful multilingual travel assistant. "
            "Respond in the same language the user speaks. "
            "When searching for flights, always confirm the details before searching. "
            "Provide concise but informative responses about flight options."
        ),
        voice="alloy",
        temperature=0.7,
        # Enable function calling
        tools=[flight_search_tool],
        turn_detection=openai.realtime.ServerVadOptions(
            threshold=0.5,
            prefix_padding_ms=300,
            silence_duration_ms=500
        ),
    )
    
    assistant = VoicePipelineAgent(
        chat_ctx=initial_ctx,
        llm=model,
        allow_interruptions=True,
        interrupt_speech_duration=0.5,
    )
    
    # Handle function calls
    @assistant.on("function_calls_collected")
    async def on_function_calls(function_calls):
        """Handle function calls from the model"""
        for call in function_calls:
            if call.name == "search_flights":
                args = json.loads(call.arguments)
                logger.info(f"Executing flight search with args: {args}")
                
                # Call our flight search
                result = await custom_agent.search_flights(**args)
                
                # Return the result to the model
                await call.add_result(json.dumps(result))
    
    # Start the agent
    assistant.start(ctx.room)
    
    # Handle participant events
    @ctx.room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant):
        logger.info(f"Participant connected: {participant.identity}")
    
    # Initial greeting when someone joins
    await assistant.say(
        "Hello! I'm your multilingual flight search assistant. "
        "You can ask me about flights in any language. "
        "Just tell me where and when you'd like to travel!",
        allow_interruptions=True
    )

if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            log_level="info",
            name="polyglot-rag-realtime",
        ),
    )