"""Voice processing pipeline with Realtime API and standard fallback"""
import os
import json
import asyncio
import logging
from typing import AsyncGenerator, Optional, Dict, Any, Tuple
from openai import OpenAI, AsyncOpenAI
import base64
from .realtime_client import RealtimeClient, check_realtime_access
from .functions import ALL_FUNCTIONS
from .flight_search_service import FlightSearchServer
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.session_logging import setup_session_logging

logger = setup_session_logging('voice_processor')

class VoiceProcessor:
    """Main voice processing pipeline with Realtime API and fallback support"""
    
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.client = AsyncOpenAI(api_key=self.openai_key)
        self.sync_client = OpenAI(api_key=self.openai_key)
        
        # Check Realtime API availability on init
        self.realtime_available = False
        self.realtime_client: Optional[RealtimeClient] = None
        
        # Flight search service
        self.flight_service = FlightSearchServer()
        
        # Conversation memory (per session)
        self.conversation_history = []
        self.max_history = 10  # Keep last 10 exchanges
        
        # Event queue for continuous mode
        self.event_queue = None
        
        # Language detection settings
        self.supported_languages = {
            'en': 'English',
            'es': 'Spanish', 
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'zh': 'Chinese',
            'ja': 'Japanese',
            'ko': 'Korean',
            'ar': 'Arabic',
            'hi': 'Hindi',
            'ru': 'Russian'
        }
        
    async def initialize(self):
        """Initialize the voice processor and check API availability"""
        self.realtime_available = await check_realtime_access(self.openai_key)
        if self.realtime_available:
            self.realtime_client = RealtimeClient(self.openai_key)
            logger.info("Realtime API is available")
        else:
            logger.info("Realtime API not available, using standard pipeline")
    
    async def process_voice_input(
        self, 
        audio_data: bytes,
        language: str = 'auto',
        stream: bool = True
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process voice input with automatic pipeline selection"""
        
        # Detect language if auto
        if language == 'auto':
            language = await self._detect_language(audio_data)
        
        if self.realtime_available and stream:
            # Use Realtime API for streaming
            async for response in self._process_realtime(audio_data, language):
                yield response
        else:
            # Use standard pipeline
            result = await self._process_standard(audio_data, language)
            yield result
    
    async def start_continuous_session(self, language: str = 'auto'):
        """Start a continuous audio session with Realtime API"""
        if not self.realtime_available:
            return False
            
        try:
            # Create and connect the realtime client if needed
            if not self.realtime_client:
                self.realtime_client = RealtimeClient(self.openai_key)
            
            if not self.realtime_client.is_connected:
                logger.info("Connecting to Realtime API for continuous mode...")
                await self.realtime_client.connect()
                
                # Start event processing in background
                self.event_task = asyncio.create_task(self._process_realtime_events())
                
            return self.realtime_client.is_connected
            
        except Exception as e:
            logger.error(f"Failed to start continuous session: {e}")
            return False
    
    async def _process_realtime_events(self):
        """Process events from Realtime API in background"""
        try:
            # Initialize event queue if not already done
            if self.event_queue is None:
                self.event_queue = asyncio.Queue()
                
            async for event in self.realtime_client.process_events():
                logger.debug(f"Realtime event: {event['type']}")
                # Store events in a queue to be retrieved by the main process
                await self.event_queue.put(event)
                
        except Exception as e:
            logger.error(f"Event processing error: {e}")
    
    async def process_continuous_audio(
        self,
        audio_chunk: bytes,
        language: str = 'auto'
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process continuous audio stream for real-time interaction"""
        
        if not self.realtime_available:
            yield {
                "type": "error",
                "error": "Continuous mode requires Realtime API access"
            }
            return
        
        try:
            # Ensure session is started
            if not self.realtime_client or not self.realtime_client.is_connected:
                connected = await self.start_continuous_session(language)
                if not connected:
                    yield {
                        "type": "error",
                        "error": "Failed to start continuous session"
                    }
                    return
            
            # Send audio chunk to Realtime API
            await self.realtime_client.send_audio(audio_chunk)
            logger.debug(f"Sent audio chunk, queue size: {self.event_queue.qsize() if self.event_queue else 'None'}")
            
            # Check for any events in the queue
            if self.event_queue is not None:
                # Process multiple events if available
                events_processed = 0
                while not self.event_queue.empty() and events_processed < 10:
                    try:
                        event = self.event_queue.get_nowait()
                        
                        if event["type"] == "user_transcript_delta":
                            # Real-time transcription of user speech
                            logger.debug(f"Yielding user_transcript_delta: {event.get('delta', '')}")
                            yield event
                        
                        elif event["type"] == "user_transcript":
                            # Final user transcript
                            yield event
                            # Update conversation history
                            self.conversation_history.append({
                                "role": "user",
                                "content": event["text"]
                            })
                        
                        elif event["type"] == "transcript_delta":
                            # Assistant's response transcription
                            yield event
                        
                        elif event["type"] == "audio_delta":
                            # Assistant's audio response
                            logger.debug(f"Yielding audio_delta event")
                            # Ensure the audio data is in the correct field
                            if "delta" in event and not "audio" in event:
                                event["audio"] = event["delta"]
                            yield event
                        
                        elif event["type"] == "function_call":
                            # Handle function call
                            result = await self._execute_function(
                                event["name"],
                                event["arguments"]
                            )
                            
                            # Send result back
                            await self.realtime_client.function_call_output(
                                event["call_id"],
                                result
                            )
                        
                        elif event["type"] == "response_done":
                            # Response completed
                            yield {
                                "type": "response_complete",
                                "text": "",  # Will be filled by transcript deltas
                                "response": event.get("response", {})
                            }
                        
                        elif event["type"] == "error":
                            logger.error(f"Realtime API error: {event.get('error')}")
                            yield event
                            
                        events_processed += 1
                    except asyncio.QueueEmpty:
                        break
            
            # Small delay to prevent tight loop
            await asyncio.sleep(0.01)
                    
        except Exception as e:
            logger.error(f"Continuous audio processing error: {e}")
            yield {
                "type": "error",
                "error": str(e)
            }
    
    async def _process_realtime(
        self, 
        audio_data: bytes,
        language: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process using Realtime API with streaming"""
        try:
            if not self.realtime_client:
                self.realtime_client = RealtimeClient(self.openai_key)
            
            # Connect if not connected
            if not self.realtime_client.is_connected:
                await self.realtime_client.connect()
            
            # Set up function call handler
            self.realtime_client.on_function_call = self._handle_function_call
            
            # Update instructions for language
            instructions = f"""You are a multilingual flight search assistant.
            Current language: {language} ({self.supported_languages.get(language, language)}).
            Always respond in {self.supported_languages.get(language, language)}.
            Help users find flights using the search_flights function.
            Be conversational and helpful."""
            
            await self.realtime_client.update_instructions(instructions)
            
            # Send audio
            await self.realtime_client.send_audio(audio_data)
            await self.realtime_client.commit_audio()
            
            # Process events with timeout
            text_response = ""
            audio_chunks = []
            response_received = False
            
            # Set a timeout for receiving events
            timeout = 30  # 30 seconds timeout
            start_time = asyncio.get_event_loop().time()
            
            async for event in self.realtime_client.process_events():
                logger.debug(f"Processing event: {event['type']}")
                
                if event["type"] == "transcript_delta":
                    text_response += event["delta"]
                    yield {
                        "type": "transcript_delta",
                        "text": event["delta"],
                        "language": language
                    }
                
                elif event["type"] == "audio_delta":
                    audio_chunk = base64.b64decode(event["delta"])
                    audio_chunks.append(audio_chunk)
                    yield {
                        "type": "audio_delta",
                        "audio": audio_chunk,
                        "language": language
                    }
                
                elif event["type"] == "function_call":
                    # Handle function call
                    result = await self._execute_function(
                        event["name"],
                        event["arguments"]
                    )
                    
                    # Send result back
                    await self.realtime_client.function_call_output(
                        event["call_id"],
                        result
                    )
                
                elif event["type"] == "response_done":
                    # Final response
                    response_received = True
                    yield {
                        "type": "response_complete",
                        "text": text_response,
                        "audio": b"".join(audio_chunks) if audio_chunks else None,
                        "language": language
                    }
                    break
                
                elif event["type"] == "error":
                    logger.error(f"Realtime API error: {event.get('error')}")
                    # Fall back to standard pipeline
                    raise Exception(f"Realtime API error: {event.get('error')}")
                
                # Check timeout
                if asyncio.get_event_loop().time() - start_time > timeout:
                    logger.warning("Realtime API timeout, falling back to standard pipeline")
                    raise asyncio.TimeoutError("Realtime API timeout")
            
            # If no response received, something went wrong
            if not response_received:
                logger.warning("No response from Realtime API, falling back to standard pipeline")
                raise Exception("No response from Realtime API")
                
        except Exception as e:
            logger.error(f"Realtime API error: {e}, falling back to standard pipeline")
            # Fallback to standard pipeline
            result = await self._process_standard(audio_data, language)
            yield result
    
    async def _process_standard(
        self,
        audio_data: bytes,
        language: str
    ) -> Dict[str, Any]:
        """Process using standard STT -> LLM -> TTS pipeline"""
        try:
            # Step 1: Speech-to-Text (Whisper)
            logger.info(f"Transcribing audio (language: {language})")
            
            # Create a temporary file for audio
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            try:
                # Transcribe with language hint
                with open(temp_file_path, "rb") as audio_file:
                    # Only pass language if it's a valid ISO-639-1 code
                    lang_param = None
                    if language != 'auto' and len(language) == 2:
                        lang_param = language
                    
                    transcript = await self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language=lang_param,
                        response_format="verbose_json"
                    )
                
                text = transcript.text
                detected_language = transcript.language if hasattr(transcript, 'language') else language
                
                logger.info(f"Transcribed: {text}")
                
                # Add to conversation history
                self.conversation_history.append({
                    "role": "user",
                    "content": text
                })
                
                # Build messages with history
                messages = [
                    {
                        "role": "system",
                        "content": f"""You are a multilingual flight search assistant.
                        Current language: {self.supported_languages.get(detected_language, detected_language)}.
                        Always respond in the same language as the user.
                        Help users find flights using the available functions.
                        Remember the context from previous messages in the conversation."""
                    }
                ]
                
                # Add conversation history (limited to last N exchanges)
                messages.extend(self.conversation_history[-self.max_history:])
                
                # Step 2: Process with LLM (GPT-4 with functions)
                response = await self.client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=messages,
                    tools=ALL_FUNCTIONS,
                    tool_choice="auto"
                )
                
                # Handle function calls if any
                message = response.choices[0].message
                
                if message.tool_calls:
                    # Execute function calls
                    function_results = []
                    for tool_call in message.tool_calls:
                        result = await self._execute_function(
                            tool_call.function.name,
                            json.loads(tool_call.function.arguments)
                        )
                        function_results.append({
                            "tool_call_id": tool_call.id,
                            "output": json.dumps(result) if not isinstance(result, str) else result
                        })
                    
                    # Get final response with function results
                    final_response = await self.client.chat.completions.create(
                        model="gpt-4-turbo-preview",
                        messages=[
                            {
                                "role": "system",
                                "content": f"""You are a multilingual flight search assistant.
                                Current language: {self.supported_languages.get(detected_language, detected_language)}.
                                Always respond in the same language as the user."""
                            },
                            {
                                "role": "user",
                                "content": text
                            },
                            message,
                            *[{
                                "role": "tool",
                                "tool_call_id": result["tool_call_id"],
                                "content": result["output"]
                            } for result in function_results]
                        ]
                    )
                    
                    response_text = final_response.choices[0].message.content
                else:
                    response_text = message.content
                
                # Add assistant's response to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response_text
                })
                
                # Trim history if too long
                if len(self.conversation_history) > self.max_history * 2:
                    self.conversation_history = self.conversation_history[-(self.max_history * 2):]
                
                # Step 3: Text-to-Speech
                logger.info(f"Generating speech for: {response_text[:100]}...")
                
                # Select voice based on language
                voice = self._get_voice_for_language(detected_language)
                
                tts_response = await self.client.audio.speech.create(
                    model="tts-1",
                    voice=voice,
                    input=response_text
                )
                
                audio_content = tts_response.content
                
                return {
                    "type": "response_complete",
                    "text": response_text,
                    "audio": audio_content,
                    "language": detected_language,
                    "input_text": text
                }
                
            finally:
                # Clean up temp file
                import os
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                
        except Exception as e:
            logger.error(f"Standard pipeline error: {e}")
            return {
                "type": "error",
                "error": str(e),
                "language": language
            }
    
    async def _detect_language(self, audio_data: bytes) -> str:
        """Detect language from audio using Whisper"""
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            try:
                with open(temp_file_path, "rb") as audio_file:
                    result = await self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="verbose_json"
                    )
                
                detected = result.language if hasattr(result, 'language') else 'en'
                # Whisper already returns ISO-639-1 codes, no conversion needed
                logger.info(f"Detected language: {detected}")
                return detected
                
            finally:
                import os
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            logger.error(f"Language detection error: {e}")
            return 'en'
    
    async def _execute_function(self, function_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a function call"""
        logger.info(f"Executing function: {function_name} with args: {arguments}")
        
        if function_name == "search_flights":
            flights = await self.flight_service.search_flights(**arguments)
            return {"flights": flights, "count": len(flights)}
        
        elif function_name == "get_airport_code":
            code = await self.flight_service.get_airport_code(arguments["city"])
            return {"city": arguments["city"], "airport_code": code}
        
        elif function_name == "get_flight_details":
            details = await self.flight_service.get_flight_details(arguments["flight_id"])
            return details
        
        else:
            return {"error": f"Unknown function: {function_name}"}
    
    async def _handle_function_call(self, call_id: str, name: str, arguments: Dict[str, Any]):
        """Handle function calls from Realtime API"""
        result = await self._execute_function(name, arguments)
        await self.realtime_client.function_call_output(call_id, result)
    
    def _get_voice_for_language(self, language: str) -> str:
        """Get appropriate TTS voice for language"""
        # Map languages to appropriate voices
        voice_map = {
            'en': 'alloy',
            'es': 'nova',
            'fr': 'shimmer',
            'de': 'echo',
            'it': 'onyx',
            'pt': 'nova',
            'zh': 'alloy',
            'ja': 'shimmer',
            'ko': 'echo',
            'ar': 'onyx',
            'hi': 'nova',
            'ru': 'fable'
        }
        
        return voice_map.get(language, 'alloy')


# Convenience function for simple voice processing
async def process_voice_query(
    audio_data: bytes,
    language: str = 'auto'
) -> Dict[str, Any]:
    """Simple interface for processing voice queries"""
    processor = VoiceProcessor()
    await processor.initialize()
    
    # For simple interface, just get the complete response
    async for response in processor.process_voice_input(audio_data, language, stream=False):
        if response["type"] == "response_complete":
            return response
    
    return {"type": "error", "error": "No response generated"}