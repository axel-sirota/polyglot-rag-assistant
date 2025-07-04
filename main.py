import asyncio
from agents.voice_agent import VoiceAgent
from agents.flight_agent import FlightSearchAgent
from agents.rag_agent import RAGAgent
from services.embeddings import EmbeddingsService
from services.vector_store import FAISSVectorStore
from services.flight_api import FlightAPIWrapper
import os
from dotenv import load_dotenv
import logging
from typing import Optional, Dict, List, Any
from utils.logging_config import setup_logging, configure_root_logger, suppress_noisy_loggers

# Configure logging
configure_root_logger()
suppress_noisy_loggers()
logger = setup_logging('orchestrator')

load_dotenv()

class PolyglotRAGOrchestrator:
    def __init__(self):
        logger.info("Initializing Polyglot RAG Orchestrator...")
        
        # Initialize services
        self.embeddings_service = EmbeddingsService()
        self.vector_store = FAISSVectorStore(dimension=1536)
        self.flight_api = FlightAPIWrapper()
        
        # Initialize agents
        self.voice_agent = VoiceAgent()
        self.flight_agent = FlightSearchAgent(self.flight_api)
        self.rag_agent = RAGAgent(self.vector_store)
        
        # Conversation state
        self.conversation_history = []
        self.current_language = "en"
        
        # Initialize vector store with sample data
        self._initialize_sample_data()
    
    async def initialize(self):
        """Async initialization of components"""
        try:
            # Initialize voice agent
            await self.voice_agent.initialize()
            
            # Initialize flight API
            await self.flight_api.initialize()
            
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
    
    def _initialize_sample_data(self):
        """Load sample travel data into vector store for demo purposes"""
        try:
            sample_docs = self.vector_store.add_sample_travel_data()
            
            # Note: Embeddings will be generated on first use
            logger.info(f"Prepared {len(sample_docs) if sample_docs else 0} sample documents")
            
        except Exception as e:
            logger.error(f"Error initializing sample data: {e}")
    
    async def _embed_sample_docs(self, sample_docs: List[Dict]):
        """Embed and store sample documents"""
        try:
            contents = [doc["content"] for doc in sample_docs]
            embeddings = await self.embeddings_service.embed(contents)
            
            # Convert to numpy array
            import numpy as np
            embeddings_array = np.array(embeddings)
            
            # Add to vector store
            metadata = [doc["metadata"] for doc in sample_docs]
            self.vector_store.add(embeddings_array, contents, metadata)
            
            logger.info(f"Added {len(contents)} sample documents to vector store")
            
        except Exception as e:
            logger.error(f"Error embedding sample docs: {e}")
    
    async def process_voice_input(self, audio_input) -> str:
        """Main processing pipeline for voice input"""
        try:
            # 1. Voice to text with language detection
            transcript, detected_language = await self.voice_agent.process_voice_input(audio_input)
            
            if not transcript:
                return await self._get_error_response(self.current_language)
            
            # Update current language if changed
            if detected_language != self.current_language:
                self.current_language = detected_language
                logger.info(f"Language switched to: {detected_language}")
            
            # 2. Process the text query
            response = await self.process_text_query(transcript, detected_language)
            
            # 3. Convert response to speech
            audio_response = await self.voice_agent.synthesize_speech(response, detected_language)
            
            return audio_response
            
        except Exception as e:
            logger.error(f"Error processing voice input: {e}")
            return await self._get_error_response(self.current_language)
    
    async def process_text_query(self, query: str, language: str = "en") -> str:
        """Process text query through the pipeline"""
        try:
            # 1. Generate embedding for the query
            query_embedding = await self.embeddings_service.embed(query)
            
            # 2. Check if this is a flight-related query
            flight_results = None
            if self._is_flight_query(query):
                # Process through flight agent
                result = await self.flight_agent.process_query(query, language)
                
                if result["needs_clarification"]:
                    return result["clarification_message"]
                
                flight_results = result["flight_results"]
            
            # 3. Generate final answer with Claude
            answer = await self.rag_agent.answer_with_context(
                query=query,
                query_embedding=query_embedding,
                flight_results=flight_results,
                language=language,
                conversation_history=self.conversation_history[-5:]  # Last 5 exchanges
            )
            
            # 4. Update conversation history
            self.conversation_history.append({"role": "user", "content": query})
            self.conversation_history.append({"role": "assistant", "content": answer})
            
            return answer
            
        except Exception as e:
            logger.error(f"Error processing text query: {e}")
            return await self._get_error_response(language)
    
    def _is_flight_query(self, text: str) -> bool:
        """Detect if the query is about flights"""
        flight_keywords = [
            # English
            'flight', 'fly', 'flying', 'book', 'ticket', 'airline', 'airport',
            'departure', 'arrival', 'round trip', 'one way',
            # Spanish
            'vuelo', 'volar', 'boleto', 'aerolínea', 'aeropuerto',
            'salida', 'llegada', 'ida y vuelta',
            # French
            'vol', 'voler', 'billet', 'compagnie aérienne', 'aéroport',
            'départ', 'arrivée', 'aller-retour',
            # German
            'flug', 'fliegen', 'ticket', 'fluggesellschaft', 'flughafen',
            'abflug', 'ankunft', 'hin und zurück',
            # Italian
            'volo', 'volare', 'biglietto', 'compagnia aerea', 'aeroporto',
            'partenza', 'arrivo', 'andata e ritorno',
            # Portuguese
            'voo', 'voar', 'passagem', 'companhia aérea', 'aeroporto',
            'partida', 'chegada', 'ida e volta',
            # Japanese
            '航空', 'フライト', '飛行機', 'チケット', '空港',
            # Chinese
            '航班', '飞机', '机票', '机场', '起飞', '到达'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in flight_keywords)
    
    async def _get_error_response(self, language: str) -> str:
        """Get error response in appropriate language"""
        error_responses = {
            "en": "I apologize, but I encountered an error. Please try again.",
            "es": "Lo siento, pero encontré un error. Por favor, inténtalo de nuevo.",
            "fr": "Je m'excuse, mais j'ai rencontré une erreur. Veuillez réessayer.",
            "de": "Es tut mir leid, aber es ist ein Fehler aufgetreten. Bitte versuchen Sie es erneut.",
            "it": "Mi scuso, ma ho riscontrato un errore. Per favore riprova.",
            "pt": "Desculpe, mas encontrei um erro. Por favor, tente novamente.",
            "ja": "申し訳ございませんが、エラーが発生しました。もう一度お試しください。",
            "zh": "抱歉，遇到了错误。请重试。"
        }
        
        return error_responses.get(language, error_responses["en"])
    
    async def run(self):
        """Run the orchestrator (for standalone mode)"""
        await self.initialize()
        logger.info("Polyglot RAG Orchestrator is ready!")
        
        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up resources"""
        if self.flight_api:
            await self.flight_api.close()
        logger.info("Cleanup completed")

# For direct execution
if __name__ == "__main__":
    orchestrator = PolyglotRAGOrchestrator()
    asyncio.run(orchestrator.run())