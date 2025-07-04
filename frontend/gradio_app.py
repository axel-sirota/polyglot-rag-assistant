import gradio as gr
from livekit import api, rtc
import asyncio
import os
from dotenv import load_dotenv
import numpy as np
import json
from typing import Optional, List, Tuple
import logging
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import PolyglotRAGOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class PolyglotRAGInterface:
    def __init__(self):
        self.livekit_url = os.getenv("LIVEKIT_URL")
        self.api_key = os.getenv("LIVEKIT_API_KEY")
        self.api_secret = os.getenv("LIVEKIT_API_SECRET")
        
        # Initialize orchestrator
        self.orchestrator = PolyglotRAGOrchestrator()
        self.is_initialized = False
        
        # Room and track management
        self.room = None
        self.audio_track = None
        
    async def initialize(self):
        """Initialize the orchestrator and LiveKit connection"""
        if not self.is_initialized:
            await self.orchestrator.initialize()
            self.is_initialized = True
    
    async def connect_to_livekit(self):
        """Connect to LiveKit room"""
        try:
            # Generate access token
            token = api.AccessToken(self.api_key, self.api_secret)
            token.with_identity("gradio-user")
            token.with_name("Gradio User")
            token.with_grants(api.VideoGrants(
                room_join=True,
                room="polyglot-rag-demo",
                can_publish=True,
                can_subscribe=True
            ))
            
            # Create and connect to room
            self.room = rtc.Room()
            await self.room.connect(self.livekit_url, token.to_jwt())
            
            logger.info("Connected to LiveKit room")
            
        except Exception as e:
            logger.error(f"Error connecting to LiveKit: {e}")
    
    async def process_audio_stream(
        self, 
        audio_data: Optional[np.ndarray], 
        chat_history: List[Tuple[str, str]],
        detected_language: str
    ) -> Tuple[List[Tuple[str, str]], str, Optional[dict]]:
        """Process audio input and return updated chat, language, and flight results"""
        
        if audio_data is None:
            return chat_history, detected_language, None
        
        try:
            # Initialize if needed
            await self.initialize()
            
            # Process audio through orchestrator
            # For demo purposes, we'll simulate the voice processing
            # In production, this would go through LiveKit
            
            # Simulate voice-to-text (in production, this would be done by LiveKit)
            # For now, we'll use a placeholder
            user_message = "Find me flights from New York to London next Tuesday"
            
            # Process the query
            response = await self.orchestrator.process_text_query(
                user_message, 
                detected_language or "en"
            )
            
            # Update chat history
            new_history = chat_history + [(user_message, response)]
            
            # Extract flight results if any
            flight_results = None
            if hasattr(self.orchestrator, 'last_flight_results'):
                flight_results = self.orchestrator.last_flight_results
            
            return new_history, self.orchestrator.current_language, flight_results
            
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            error_msg = "Sorry, I encountered an error processing your request."
            return chat_history + [("Audio input", error_msg)], detected_language, None
    
    async def process_text_input(
        self,
        text_input: str,
        chat_history: List[Tuple[str, str]],
        detected_language: str
    ) -> Tuple[List[Tuple[str, str]], str, Optional[dict], str]:
        """Process text input and return updated chat, language, and flight results"""
        
        if not text_input.strip():
            return chat_history, detected_language, None, ""
        
        try:
            # Initialize if needed
            await self.initialize()
            
            # Process the query
            response = await self.orchestrator.process_text_query(
                text_input,
                detected_language or "en"
            )
            
            # Update chat history
            new_history = chat_history + [(text_input, response)]
            
            # Extract flight results if any
            flight_results = None
            if self.orchestrator._is_flight_query(text_input):
                # Get the last flight results from the orchestrator
                if hasattr(self.orchestrator.flight_agent, 'graph'):
                    result = await self.orchestrator.flight_agent.process_query(text_input, detected_language)
                    if not result["needs_clarification"] and result["flight_results"]:
                        flight_results = result["flight_results"]
            
            return new_history, self.orchestrator.current_language, flight_results, ""
            
        except Exception as e:
            logger.error(f"Error processing text: {e}")
            error_msg = "Sorry, I encountered an error processing your request."
            return chat_history + [(text_input, error_msg)], detected_language, None, ""
    
    def format_flight_results(self, flights: List[dict]) -> str:
        """Format flight results for display"""
        if not flights:
            return "No flights found"
        
        formatted = "### 🛫 Flight Search Results\n\n"
        
        for i, flight in enumerate(flights[:5], 1):  # Show top 5
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
            title="🌍 Polyglot RAG Assistant",
            theme=gr.themes.Soft(),
            css="""
            .gradio-container {
                max-width: 1200px;
                margin: auto;
            }
            #chatbot {
                height: 500px;
            }
            #flight-results {
                max-height: 400px;
                overflow-y: auto;
            }
            """
        ) as demo:
            gr.Markdown("""
            # 🌍 Polyglot RAG: Multilingual Flight Assistant
            
            Powered by **LiveKit** + **OpenAI** + **Anthropic Claude**
            
            Speak or type in any language to search for flights!
            """)
            
            with gr.Row():
                with gr.Column(scale=2):
                    chatbot = gr.Chatbot(
                        height=400,
                        elem_id="chatbot",
                        avatar_images=(None, "🤖")
                    )
                    
                    with gr.Row():
                        with gr.Column(scale=4):
                            text_input = gr.Textbox(
                                placeholder="Type your message here... (any language)",
                                lines=1,
                                max_lines=3,
                                elem_id="text-input"
                            )
                        with gr.Column(scale=1):
                            send_btn = gr.Button("Send", variant="primary")
                    
                    with gr.Row():
                        audio_input = gr.Audio(
                            sources=["microphone"],
                            type="numpy",
                            label="🎤 Click to speak (or use push-to-talk)"
                        )
                
                with gr.Column(scale=1):
                    gr.Markdown("### 🌐 Detected Language")
                    language_display = gr.Textbox(
                        value="English",
                        interactive=False,
                        elem_id="language-display"
                    )
                    
                    gr.Markdown("### ✈️ Flight Results")
                    flight_results_display = gr.Markdown(
                        value="*No flight search performed yet*",
                        elem_id="flight-results"
                    )
                    
                    with gr.Accordion("📋 Example Queries", open=False):
                        gr.Markdown("""
                        **English:**
                        - "Find flights from NYC to London next week"
                        - "I need a round trip to Paris in December"
                        
                        **Spanish:**
                        - "Busca vuelos de Madrid a Nueva York"
                        - "Necesito un vuelo a Barcelona mañana"
                        
                        **French:**
                        - "Trouve-moi un vol Paris-Tokyo"
                        - "Je veux aller à Rome la semaine prochaine"
                        
                        **German:**
                        - "Flüge von Berlin nach New York"
                        - "Ich brauche einen Flug nach München"
                        
                        **Japanese:**
                        - "東京からニューヨークへのフライトを探して"
                        - "来週パリに行きたい"
                        """)
            
            # State management
            detected_language = gr.State("en")
            flight_results_json = gr.State(None)
            
            # Event handlers
            async def handle_text_submit(text, history, lang):
                result = await self.process_text_input(text, history, lang)
                history, new_lang, flights, _ = result
                
                # Format flight results for display
                flight_display = "*No flights to display*"
                if flights:
                    flight_display = self.format_flight_results(flights)
                
                return history, new_lang, flights, flight_display, ""
            
            async def handle_audio_input(audio, history, lang):
                if audio is None:
                    return history, lang, None, "*No flights to display*"
                
                result = await self.process_audio_stream(audio, history, lang)
                history, new_lang, flights = result
                
                # Format flight results for display
                flight_display = "*No flights to display*"
                if flights:
                    flight_display = self.format_flight_results(flights)
                
                return history, new_lang, flights, flight_display
            
            # Wire up events
            text_input.submit(
                handle_text_submit,
                inputs=[text_input, chatbot, detected_language],
                outputs=[chatbot, detected_language, flight_results_json, flight_results_display, text_input]
            )
            
            send_btn.click(
                handle_text_submit,
                inputs=[text_input, chatbot, detected_language],
                outputs=[chatbot, detected_language, flight_results_json, flight_results_display, text_input]
            )
            
            audio_input.change(
                handle_audio_input,
                inputs=[audio_input, chatbot, detected_language],
                outputs=[chatbot, detected_language, flight_results_json, flight_results_display]
            )
            
            # Add footer
            gr.Markdown("""
            ---
            **Note:** This is a demo version. Voice processing requires LiveKit connection.
            For production use, deploy with proper LiveKit cloud configuration.
            """)
        
        return demo

def main():
    """Main entry point for Gradio app"""
    interface = PolyglotRAGInterface()
    demo = interface.create_interface()
    
    # Launch the app
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,  # Create public URL for demo
        show_api=False
    )

if __name__ == "__main__":
    # Run with asyncio support
    import nest_asyncio
    nest_asyncio.apply()
    
    main()