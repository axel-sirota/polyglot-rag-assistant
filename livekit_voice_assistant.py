import asyncio
from livekit import agents, rtc
from livekit.agents import JobContext, WorkerOptions, cli, llm
from livekit.agents.voice import Agent as VoiceAgent
from livekit.plugins import openai, silero
from dotenv import load_dotenv
import logging
import json

load_dotenv()
logger = logging.getLogger("polyglot-assistant")
logger.setLevel(logging.INFO)

async def entrypoint(ctx: JobContext):
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            "You are a multilingual flight search assistant created by LiveKit. "
            "Your interface with users will be voice. "
            "You can help users search for flights in any language. "
            "Always respond in the same language the user speaks. "
            "Use short and concise responses suitable for voice interaction. "
            "When users ask about flights, use the search_flights function to find real flight data."
        )
    )

    await ctx.connect(auto_subscribe=agents.AutoSubscribe.AUDIO_ONLY)

    # Function context for flight search
    fnc_ctx = llm.FunctionContext()
    
    @fnc_ctx.ai_callable()
    async def search_flights(
        origin: str,
        destination: str, 
        departure_date: str,
        return_date: str = None,
        passengers: int = 1,
        cabin_class: str = "economy"
    ):
        """
        Search for flights between two locations.
        
        Args:
            origin: Departure city or airport code (e.g., 'New York' or 'JFK')
            destination: Arrival city or airport code (e.g., 'London' or 'LHR')
            departure_date: Date in YYYY-MM-DD format
            return_date: Optional return date for round trips
            passengers: Number of passengers (default 1)
            cabin_class: Class of service - economy, business, or first (default economy)
            
        Returns:
            Flight search results
        """
        logger.info(f"Searching flights: {origin} -> {destination} on {departure_date}")
        
        # Call our flight API
        import httpx
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "http://localhost:8765/search_flights",
                    json={
                        "origin": origin,
                        "destination": destination,
                        "departure_date": departure_date,
                        "return_date": return_date,
                        "passengers": passengers,
                        "cabin_class": cabin_class
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    flights = data.get("flights", [])
                    
                    if flights:
                        # Format response for voice
                        result = f"I found {len(flights)} flights from {origin} to {destination}. "
                        
                        # Describe top 3 options
                        for i, flight in enumerate(flights[:3], 1):
                            result += f"Option {i}: {flight.get('airline', 'Unknown')} "
                            result += f"flight {flight.get('flight_number', '')} "
                            result += f"at {flight.get('price', 'price unavailable')}. "
                        
                        return result
                    else:
                        return f"I couldn't find any flights from {origin} to {destination} on that date."
                else:
                    return "I'm having trouble searching for flights right now. Please try again."
                    
            except Exception as e:
                logger.error(f"Error searching flights: {e}")
                return "I encountered an error while searching for flights. Please try again."

    assistant = VoiceAgent(
        vad=silero.VAD.load(),
        stt=openai.STT(model="whisper-1"),
        llm=openai.LLM(model="gpt-4o"),
        tts=openai.TTS(model="tts-1", voice="alloy"),
        chat_ctx=initial_ctx,
        fnc_ctx=fnc_ctx,
    )

    assistant.start(ctx.room)

    # Greet the user
    await assistant.say(
        "Hello! I'm your multilingual flight search assistant. "
        "You can ask me about flights in any language. "
        "Just tell me where and when you'd like to travel!",
        allow_interruptions=True
    )


if __name__ == "__main__":
    cli.run_app(entrypoint)