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

logger = logging.getLogger(__name__)

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
            
            # Process events
            text_response = ""
            audio_chunks = []
            
            async for event in self.realtime_client.process_events():
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
                    yield {
                        "type": "response_complete",
                        "text": text_response,
                        "audio": b"".join(audio_chunks) if audio_chunks else None,
                        "language": language
                    }
                    break
                
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
                
                # Step 2: Process with LLM (GPT-4 with functions)
                response = await self.client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {
                            "role": "system",
                            "content": f"""You are a multilingual flight search assistant.
                            Current language: {self.supported_languages.get(detected_language, detected_language)}.
                            Always respond in the same language as the user.
                            Help users find flights using the available functions."""
                        },
                        {
                            "role": "user",
                            "content": text
                        }
                    ],
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