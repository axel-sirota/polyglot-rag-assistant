from anthropic import AsyncAnthropic
import numpy as np
from typing import List, Dict, Optional, Any
import asyncio
import os
import json
import logging

logger = logging.getLogger(__name__)

class RAGAgent:
    def __init__(self, vector_store):
        self.anthropic = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.vector_store = vector_store
        
        # Language prompts for different languages
        self.language_prompts = {
            "en": "You are a helpful multilingual travel assistant specializing in flight search and travel planning.",
            "es": "Eres un asistente de viaje multilingüe especializado en búsqueda de vuelos y planificación de viajes.",
            "fr": "Vous êtes un assistant de voyage multilingue spécialisé dans la recherche de vols et la planification de voyages.",
            "de": "Sie sind ein mehrsprachiger Reiseassistent, spezialisiert auf Flugsuche und Reiseplanung.",
            "it": "Sei un assistente di viaggio multilingue specializzato nella ricerca di voli e nella pianificazione dei viaggi.",
            "pt": "Você é um assistente de viagem multilíngue especializado em busca de voos e planejamento de viagens.",
            "ja": "あなたは、フライト検索と旅行計画を専門とする多言語対応の旅行アシスタントです。",
            "zh": "您是一位专门从事航班搜索和旅行规划的多语言旅行助手。",
            "ko": "당신은 항공편 검색과 여행 계획을 전문으로 하는 다국어 여행 도우미입니다.",
            "ar": "أنت مساعد سفر متعدد اللغات متخصص في البحث عن الرحلات الجوية وتخطيط السفر.",
            "hi": "आप उड़ान खोज और यात्रा योजना में विशेषज्ञता वाले बहुभाषी यात्रा सहायक हैं।",
            "ru": "Вы многоязычный помощник по путешествиям, специализирующийся на поиске рейсов и планировании путешествий."
        }
    
    def _get_system_prompt(self, language: str) -> str:
        """Get system prompt in the appropriate language"""
        base_prompt = self.language_prompts.get(language, self.language_prompts["en"])
        
        return f"""{base_prompt}

Key instructions:
1. Always respond in {language} unless the user explicitly switches languages
2. If the user switches languages mid-conversation, acknowledge it and continue in the new language
3. When presenting flight results, format them clearly with prices, times, and durations
4. Be conversational and helpful, providing additional travel tips when relevant
5. If no flights are found, suggest alternative dates or nearby airports
6. Always mention if prices are estimates or if real-time data is unavailable"""
    
    async def answer_with_context(
        self, 
        query: str, 
        query_embedding: np.ndarray,
        flight_results: Optional[List[Dict]] = None,
        language: str = "en",
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """Use Claude Sonnet 4 to generate final answer with RAG context"""
        
        try:
            # Retrieve relevant documents from vector store
            relevant_docs = await self._retrieve_relevant_docs(query_embedding)
            
            # Build context from retrieved documents and flight results
            context = self._build_context(relevant_docs, flight_results)
            
            # Prepare messages
            messages = []
            
            # Add conversation history if available
            if conversation_history:
                messages.extend(conversation_history)
            
            # Add current query
            messages.append({
                "role": "user",
                "content": self._format_user_query(query, context, language)
            })
            
            # Generate response with Claude
            response = await self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                temperature=0.7,
                system=self._get_system_prompt(language),
                messages=messages
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Error in RAG agent: {e}")
            return self._get_error_message(language)
    
    async def _retrieve_relevant_docs(self, query_embedding: np.ndarray, k: int = 5) -> List[Dict]:
        """Retrieve relevant documents from vector store"""
        try:
            if self.vector_store and self.vector_store.index is not None:
                results = self.vector_store.search(query_embedding, k=k)
                return results
            return []
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return []
    
    def _build_context(self, relevant_docs: List[Dict], flight_results: Optional[List[Dict]]) -> str:
        """Build context string from retrieved docs and flight results"""
        context_parts = []
        
        # Add retrieved documents
        if relevant_docs:
            context_parts.append("Relevant Information:")
            for i, doc in enumerate(relevant_docs, 1):
                context_parts.append(f"\n{i}. {doc.get('content', '')}")
        
        # Add flight results
        if flight_results:
            context_parts.append("\n\nFlight Search Results:")
            for i, flight in enumerate(flight_results, 1):
                context_parts.append(self._format_flight_result(flight, i))
        
        return "\n".join(context_parts)
    
    def _format_flight_result(self, flight: Dict, index: int) -> str:
        """Format a single flight result"""
        return f"""
{index}. {flight.get('airline', 'Unknown Airline')} - Flight {flight.get('flight_number', 'N/A')}
   Departure: {flight.get('departure_time', 'N/A')}
   Arrival: {flight.get('arrival_time', 'N/A')}
   Duration: {flight.get('duration', 'N/A')}
   Price: {flight.get('price', 'N/A')}
   Stops: {flight.get('stops', 0)}
   Booking: {flight.get('booking_link', 'Not available')}"""
    
    def _format_user_query(self, query: str, context: str, language: str) -> str:
        """Format the user query with context"""
        if context:
            return f"""Context Information:
{context}

User Query: {query}

Please provide a helpful, conversational response in {language} that addresses the user's query using the provided context and flight information."""
        else:
            return f"""User Query: {query}

Please provide a helpful, conversational response in {language} that addresses the user's query."""
    
    def _get_error_message(self, language: str) -> str:
        """Get error message in the appropriate language"""
        error_messages = {
            "en": "I apologize, but I encountered an error processing your request. Please try again.",
            "es": "Lo siento, pero encontré un error al procesar tu solicitud. Por favor, inténtalo de nuevo.",
            "fr": "Je m'excuse, mais j'ai rencontré une erreur lors du traitement de votre demande. Veuillez réessayer.",
            "de": "Es tut mir leid, aber bei der Bearbeitung Ihrer Anfrage ist ein Fehler aufgetreten. Bitte versuchen Sie es erneut.",
            "it": "Mi scuso, ma ho riscontrato un errore nell'elaborazione della tua richiesta. Per favore riprova.",
            "pt": "Desculpe, mas encontrei um erro ao processar sua solicitação. Por favor, tente novamente.",
            "ja": "申し訳ございませんが、リクエストの処理中にエラーが発生しました。もう一度お試しください。",
            "zh": "抱歉，处理您的请求时遇到错误。请重试。",
            "ko": "죄송합니다. 요청을 처리하는 중에 오류가 발생했습니다. 다시 시도해 주세요.",
            "ar": "أعتذر، لكنني واجهت خطأ في معالجة طلبك. يرجى المحاولة مرة أخرى.",
            "hi": "मुझे खेद है, लेकिन आपके अनुरोध को संसाधित करते समय एक त्रुटि हुई। कृपया पुनः प्रयास करें।",
            "ru": "Извините, но при обработке вашего запроса произошла ошибка. Пожалуйста, попробуйте еще раз."
        }
        
        return error_messages.get(language, error_messages["en"])
    
    async def generate_travel_tips(self, destination: str, language: str = "en") -> str:
        """Generate travel tips for a destination"""
        try:
            response = await self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=512,
                temperature=0.8,
                system=self._get_system_prompt(language),
                messages=[{
                    "role": "user",
                    "content": f"Please provide 3-5 brief travel tips for visiting {destination}. Keep it concise and practical."
                }]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Error generating travel tips: {e}")
            return ""