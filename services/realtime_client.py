"""OpenAI Realtime API WebSocket Client"""
import os
import json
import asyncio
import base64
from typing import Optional, AsyncGenerator, Dict, Any, Callable
import websockets
import logging
from openai import OpenAI
from .functions import REALTIME_FUNCTIONS
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.session_logging import setup_session_logging, get_session_logger

# Set up session logging
logger = setup_session_logging('realtime_client')

class RealtimeClient:
    """Client for OpenAI Realtime API with WebSocket support"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.ws_url = "wss://api.openai.com/v1/realtime"
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.session_id: Optional[str] = None
        self.is_connected = False
        
        # Default session configuration with proper VAD
        self.session_config = {
            "model": "gpt-4o-realtime-preview",
            "modalities": ["text", "audio"],
            "voice": "alloy",
            "turn_detection": {
                "type": "server_vad",
                "threshold": 0.5,  # Default LiveKit threshold
                "prefix_padding_ms": 300,  # LiveKit default
                "silence_duration_ms": 200,  # LiveKit default for faster interruption
                "create_response": True,  # Automatically create response when VAD detects end
                "interrupt_response": True  # Enable interruption of ongoing responses
            },
            "input_audio_transcription": {
                "model": "whisper-1",  # Enable real-time transcription
                # Don't specify language to allow auto-detection of any language
                # The model will detect Spanish, French, Chinese, etc. automatically
            },
            "tools": REALTIME_FUNCTIONS,
            "tool_choice": "auto",
            "temperature": 0.8,
            "instructions": """You are a multilingual flight search assistant.

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
- Internally translate city names to English for the search_flights function
- Example: "Buenos Aires" → "EZE", "Nueva York" → "JFK"
- But present results in the user's language

RESPONSE FORMAT:
- Be conversational in the user's language
- Format prices and times appropriately for their culture
- Use natural expressions from their language

IMPORTANT: If a user asks for a specific airline (like American Airlines) and you don't find it:
- Acknowledge in their language that you couldn't find that airline
- Mention the flight data might be limited
- Suggest checking the airline's website
- Show available alternatives"""
        }
        
        # Callbacks for handling events
        self.on_transcript: Optional[Callable] = None
        self.on_audio: Optional[Callable] = None
        self.on_function_call: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        
    async def connect(self):
        """Establish WebSocket connection to Realtime API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "OpenAI-Beta": "realtime=v1"
            }
            
            self.ws = await websockets.connect(
                f"{self.ws_url}?model=gpt-4o-realtime-preview",
                additional_headers=headers
            )
            self.is_connected = True
            logger.info("Connected to OpenAI Realtime API")
            
            # Send initial session configuration
            await self._send_session_update()
            
        except Exception as e:
            logger.error(f"Failed to connect to Realtime API: {e}")
            self.is_connected = False
            raise
    
    async def disconnect(self):
        """Close WebSocket connection"""
        if self.ws:
            await self.ws.close()
            self.is_connected = False
            logger.info("Disconnected from OpenAI Realtime API")
    
    async def _send_session_update(self):
        """Send session configuration to the API"""
        message = {
            "type": "session.update",
            "session": self.session_config
        }
        await self._send_message(message)
    
    async def _send_message(self, message: Dict[str, Any]):
        """Send a message through the WebSocket"""
        if not self.ws or not self.is_connected:
            raise ConnectionError("Not connected to Realtime API")
        
        await self.ws.send(json.dumps(message))
        logger.debug(f"Sent message: {message.get('type')}")
    
    async def send_audio(self, audio_data: bytes):
        """Send audio data to the API"""
        # Convert audio to base64
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        message = {
            "type": "input_audio_buffer.append",
            "audio": audio_base64
        }
        await self._send_message(message)
    
    async def commit_audio(self):
        """Commit the audio buffer for processing"""
        message = {"type": "input_audio_buffer.commit"}
        await self._send_message(message)
    
    async def send_text(self, text: str):
        """Send text input to the API"""
        message = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": text}]  # Fixed: use input_text
            }
        }
        await self._send_message(message)
        
        # Trigger response
        await self._send_message({"type": "response.create"})
    
    async def update_instructions(self, instructions: str):
        """Update the system instructions"""
        self.session_config["instructions"] = instructions
        await self._send_session_update()
    
    async def function_call_output(self, call_id: str, output: Any):
        """Send function call output back to the API"""
        message = {
            "type": "conversation.item.create",
            "item": {
                "type": "function_call_output",
                "call_id": call_id,
                "output": json.dumps(output) if not isinstance(output, str) else output
            }
        }
        await self._send_message(message)
        
        # Trigger response continuation
        await self._send_message({"type": "response.create"})
    
    async def process_events(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Process incoming events from the WebSocket"""
        if not self.ws or not self.is_connected:
            raise ConnectionError("Not connected to Realtime API")
        
        try:
            async for message in self.ws:
                event = json.loads(message)
                event_type = event.get("type")
                
                logger.debug(f"Received event: {event_type}")
                logger.debug(f"Full event: {json.dumps(event, indent=2)}")
                
                # Handle different event types
                if event_type == "session.created":
                    self.session_id = event["session"]["id"]
                    logger.info(f"Session created: {self.session_id}")
                
                elif event_type == "conversation.item.created":
                    # New conversation item added
                    item = event["item"]
                    if item["type"] == "message" and item["role"] == "assistant":
                        yield {"type": "assistant_message", "item": item}
                
                elif event_type == "response.audio_transcript.delta":
                    # Incremental transcript update from assistant
                    yield {
                        "type": "transcript_delta",
                        "delta": event["delta"],
                        "item_id": event["item_id"]
                    }
                
                elif event_type == "conversation.item.input_audio_transcription.completed":
                    # User's speech transcribed in real-time
                    yield {
                        "type": "user_transcript",
                        "text": event["transcript"],
                        "item_id": event["item_id"]
                    }
                
                elif event_type == "conversation.item.input_audio_transcription.delta":
                    # Real-time transcription of user's speech
                    yield {
                        "type": "user_transcript_delta",
                        "delta": event["delta"],
                        "item_id": event.get("item_id")
                    }
                
                elif event_type == "response.audio.delta":
                    # Audio data chunk
                    yield {
                        "type": "audio_delta",
                        "delta": event["delta"],
                        "item_id": event["item_id"]
                    }
                
                elif event_type == "response.function_call_arguments.done":
                    # Function call completed
                    yield {
                        "type": "function_call",
                        "call_id": event["call_id"],
                        "name": event["name"],
                        "arguments": json.loads(event["arguments"])
                    }
                
                elif event_type == "conversation.interrupted":
                    # User interrupted the assistant
                    logger.info("Conversation interrupted by user")
                    yield {"type": "interrupted", "item_id": event.get("item_id")}
                
                elif event_type == "input_audio_buffer.speech_started":
                    # User started speaking
                    logger.debug("User speech started")
                    yield {"type": "user_speech_started"}
                
                elif event_type == "input_audio_buffer.speech_stopped":
                    # User stopped speaking
                    logger.debug("User speech stopped")
                    yield {"type": "user_speech_stopped"}
                
                elif event_type == "error":
                    # Error occurred
                    error = event["error"]
                    logger.error(f"API Error: {error}")
                    yield {"type": "error", "error": error}
                
                elif event_type == "response.done":
                    # Response completed
                    yield {"type": "response_done", "response": event["response"]}
                
                # Call appropriate callbacks
                if self.on_transcript and event_type == "response.audio_transcript.delta":
                    await self.on_transcript(event["delta"])
                
                elif self.on_audio and event_type == "response.audio.delta":
                    await self.on_audio(event["delta"])
                
                elif self.on_function_call and event_type == "response.function_call_arguments.done":
                    await self.on_function_call(event["call_id"], event["name"], json.loads(event["arguments"]))
                
                elif self.on_error and event_type == "error":
                    await self.on_error(event["error"])
                
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")
            self.is_connected = False
        except Exception as e:
            logger.error(f"Error processing events: {e}")
            self.is_connected = False
            raise
    
    async def stream_conversation(
        self, 
        audio_stream: AsyncGenerator[bytes, None],
        language: str = "en"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream audio input and yield responses"""
        # Update instructions with language preference
        instructions = f"""You are a multilingual flight search assistant. 
        Current language: {language}. 
        Help users find flights using the search_flights function.
        Always respond in the same language as the user.
        Confirm critical details like dates and airports before searching."""
        
        await self.update_instructions(instructions)
        
        # Start processing events in background
        event_task = asyncio.create_task(self._event_processor())
        
        try:
            # Stream audio to API
            async for audio_chunk in audio_stream:
                await self.send_audio(audio_chunk)
                
                # Yield any accumulated events
                while not event_task.done():
                    await asyncio.sleep(0.01)
                    # Events are yielded through the event processor
            
            # Commit final audio
            await self.commit_audio()
            
            # Wait for final responses
            await asyncio.sleep(2)
            
        finally:
            event_task.cancel()
    
    async def _event_processor(self):
        """Background task to process events"""
        async for event in self.process_events():
            # This would be connected to the main stream
            # For now, just log
            logger.info(f"Event: {event['type']}")


# Utility function to check Realtime API availability
async def check_realtime_access(api_key: Optional[str] = None) -> bool:
    """Check if the account has access to Realtime API"""
    try:
        # Just check if we have an API key and the correct model access
        # Don't actually connect/disconnect during initialization
        if not api_key:
            return False
        
        # For now, assume if we have an API key, we have access
        # The actual check will happen on first use
        return True
    except Exception as e:
        logger.warning(f"Realtime API check failed: {e}")
        return False