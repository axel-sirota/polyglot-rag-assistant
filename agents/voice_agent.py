from livekit.agents import AgentSession, JobContext, cli, llm
from livekit.plugins import openai, silero
from typing import Optional, Tuple
import os
import logging

logger = logging.getLogger(__name__)

class VoiceAgent:
    def __init__(self):
        self.session: Optional[AgentSession] = None
        self.vad = None
        self.stt = None
        self.tts = None
        self.current_language = "en"
        
    async def initialize(self):
        """Initialize voice components"""
        self.vad = silero.VAD.load(
            min_speech_duration=0.1,
            min_silence_duration=0.3,
            activation_threshold=0.5
        )
        
        self.stt = openai.STT(
            model="whisper-1",
            language=None  # Auto-detect language
        )
        
        self.tts = openai.TTS(
            model="tts-1",
            voice="alloy",
            speed=1.0
        )
    
    async def process_voice_input(self, audio_data) -> Tuple[str, str]:
        """Process voice input and return transcript with detected language"""
        try:
            # Use OpenAI Whisper to transcribe
            result = await self.stt.recognize(audio_data)
            
            # Extract transcript and language
            transcript = result.text
            detected_language = result.language if hasattr(result, 'language') else 'en'
            
            # Update current language if different
            if detected_language and detected_language != self.current_language:
                self.current_language = detected_language
                logger.info(f"Language switched to: {detected_language}")
            
            return transcript, self.current_language
            
        except Exception as e:
            logger.error(f"Error processing voice input: {e}")
            return "", self.current_language
    
    async def synthesize_speech(self, text: str, language: str = None) -> bytes:
        """Convert text to speech"""
        try:
            # Use the current language if not specified
            target_language = language or self.current_language
            
            # TTS with OpenAI
            audio_data = await self.tts.synthesize(text)
            return audio_data
            
        except Exception as e:
            logger.error(f"Error synthesizing speech: {e}")
            return b""

async def entrypoint(ctx: JobContext):
    """LiveKit agent entrypoint"""
    logger.info("Starting Polyglot RAG Voice Agent")
    
    # Connect to the room
    await ctx.connect()
    
    # Initialize voice agent
    agent = VoiceAgent()
    await agent.initialize()
    
    # Import orchestrator to handle the full pipeline
    from main import PolyglotRAGOrchestrator
    orchestrator = PolyglotRAGOrchestrator()
    
    # Create assistant with custom function
    assistant = llm.AssistantLLM(
        vad=agent.vad,
        stt=agent.stt,
        tts=agent.tts,
        fnc_ctx=llm.FunctionContext()
    )
    
    # Custom function to process queries through our pipeline
    @assistant.fnc_ctx.ai_callable()
    async def process_user_query(query: str) -> str:
        """Process user query through RAG and flight search pipeline"""
        # Detect language from the query
        language = agent.current_language
        
        # Process through orchestrator
        response = await orchestrator.process_text_query(query, language)
        
        return response
    
    # Start the session
    session = AgentSession(
        agent=assistant,
        fnc_ctx=assistant.fnc_ctx
    )
    
    await session.start(ctx.room)
    await session.wait()

if __name__ == "__main__":
    cli.run_app(
        entrypoint,
        name="polyglot-rag-voice-agent",
        description="Multilingual voice-enabled flight search assistant"
    )