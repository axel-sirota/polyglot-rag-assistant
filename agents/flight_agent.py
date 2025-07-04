from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from typing import TypedDict, List, Optional, Dict, Any, Literal
from datetime import datetime, timedelta
import json
import re
import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logging_config import setup_logging

logger = setup_logging('flight_agent')

class FlightSearchState(TypedDict):
    messages: List[str]
    origin: Optional[str]
    destination: Optional[str]
    departure_date: Optional[str]
    return_date: Optional[str]
    passengers: Optional[int]
    cabin_class: Optional[str]
    search_results: Optional[List[Dict]]
    final_answer: Optional[str]
    needs_clarification: bool
    language: str

class FlightSearchAgent:
    def __init__(self, flight_api):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3
        )
        self.flight_api = flight_api
        self.graph = self._build_graph()
        
        # Date patterns for different languages
        self.date_patterns = {
            "en": [
                r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})",  # MM/DD/YYYY or MM-DD-YYYY
                r"(\d{1,2})\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{2,4})",
                r"(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2}),?\s+(\d{2,4})",
                r"(tomorrow|next week|next month)",
                r"in (\d+) days?"
            ],
            "es": [
                r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})",
                r"(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+de\s+(\d{2,4})",
                r"(mañana|próxima semana|próximo mes)",
                r"en (\d+) días?"
            ],
            "fr": [
                r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})",
                r"(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{2,4})",
                r"(demain|semaine prochaine|mois prochain)",
                r"dans (\d+) jours?"
            ]
        }
    
    def _build_graph(self):
        """Build the LangGraph workflow for flight search"""
        workflow = StateGraph(FlightSearchState)
        
        # Define nodes
        workflow.add_node("extract_params", self.extract_search_params)
        workflow.add_node("validate_params", self.validate_params)
        workflow.add_node("clarify_params", self.clarify_missing_params)
        workflow.add_node("search_flights", self.search_flights_mcp)
        workflow.add_node("format_results", self.format_results)
        
        # Define edges
        workflow.add_edge(START, "extract_params")
        workflow.add_edge("extract_params", "validate_params")
        
        # Conditional routing based on parameter validation
        workflow.add_conditional_edges(
            "validate_params",
            self.check_params_complete,
            {
                "complete": "search_flights",
                "incomplete": "clarify_params",
                "invalid": "clarify_params"
            }
        )
        
        workflow.add_edge("clarify_params", END)
        workflow.add_edge("search_flights", "format_results")
        workflow.add_edge("format_results", END)
        
        return workflow.compile()
    
    async def extract_search_params(self, state: FlightSearchState) -> FlightSearchState:
        """Use GPT-4o-mini to extract flight search parameters from user query"""
        try:
            query = state["messages"][-1] if state["messages"] else ""
            language = state.get("language", "en")
            
            # Create extraction prompt
            prompt = f"""Extract flight search parameters from the following query in {language}:
            
            Query: "{query}"
            
            Extract the following information:
            1. Origin city or airport code
            2. Destination city or airport code
            3. Departure date (convert to YYYY-MM-DD format)
            4. Return date if mentioned (convert to YYYY-MM-DD format)
            5. Number of passengers (default to 1 if not mentioned)
            6. Cabin class (economy/business/first, default to economy)
            
            Respond in JSON format:
            {{
                "origin": "city or code",
                "destination": "city or code",
                "departure_date": "YYYY-MM-DD",
                "return_date": "YYYY-MM-DD or null",
                "passengers": 1,
                "cabin_class": "economy"
            }}
            
            If dates are relative (like "tomorrow", "next week"), calculate from today's date: {datetime.now().date()}
            """
            
            response = await self.llm.ainvoke(prompt)
            
            # Parse the response
            try:
                params = json.loads(response.content)
                
                # Update state with extracted parameters
                state["origin"] = params.get("origin")
                state["destination"] = params.get("destination")
                state["departure_date"] = params.get("departure_date")
                state["return_date"] = params.get("return_date")
                state["passengers"] = params.get("passengers", 1)
                state["cabin_class"] = params.get("cabin_class", "economy")
                
            except json.JSONDecodeError:
                logger.error("Failed to parse LLM response as JSON")
                state["needs_clarification"] = True
            
            return state
            
        except Exception as e:
            logger.error(f"Error extracting parameters: {e}")
            state["needs_clarification"] = True
            return state
    
    async def validate_params(self, state: FlightSearchState) -> FlightSearchState:
        """Validate extracted parameters"""
        errors = []
        
        # Check required fields
        if not state.get("origin"):
            errors.append("origin city or airport")
        
        if not state.get("destination"):
            errors.append("destination city or airport")
        
        if not state.get("departure_date"):
            errors.append("departure date")
        else:
            # Validate date format
            try:
                dep_date = datetime.strptime(state["departure_date"], "%Y-%m-%d")
                # Check if date is in the past
                if dep_date.date() < datetime.now().date():
                    errors.append("departure date (cannot be in the past)")
            except ValueError:
                errors.append("valid departure date format")
        
        # Validate return date if provided
        if state.get("return_date"):
            try:
                ret_date = datetime.strptime(state["return_date"], "%Y-%m-%d")
                dep_date = datetime.strptime(state["departure_date"], "%Y-%m-%d")
                if ret_date < dep_date:
                    errors.append("return date (must be after departure date)")
            except ValueError:
                errors.append("valid return date format")
        
        # Set clarification flag if there are errors
        state["needs_clarification"] = len(errors) > 0
        
        if errors:
            state["final_answer"] = self._get_clarification_message(errors, state.get("language", "en"))
        
        return state
    
    def check_params_complete(self, state: FlightSearchState) -> Literal["complete", "incomplete", "invalid"]:
        """Check if all required parameters are present and valid"""
        if state.get("needs_clarification", False):
            return "incomplete"
        
        if all([state.get("origin"), state.get("destination"), state.get("departure_date")]):
            return "complete"
        
        return "incomplete"
    
    async def clarify_missing_params(self, state: FlightSearchState) -> FlightSearchState:
        """Ask user to clarify missing parameters"""
        # The final_answer is already set in validate_params
        return state
    
    async def search_flights_mcp(self, state: FlightSearchState) -> FlightSearchState:
        """Call MCP server to search flights"""
        try:
            # Prepare search parameters
            search_params = {
                "origin": state["origin"],
                "destination": state["destination"],
                "departure_date": state["departure_date"],
                "passengers": state.get("passengers", 1),
                "cabin_class": state.get("cabin_class", "economy")
            }
            
            if state.get("return_date"):
                search_params["return_date"] = state["return_date"]
            
            # Call MCP server
            results = await self.mcp_client.call_tool("search_flights", search_params)
            
            state["search_results"] = results
            
        except Exception as e:
            logger.error(f"Error searching flights: {e}")
            state["search_results"] = []
            state["final_answer"] = self._get_error_message(state.get("language", "en"))
        
        return state
    
    async def format_results(self, state: FlightSearchState) -> FlightSearchState:
        """Format flight results for presentation"""
        if not state.get("search_results"):
            state["final_answer"] = self._get_no_results_message(state.get("language", "en"))
            return state
        
        # Results will be formatted by the RAG agent with Claude
        # Here we just ensure they're properly structured
        state["final_answer"] = "FLIGHT_RESULTS_READY"
        
        return state
    
    def _get_clarification_message(self, missing_fields: List[str], language: str) -> str:
        """Get clarification message in appropriate language"""
        messages = {
            "en": f"I need more information to search for flights. Please provide: {', '.join(missing_fields)}",
            "es": f"Necesito más información para buscar vuelos. Por favor proporcione: {', '.join(missing_fields)}",
            "fr": f"J'ai besoin de plus d'informations pour rechercher des vols. Veuillez fournir: {', '.join(missing_fields)}",
            "de": f"Ich benötige weitere Informationen für die Flugsuche. Bitte geben Sie an: {', '.join(missing_fields)}",
            "it": f"Ho bisogno di più informazioni per cercare i voli. Per favore fornisci: {', '.join(missing_fields)}",
            "pt": f"Preciso de mais informações para pesquisar voos. Por favor, forneça: {', '.join(missing_fields)}"
        }
        
        return messages.get(language, messages["en"])
    
    def _get_no_results_message(self, language: str) -> str:
        """Get no results message in appropriate language"""
        messages = {
            "en": "I couldn't find any flights matching your criteria. Try adjusting your dates or consider nearby airports.",
            "es": "No pude encontrar vuelos que coincidan con sus criterios. Intente ajustar sus fechas o considere aeropuertos cercanos.",
            "fr": "Je n'ai trouvé aucun vol correspondant à vos critères. Essayez d'ajuster vos dates ou envisagez des aéroports à proximité.",
            "de": "Ich konnte keine Flüge finden, die Ihren Kriterien entsprechen. Versuchen Sie, Ihre Daten anzupassen oder nahe gelegene Flughäfen in Betracht zu ziehen.",
            "it": "Non sono riuscito a trovare voli che corrispondano ai tuoi criteri. Prova a modificare le date o considera gli aeroporti vicini.",
            "pt": "Não consegui encontrar voos que correspondam aos seus critérios. Tente ajustar suas datas ou considere aeroportos próximos."
        }
        
        return messages.get(language, messages["en"])
    
    def _get_error_message(self, language: str) -> str:
        """Get error message in appropriate language"""
        messages = {
            "en": "I encountered an error while searching for flights. Please try again.",
            "es": "Encontré un error al buscar vuelos. Por favor, inténtelo de nuevo.",
            "fr": "J'ai rencontré une erreur lors de la recherche de vols. Veuillez réessayer.",
            "de": "Bei der Suche nach Flügen ist ein Fehler aufgetreten. Bitte versuchen Sie es erneut.",
            "it": "Ho riscontrato un errore durante la ricerca dei voli. Per favore riprova.",
            "pt": "Encontrei um erro ao pesquisar voos. Por favor, tente novamente."
        }
        
        return messages.get(language, messages["en"])
    
    async def process_query(self, query: str, language: str = "en") -> Dict[str, Any]:
        """Main entry point to process a flight search query"""
        initial_state = {
            "messages": [query],
            "language": language,
            "needs_clarification": False
        }
        
        result = await self.graph.ainvoke(initial_state)
        
        return {
            "needs_clarification": result.get("needs_clarification", False),
            "clarification_message": result.get("final_answer") if result.get("needs_clarification") else None,
            "flight_results": result.get("search_results", []),
            "origin": result.get("origin"),
            "destination": result.get("destination"),
            "departure_date": result.get("departure_date"),
            "return_date": result.get("return_date")
        }