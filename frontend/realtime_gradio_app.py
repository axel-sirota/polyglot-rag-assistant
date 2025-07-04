"""
Gradio interface for OpenAI Realtime Voice conversations
"""
import gradio as gr
import os
import json
import asyncio
import logging
import sys
from typing import List, Tuple, Optional, Dict
from dotenv import load_dotenv
import openai
from openai import OpenAI
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logging_config import setup_logging, configure_root_logger, suppress_noisy_loggers
from services.flight_api import FlightAPIWrapper

# Configure logging
configure_root_logger()
suppress_noisy_loggers()
logger = setup_logging('realtime_gradio')

load_dotenv()

class RealtimeGradioInterface:
    def __init__(self):
        self.client = OpenAI()
        self.flight_api = FlightAPIWrapper()
        self.conversation_history = []
        
    async def initialize(self):
        """Initialize services"""
        await self.flight_api.initialize()
        logger.info("RealtimeGradioInterface initialized")
    
    async def process_voice_query(
        self,
        audio_input: Optional[np.ndarray],
        chat_history: List[Tuple[str, str]]
    ) -> Tuple[List[Tuple[str, str]], Optional[str], Optional[Dict]]:
        """Process voice input using OpenAI Realtime-like approach"""
        
        if audio_input is None:
            return chat_history, None, None
        
        try:
            # For now, use standard Whisper + GPT-4 + TTS pipeline
            # (True Realtime API requires WebRTC which Gradio doesn't support directly)
            
            # 1. Speech to Text
            import io
            import soundfile as sf
            
            sample_rate = 16000
            audio_buffer = io.BytesIO()
            sf.write(audio_buffer, audio_input, sample_rate, format='WAV')
            audio_buffer.seek(0)
            audio_buffer.name = "audio.wav"
            
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_buffer,
                response_format="verbose_json"
            )
            
            user_message = transcript.text
            detected_language = transcript.language
            
            logger.info(f"Transcribed: {user_message} (language: {detected_language})")
            
            # 2. Process with GPT-4 and flight search
            response_text, flight_results = await self.process_query_with_tools(
                user_message, 
                detected_language
            )
            
            # 3. Text to Speech
            tts_response = self.client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=response_text
            )
            
            # Update chat history
            new_history = chat_history + [(user_message, response_text)]
            
            # Format audio for Gradio
            audio_data = np.frombuffer(tts_response.content, dtype=np.int16)
            audio_response = (24000, audio_data)
            
            return new_history, audio_response, flight_results
            
        except Exception as e:
            logger.error(f"Error processing voice: {e}")
            import traceback
            traceback.print_exc()
            error_msg = "Sorry, I encountered an error. Please try again."
            return chat_history + [("Audio input", error_msg)], None, None
    
    async def process_query_with_tools(
        self, 
        query: str, 
        language: str = "en"
    ) -> Tuple[str, Optional[List[Dict]]]:
        """Process query with GPT-4 and flight search tools"""
        
        # System prompt based on language
        system_prompts = {
            "en": "You are a helpful multilingual travel assistant specializing in flight search.",
            "es": "Eres un asistente de viaje multilingüe especializado en búsqueda de vuelos.",
            "fr": "Vous êtes un assistant de voyage multilingue spécialisé dans la recherche de vols.",
            "de": "Sie sind ein mehrsprachiger Reiseassistent, spezialisiert auf Flugsuche.",
            "zh": "您是一位专门从事航班搜索的多语言旅行助手。"
        }
        
        system_prompt = system_prompts.get(language, system_prompts["en"])
        system_prompt += f" Always respond in {language}. When users ask about flights, search for real flight data."
        
        # Define flight search tool
        tools = [{
            "type": "function",
            "function": {
                "name": "search_flights",
                "description": "Search for flights between two locations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "origin": {"type": "string", "description": "Departure city or airport"},
                        "destination": {"type": "string", "description": "Arrival city or airport"},
                        "departure_date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                        "return_date": {"type": "string", "description": "Return date (optional)"},
                        "passengers": {"type": "integer", "default": 1},
                        "cabin_class": {"type": "string", "default": "economy"}
                    },
                    "required": ["origin", "destination", "departure_date"]
                }
            }
        }]
        
        # Call GPT-4 with tools
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.7
        )
        
        message = response.choices[0].message
        flight_results = None
        
        # Check if the model wants to call a function
        if message.tool_calls:
            for tool_call in message.tool_calls:
                if tool_call.function.name == "search_flights":
                    # Parse arguments
                    args = json.loads(tool_call.function.arguments)
                    logger.info(f"Searching flights with args: {args}")
                    
                    # Search flights
                    flights = await self.flight_api.search_flights(**args)
                    flight_results = flights
                    
                    # Add function result to conversation
                    messages.append(message)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps({
                            "count": len(flights),
                            "flights": flights[:5]  # Limit for context
                        })
                    })
                    
                    # Get final response
                    final_response = self.client.chat.completions.create(
                        model="gpt-4o",
                        messages=messages,
                        temperature=0.7
                    )
                    
                    return final_response.choices[0].message.content, flight_results
        
        # No function call needed
        return message.content, None
    
    def format_flight_results(self, flights: List[dict]) -> str:
        """Format flight results for display"""
        if not flights:
            return "No flights found"
        
        formatted = "### ✈️ Flight Search Results\n\n"
        
        for i, flight in enumerate(flights[:5], 1):
            formatted += f"""**Option {i}: {flight.get('airline', 'Unknown')} - {flight.get('flight_number', 'N/A')}**
- 🕐 Departure: {flight.get('departure_time', 'N/A')}
- 🕐 Arrival: {flight.get('arrival_time', 'N/A')}
- ⏱️ Duration: {flight.get('duration', 'N/A')}
- 💰 Price: {flight.get('price', 'N/A')}
- 🔄 Stops: {flight.get('stops', 0)}
---
"""
        
        return formatted
    
    def create_interface(self):
        """Create the Gradio interface"""
        with gr.Blocks(
            title="🎙️ Polyglot Voice Assistant",
            theme=gr.themes.Soft(),
            css="""
            .gradio-container {
                max-width: 1200px;
                margin: auto;
            }
            #chatbot {
                height: 500px;
            }
            """
        ) as demo:
            gr.Markdown("""
            # 🎙️ Polyglot Voice Assistant (OpenAI Realtime-style)
            
            Speak in any language to search for flights using voice!
            """)
            
            with gr.Row():
                with gr.Column(scale=2):
                    chatbot = gr.Chatbot(
                        height=400,
                        elem_id="chatbot",
                        avatar_images=(None, "🎙️"),
                        type="tuples"
                    )
                    
                    audio_input = gr.Audio(
                        sources=["microphone"],
                        type="numpy",
                        label="🎤 Click and speak your request",
                        streaming=False
                    )
                    
                    audio_output = gr.Audio(
                        label="🔊 Assistant Response",
                        type="numpy",
                        autoplay=True
                    )
                
                with gr.Column(scale=1):
                    gr.Markdown("### ✈️ Flight Results")
                    flight_display = gr.Markdown(
                        value="*No flights searched yet*"
                    )
                    
                    with gr.Accordion("💡 Example Queries", open=True):
                        gr.Markdown("""
                        Try saying:
                        - "Find flights from New York to London next Monday"
                        - "Busca vuelos de Madrid a Barcelona mañana"
                        - "Trouve-moi un vol Paris-Tokyo en décembre"
                        - "我想查询北京到上海的航班"
                        """)
            
            # Handle audio input
            async def handle_audio(audio, history):
                if audio is None:
                    return history, None, "*No flights searched yet*"
                
                new_history, audio_response, flights = await self.process_voice_query(
                    audio, history
                )
                
                # Format flight display
                flight_text = "*No flights found*"
                if flights:
                    flight_text = self.format_flight_results(flights)
                
                return new_history, audio_response, flight_text
            
            audio_input.change(
                handle_audio,
                inputs=[audio_input, chatbot],
                outputs=[chatbot, audio_output, flight_display]
            )
            
            # Add a clear button
            clear_btn = gr.Button("Clear Conversation")
            clear_btn.click(
                lambda: ([], None, "*No flights searched yet*"),
                outputs=[chatbot, audio_output, flight_display]
            )
        
        return demo

# Initialize and launch
if __name__ == "__main__":
    interface = RealtimeGradioInterface()
    
    # Initialize in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(interface.initialize())
    
    demo = interface.create_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True  # Create public URL
    )