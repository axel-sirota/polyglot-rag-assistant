"""Flight Search API Server - Direct implementation without MCP"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import os
import json
import asyncio
import re
from dotenv import load_dotenv
import uvicorn
import logging
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logging_config import setup_logging
from .real_flight_search import get_real_flights
from .amadeus_sdk_flight_search import AmadeusSDKFlightSearch

# Set up logging
from utils.session_logging import setup_session_logging
logger = setup_session_logging('flight_search_api')

load_dotenv()

app = FastAPI(title="Flight Search API", version="1.0.0")

# Request models
class FlightSearchRequest(BaseModel):
    origin: str
    destination: str
    departure_date: str
    return_date: Optional[str] = None
    passengers: int = 1
    cabin_class: str = "economy"
    currency: str = "USD"

class FlightSearchServer:
    def __init__(self):
        self.serpapi_key = os.getenv("SERPAPI_API_KEY")
        self.serper_key = os.getenv("SERPER_API_KEY")  # Serper.dev for Google search
        self.http_client = httpx.AsyncClient()
        # Initialize Amadeus SDK
        self.amadeus_search = AmadeusSDKFlightSearch()
        
        # Multilingual city name mappings (normalize to English)
        self.multilingual_cities = {
            # Spanish
            "nueva york": "new york",
            "nueva jersey": "new jersey",
            "nuevo york": "new york", 
            "san francisco": "san francisco",
            "los ángeles": "los angeles",
            "los angeles": "los angeles",
            "miami": "miami",
            "chicago": "chicago",
            "boston": "boston",
            "filadelfia": "philadelphia",
            "washington": "washington",
            "atlanta": "atlanta",
            "dallas": "dallas",
            "houston": "houston",
            "phoenix": "phoenix",
            "las vegas": "las vegas",
            "seattle": "seattle",
            "londres": "london",
            "parís": "paris",
            "madrid": "madrid",
            "barcelona": "barcelona",
            "roma": "rome",
            "milán": "milan",
            "berlín": "berlin",
            "múnich": "munich",
            "fráncfort": "frankfurt",
            "ámsterdam": "amsterdam",
            "bruselas": "brussels",
            "viena": "vienna",
            "zúrich": "zurich",
            "ginebra": "geneva",
            "moscú": "moscow",
            "san petersburgo": "saint petersburg",
            "estambul": "istanbul",
            "atenas": "athens",
            "lisboa": "lisbon",
            "oporto": "porto",
            "dublín": "dublin",
            "edimburgo": "edinburgh",
            "copenhague": "copenhagen",
            "estocolmo": "stockholm",
            "helsinki": "helsinki",
            "varsovia": "warsaw",
            "praga": "prague",
            "budapest": "budapest",
            "bucarest": "bucharest",
            "belgrado": "belgrade",
            "zagreb": "zagreb",
            "liubliana": "ljubljana",
            "sofía": "sofia",
            "ciudad de méxico": "mexico city",
            "cancún": "cancun",
            "guadalajara": "guadalajara",
            "monterrey": "monterrey",
            "buenos aires": "buenos aires",
            "são paulo": "sao paulo",
            "san pablo": "sao paulo",
            "río de janeiro": "rio de janeiro",
            "río": "rio de janeiro",
            "lima": "lima",
            "bogotá": "bogota",
            "caracas": "caracas",
            "quito": "quito",
            "la paz": "la paz",
            "asunción": "asuncion",
            "montevideo": "montevideo",
            "santiago": "santiago",
            "santiago de chile": "santiago",
            "la habana": "havana",
            "santo domingo": "santo domingo",
            "san juan": "san juan",
            "panamá": "panama city",
            "ciudad de panamá": "panama city",
            "san josé": "san jose",
            "managua": "managua",
            "tegucigalpa": "tegucigalpa",
            "san salvador": "san salvador",
            "ciudad de guatemala": "guatemala city",
            # French
            "new york": "new york",
            "los angeles": "los angeles",
            "san francisco": "san francisco",
            "chicago": "chicago",
            "miami": "miami",
            "londres": "london",
            "madrid": "madrid",
            "barcelone": "barcelona",
            "rome": "rome",
            "berlin": "berlin",
            "munich": "munich",
            "francfort": "frankfurt",
            "amsterdam": "amsterdam",
            "bruxelles": "brussels",
            "vienne": "vienna",
            "zurich": "zurich",
            "genève": "geneva",
            "moscou": "moscow",
            "saint-pétersbourg": "saint petersburg",
            "istanbul": "istanbul",
            "athènes": "athens",
            "lisbonne": "lisbon",
            "dublin": "dublin",
            "édimbourg": "edinburgh",
            "copenhague": "copenhagen",
            "varsovie": "warsaw",
            "budapest": "budapest",
            "bucarest": "bucharest",
            "pékin": "beijing",
            "shanghai": "shanghai",
            "tokyo": "tokyo",
            "osaka": "osaka",
            "séoul": "seoul",
            "bangkok": "bangkok",
            "singapour": "singapore",
            "hong kong": "hong kong",
            "bombay": "mumbai",
            "nouvelle-delhi": "new delhi",
            "delhi": "delhi",
            "bangalore": "bangalore",
            "dubaï": "dubai",
            "abou dhabi": "abu dhabi",
            "tel-aviv": "tel aviv",
            "jérusalem": "jerusalem",
            "le caire": "cairo",
            "johannesburg": "johannesburg",
            "le cap": "cape town",
            "sydney": "sydney",
            "melbourne": "melbourne",
            "auckland": "auckland",
            # Portuguese
            "nova york": "new york",
            "nova iorque": "new york",
            "são francisco": "san francisco",
            "los angeles": "los angeles",
            "chicago": "chicago",
            "miami": "miami",
            "londres": "london",
            "paris": "paris",
            "madri": "madrid",
            "barcelona": "barcelona",
            "roma": "rome",
            "milão": "milan",
            "berlim": "berlin",
            "munique": "munich",
            "frankfurt": "frankfurt",
            "amsterdã": "amsterdam",
            "bruxelas": "brussels",
            "viena": "vienna",
            "zurique": "zurich",
            "genebra": "geneva",
            "moscou": "moscow",
            "moscovo": "moscow",
            "são petersburgo": "saint petersburg",
            "istambul": "istanbul",
            "atenas": "athens",
            "lisboa": "lisbon",
            "porto": "porto",
            "dublin": "dublin",
            "edimburgo": "edinburgh",
            "copenhaga": "copenhagen",
            "estocolmo": "stockholm",
            "helsínquia": "helsinki",
            "varsóvia": "warsaw",
            "praga": "prague",
            "budapeste": "budapest",
            "bucareste": "bucharest",
            "belgrado": "belgrade",
            "zagrebe": "zagreb",
            "sófia": "sofia",
            "cidade do méxico": "mexico city",
            "cancún": "cancun",
            "buenos aires": "buenos aires",
            "rio de janeiro": "rio de janeiro",
            "lima": "lima",
            "bogotá": "bogota",
            "caracas": "caracas",
            "quito": "quito",
            "assunção": "asuncion",
            "montevideu": "montevideo",
            "santiago": "santiago",
            "havana": "havana",
            "santo domingo": "santo domingo",
            "cidade do panamá": "panama city",
            "san josé": "san jose",
            "manágua": "managua",
            "tegucigalpa": "tegucigalpa",
            "são salvador": "san salvador",
            "cidade da guatemala": "guatemala city",
            "pequim": "beijing",
            "xangai": "shanghai",
            "tóquio": "tokyo",
            "osaka": "osaka",
            "seul": "seoul",
            "banguecoque": "bangkok",
            "singapura": "singapore",
            "hong kong": "hong kong",
            "bombaim": "mumbai",
            "nova deli": "new delhi",
            "deli": "delhi",
            "bangalore": "bangalore",
            "dubai": "dubai",
            "abu dhabi": "abu dhabi",
            "telavive": "tel aviv",
            "jerusalém": "jerusalem",
            "cairo": "cairo",
            "joanesburgo": "johannesburg",
            "cidade do cabo": "cape town",
            "sydney": "sydney",
            "melbourne": "melbourne",
            "auckland": "auckland",
            # German
            "neu york": "new york",
            "new york": "new york",
            "los angeles": "los angeles",
            "san francisco": "san francisco",
            "chicago": "chicago",
            "miami": "miami",
            "london": "london",
            "paris": "paris",
            "madrid": "madrid",
            "barcelona": "barcelona",
            "rom": "rome",
            "mailand": "milan",
            "berlin": "berlin",
            "münchen": "munich",
            "frankfurt": "frankfurt",
            "amsterdam": "amsterdam",
            "brüssel": "brussels",
            "wien": "vienna",
            "zürich": "zurich",
            "genf": "geneva",
            "moskau": "moscow",
            "sankt petersburg": "saint petersburg",
            "istanbul": "istanbul",
            "athen": "athens",
            "lissabon": "lisbon",
            "dublin": "dublin",
            "edinburgh": "edinburgh",
            "kopenhagen": "copenhagen",
            "stockholm": "stockholm",
            "helsinki": "helsinki",
            "warschau": "warsaw",
            "prag": "prague",
            "budapest": "budapest",
            "bukarest": "bucharest",
            "belgrad": "belgrade",
            "zagreb": "zagreb",
            "sofia": "sofia",
            "mexiko-stadt": "mexico city",
            "cancún": "cancun",
            "buenos aires": "buenos aires",
            "são paulo": "sao paulo",
            "rio de janeiro": "rio de janeiro",
            "lima": "lima",
            "bogotá": "bogota",
            "caracas": "caracas",
            "quito": "quito",
            "asunción": "asuncion",
            "montevideo": "montevideo",
            "santiago": "santiago",
            "havanna": "havana",
            "santo domingo": "santo domingo",
            "panama-stadt": "panama city",
            "san josé": "san jose",
            "managua": "managua",
            "tegucigalpa": "tegucigalpa",
            "san salvador": "san salvador",
            "guatemala-stadt": "guatemala city",
            "peking": "beijing",
            "shanghai": "shanghai",
            "tokio": "tokyo",
            "osaka": "osaka",
            "seoul": "seoul",
            "bangkok": "bangkok",
            "singapur": "singapore",
            "hongkong": "hong kong",
            "mumbai": "mumbai",
            "neu-delhi": "new delhi",
            "delhi": "delhi",
            "bangalore": "bangalore",
            "dubai": "dubai",
            "abu dhabi": "abu dhabi",
            "tel aviv": "tel aviv",
            "jerusalem": "jerusalem",
            "kairo": "cairo",
            "johannesburg": "johannesburg",
            "kapstadt": "cape town",
            "sydney": "sydney",
            "melbourne": "melbourne",
            "auckland": "auckland",
            # Italian
            "nuova york": "new york",
            "los angeles": "los angeles",
            "san francisco": "san francisco",
            "chicago": "chicago",
            "miami": "miami",
            "londra": "london",
            "parigi": "paris",
            "madrid": "madrid",
            "barcellona": "barcelona",
            "roma": "rome",
            "milano": "milan",
            "berlino": "berlin",
            "monaco": "munich",
            "francoforte": "frankfurt",
            "amsterdam": "amsterdam",
            "bruxelles": "brussels",
            "vienna": "vienna",
            "zurigo": "zurich",
            "ginevra": "geneva",
            "mosca": "moscow",
            "san pietroburgo": "saint petersburg",
            "istanbul": "istanbul",
            "atene": "athens",
            "lisbona": "lisbon",
            "dublino": "dublin",
            "edimburgo": "edinburgh",
            "copenaghen": "copenhagen",
            "stoccolma": "stockholm",
            "helsinki": "helsinki",
            "varsavia": "warsaw",
            "praga": "prague",
            "budapest": "budapest",
            "bucarest": "bucharest",
            "belgrado": "belgrade",
            "zagabria": "zagreb",
            "sofia": "sofia",
            "città del messico": "mexico city",
            "cancún": "cancun",
            "buenos aires": "buenos aires",
            "san paolo": "sao paulo",
            "rio de janeiro": "rio de janeiro",
            "lima": "lima",
            "bogotà": "bogota",
            "caracas": "caracas",
            "quito": "quito",
            "asunción": "asuncion",
            "montevideo": "montevideo",
            "santiago": "santiago",
            "l'avana": "havana",
            "santo domingo": "santo domingo",
            "città di panama": "panama city",
            "san josé": "san jose",
            "managua": "managua",
            "tegucigalpa": "tegucigalpa",
            "san salvador": "san salvador",
            "città del guatemala": "guatemala city",
            "pechino": "beijing",
            "shanghai": "shanghai",
            "tokyo": "tokyo",
            "osaka": "osaka",
            "seul": "seoul",
            "bangkok": "bangkok",
            "singapore": "singapore",
            "hong kong": "hong kong",
            "mumbai": "mumbai",
            "nuova delhi": "new delhi",
            "delhi": "delhi",
            "bangalore": "bangalore",
            "dubai": "dubai",
            "abu dhabi": "abu dhabi",
            "tel aviv": "tel aviv",
            "gerusalemme": "jerusalem",
            "il cairo": "cairo",
            "johannesburg": "johannesburg",
            "città del capo": "cape town",
            "sydney": "sydney",
            "melbourne": "melbourne",
            "auckland": "auckland",
            # Chinese (pinyin)
            "niuyue": "new york",
            "luoshanji": "los angeles",
            "jiujinshan": "san francisco",
            "zhijiage": "chicago",
            "maiami": "miami",
            "lundun": "london",
            "bali": "paris",
            "madeli": "madrid",
            "basailuona": "barcelona",
            "luoma": "rome",
            "milan": "milan",
            "bailin": "berlin",
            "munihei": "munich",
            "falankefu": "frankfurt",
            "amusitedan": "amsterdam",
            "buluxisai": "brussels",
            "weiyena": "vienna",
            "sulishi": "zurich",
            "rineiwa": "geneva",
            "mosike": "moscow",
            "shengbidebao": "saint petersburg",
            "yisitanbuer": "istanbul",
            "yadian": "athens",
            "lisiben": "lisbon",
            "dubolin": "dublin",
            "aidingbao": "edinburgh",
            "gebenhagen": "copenhagen",
            "sigededemo": "stockholm",
            "heerxinji": "helsinki",
            "huasha": "warsaw",
            "bulage": "prague",
            "budapeis": "budapest",
            "bujialesite": "bucharest",
            "beigelaide": "belgrade",
            "sagelubu": "zagreb",
            "suofiya": "sofia",
            "moxigecheng": "mexico city",
            "kankun": "cancun",
            "buluosiailisi": "buenos aires",
            "shengbaoluo": "sao paulo",
            "liyueneilu": "rio de janeiro",
            "lima": "lima",
            "bogeda": "bogota",
            "jialajiasi": "caracas",
            "jiduo": "quito",
            "yasong": "asuncion",
            "mengdeweideya": "montevideo",
            "shengdiyage": "santiago",
            "hawana": "havana",
            "shengduomingge": "santo domingo",
            "banama": "panama city",
            "shenghuose": "san jose",
            "managua": "managua",
            "teguxijiaerba": "tegucigalpa",
            "shengzawaduo": "san salvador",
            "weidimala": "guatemala city",
            "beijing": "beijing",
            "shanghai": "shanghai",
            "dongjing": "tokyo",
            "daban": "osaka",
            "hancheng": "seoul",
            "mangu": "bangkok",
            "xinjiapo": "singapore",
            "xianggang": "hong kong",
            "mengmai": "mumbai",
            "xindeli": "new delhi",
            "deli": "delhi",
            "banjialeuer": "bangalore",
            "dibai": "dubai",
            "abuzhabi": "abu dhabi",
            "telaweifu": "tel aviv",
            "yelusaleng": "jerusalem",
            "kailuo": "cairo",
            "yuehanneisibao": "johannesburg",
            "kaipudun": "cape town",
            "xini": "sydney",
            "moerben": "melbourne",
            "aokelan": "auckland"
        }
        
        # Airport code mapping for common cities
        self.airport_codes = {
            "new york": ["JFK", "LGA", "EWR"],
            "london": ["LHR", "LGW", "STN"],
            "paris": ["CDG", "ORY"],
            "tokyo": ["NRT", "HND"],
            "los angeles": ["LAX"],
            "san francisco": ["SFO"],
            "chicago": ["ORD", "MDW"],
            "miami": ["MIA"],
            "madrid": ["MAD"],
            "barcelona": ["BCN"],
            "rome": ["FCO"],
            "berlin": ["BER"],
            "amsterdam": ["AMS"],
            "dubai": ["DXB"],
            "singapore": ["SIN"],
            "hong kong": ["HKG"],
            "sydney": ["SYD"],
            "toronto": ["YYZ"],
            "mexico city": ["MEX"],
            "são paulo": ["GRU"],
            "buenos aires": ["EZE"],
        }
    
    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        passengers: int = 1,
        cabin_class: str = "economy",
        currency: str = "USD",
        preferred_airline: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for flights - Run multiple APIs in parallel to enrich results"""
        try:
            # Convert city names to airport codes if needed
            origin_code = await self.get_airport_code(origin)
            dest_code = await self.get_airport_code(destination)
            
            logger.info(f"Searching flights: {origin_code} -> {dest_code} on {departure_date}, preferred airline: {preferred_airline}, class: {cabin_class}")
            
            # Run APIs in parallel to get comprehensive results
            tasks = []
            
            # Always try Amadeus
            tasks.append(self._search_with_timeout(
                self.amadeus_search.search_flights(
                    origin_code, dest_code, departure_date,
                    return_date, passengers, 0, cabin_class.upper(), currency
                ),
                "Amadeus",
                timeout=10.0
            ))
            
            # AviationStack removed - not working properly
            
            # Try Serper.dev for Google search
            if self.serper_key:
                tasks.append(self._search_with_timeout(
                    self._search_flights_serper(
                        origin_code, dest_code, departure_date,
                        preferred_airline, passengers, cabin_class
                    ),
                    "Serper",
                    timeout=8.0
                ))
            
            # Always try SerpAPI for better coverage (if we have a valid key)
            if self.serpapi_key and self.serpapi_key != self.serper_key:
                tasks.append(self._search_with_timeout(
                    self._search_flights_serpapi(
                        origin_code, dest_code, departure_date,
                        return_date, passengers, cabin_class, currency
                    ),
                    "SerpAPI",
                    timeout=8.0
                ))
            
            # Browserless.io removed - not working properly
            
            # Run all searches in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Merge results from all sources
            all_flights = []
            for i, result in enumerate(results):
                if isinstance(result, list) and result:
                    # Map index to source based on order of tasks
                    source_mapping = {
                        0: "Amadeus",
                        1: "Serper",
                        2: "SerpAPI"
                    }
                    source = source_mapping.get(i, "Unknown")
                    logger.info(f"{source} returned {len(result)} flights")
                    # Add source to each flight
                    for flight in result:
                        flight['data_source'] = source
                    all_flights.extend(result)
                elif isinstance(result, Exception):
                    logger.warning(f"API error: {result}")
            
            # Remove duplicates and enrich data
            enriched_flights = self._merge_and_enrich_flights(all_flights)
            
            # Filter by airline if requested
            if preferred_airline:
                airline_flights = self._filter_by_airline(enriched_flights, preferred_airline)
                
                if airline_flights:
                    # Found the requested airline
                    logger.info(f"Found {len(airline_flights)} {preferred_airline} flights")
                    return airline_flights
                else:
                    # Airline not found - return all flights but note the preference
                    logger.info(f"No {preferred_airline} flights found, returning all {len(enriched_flights)} options")
                    # Add a note to the first few flights about airline not found
                    for flight in enriched_flights[:3]:
                        flight['note'] = f"Note: {preferred_airline} not available on this route"
                    return enriched_flights
            
            return enriched_flights
                
        except Exception as e:
            logger.error(f"Error searching flights: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _search_with_timeout(self, coro, source_name: str, timeout: float) -> List[Dict[str, Any]]:
        """Run a search coroutine with timeout"""
        try:
            result = await asyncio.wait_for(coro, timeout=timeout)
            logger.info(f"{source_name} completed successfully")
            return result
        except asyncio.TimeoutError:
            logger.warning(f"{source_name} timed out after {timeout}s")
            return []
        except Exception as e:
            logger.error(f"{source_name} error: {e}")
            return []
    
    def _merge_and_enrich_flights(self, all_flights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge flights from multiple sources and remove duplicates"""
        # Create a unique identifier for each flight
        seen_flights = {}
        enriched = []
        
        for flight in all_flights:
            # Skip "Multiple airlines" results which are typically aggregator results
            if flight.get('airline', '').lower() == 'multiple airlines':
                continue
            # Create a unique key based on flight number, departure time, or airline+times
            flight_key = None
            
            # Try to use flight number as primary key
            if flight.get('flight_number'):
                flight_key = f"{flight['flight_number']}_{flight.get('departure_time', '')}"
            # Fallback to airline + times
            elif flight.get('airline') and flight.get('departure_time'):
                flight_key = f"{flight['airline']}_{flight['departure_time']}_{flight.get('arrival_time', '')}"
            
            if flight_key:
                if flight_key not in seen_flights:
                    # First time seeing this flight
                    seen_flights[flight_key] = flight
                    enriched.append(flight)
                else:
                    # Merge data from different sources
                    existing = seen_flights[flight_key]
                    # Prefer data from more reliable sources
                    if flight.get('data_source') == 'Amadeus' and existing.get('data_source') != 'Amadeus':
                        # Amadeus data is usually most complete
                        existing.update({k: v for k, v in flight.items() if v and not existing.get(k)})
                    elif flight.get('data_source') == 'SerpAPI':
                        # SerpAPI might have better pricing
                        if flight.get('price') and not existing.get('price'):
                            existing['price'] = flight['price']
            else:
                # No unique key, just add it
                enriched.append(flight)
        
        # Sort by departure time and price
        def get_price_value(flight):
            price = str(flight.get('price', '999999'))
            # Extract numeric value from price string
            price_num = re.sub(r'[^\d.]', '', price)
            # Handle empty strings or non-numeric prices
            try:
                return float(price_num) if price_num else 999999
            except ValueError:
                return 999999
        
        enriched.sort(key=lambda f: (
            f.get('departure_time', 'ZZZ'),
            get_price_value(f)
        ))
        
        return enriched
    
    async def get_airport_code(self, city: str) -> str:
        """Convert city name to airport code"""
        city_lower = city.lower().strip()
        
        # Check if it's already an airport code (3 letters)
        if len(city) == 3 and city.isupper():
            return city
        
        # Look up in our mapping
        for city_name, codes in self.airport_codes.items():
            if city_lower in city_name or city_name in city_lower:
                return codes[0]  # Return primary airport
        
        # If not found, try to search online
        if self.serpapi_key:
            return await self._search_airport_code_online(city)
        
        # Default: return the input uppercased
        return city.upper()[:3]
    
    async def get_flight_details(self, flight_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific flight"""
        # Return minimal info - real-time flight tracking requires paid APIs
        return {
            "flight_id": flight_id,
            "error": "Unable to retrieve live flight details",
            "note": "Please check with the airline for current flight status"
        }
    
    async def _search_flights_serper(
        self, origin: str, destination: str, departure_date: str,
        airline: Optional[str], passengers: int, cabin_class: str
    ) -> List[Dict[str, Any]]:
        """Search flights using Serper.dev Google Search API"""
        try:
            # Build search query
            query_parts = [
                f"flights from {origin} to {destination}",
                f"on {departure_date}",
                cabin_class if cabin_class != "economy" else "",
                f"{airline} airlines" if airline else "",
                "prices schedule"
            ]
            query = " ".join(filter(None, query_parts))
            
            logger.info(f"Searching with Serper.dev: {query}")
            
            # Serper.dev API endpoint
            url = "https://google.serper.dev/search"
            
            headers = {
                "X-API-KEY": self.serper_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "q": query,
                "num": 20,
                "gl": "us",
                "hl": "en"
            }
            
            response = await self.http_client.post(
                url,
                json=payload,
                headers=headers,
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_serper_results(data, origin, destination, departure_date, airline)
            else:
                logger.error(f"Serper error: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Serper search error: {e}")
            return []
    
    def _parse_serper_results(self, data: Dict, origin: str, destination: str, date: str, airline: Optional[str]) -> List[Dict[str, Any]]:
        """Parse Serper.dev search results for flight information"""
        flights = []
        
        try:
            # Check organic results for flight information
            organic = data.get("organic", [])
            
            for result in organic[:10]:
                title = result.get("title", "").lower()
                snippet = result.get("snippet", "")
                link = result.get("link", "")
                
                # Look for flight-related results
                if any(word in title for word in ["flight", "airline", "travel", "cheap", "book"]):
                    # Try to extract price from snippet
                    import re
                    price_match = re.search(r'\$(\d+(?:,\d+)?)', snippet)
                    price = f"${price_match.group(1)}" if price_match else "Check website"
                    
                    # Extract airline if mentioned
                    flight_airline = "Multiple Airlines"
                    for known_airline in ["Delta", "United", "American", "Southwest", "JetBlue", "Alaska", "Spirit", "Frontier"]:
                        if known_airline.lower() in snippet.lower():
                            flight_airline = known_airline + " Airlines"
                            break
                    
                    # Skip if we're filtering by airline and this doesn't match
                    if airline and airline.lower() not in flight_airline.lower():
                        continue
                    
                    flight = {
                        "airline": flight_airline,
                        "price": price,
                        "departure_airport": origin,
                        "arrival_airport": destination,
                        "departure_date": date,
                        "source": "Google Search (via Serper)",
                        "data_source": "Serper",
                        "booking_link": link,
                        "description": snippet[:200]
                    }
                    flights.append(flight)
            
            # Also check answer box if available
            answer_box = data.get("answerBox", {})
            if answer_box:
                answer = answer_box.get("answer", "")
                if "$" in answer:
                    flights.insert(0, {
                        "airline": "Various Airlines",
                        "price": answer,
                        "departure_airport": origin,
                        "arrival_airport": destination,
                        "departure_date": date,
                        "source": "Google Answer Box (via Serper)",
                        "description": "Best price found"
                    })
            
            logger.info(f"Parsed {len(flights)} flights from Serper results")
            return flights
            
        except Exception as e:
            logger.error(f"Error parsing Serper results: {e}")
            return []
    
    async def _search_flights_serpapi(
        self, origin: str, destination: str, departure_date: str,
        return_date: Optional[str], passengers: int, cabin_class: str,
        currency: str
    ) -> List[Dict[str, Any]]:
        """Search flights using SerpAPI Google Flights"""
        params = {
            "api_key": self.serpapi_key,
            "engine": "google_flights",
            "departure_id": origin,
            "arrival_id": destination,
            "outbound_date": departure_date,
            "currency": currency,
            "adults": passengers,
            "travel_class": cabin_class
        }
        
        if return_date:
            params["return_date"] = return_date
            params["type"] = "2"  # Round trip
        else:
            params["type"] = "1"  # One way
        
        logger.info(f"Calling SerpAPI with params: {params}")
        
        response = await self.http_client.get(
            "https://serpapi.com/search",
            params=params
        )
        
        if response.status_code == 200:
            data = response.json()
            return self._parse_serpapi_results(data)
        else:
            logger.error(f"SerpAPI error: {response.status_code} - {response.text}")
            raise Exception(f"SerpAPI error: {response.status_code}")
    
    
    def _parse_serpapi_results(self, data: Dict) -> List[Dict[str, Any]]:
        """Parse SerpAPI Google Flights results into standard format"""
        flights = []
        
        # SerpAPI returns different structures for one-way vs round-trip
        flight_sections = []
        
        # Check for best flights
        if "best_flights" in data:
            flight_sections.extend(data["best_flights"])
        
        # Check for other flights
        if "other_flights" in data:
            flight_sections.extend(data["other_flights"])
            
        for flight_option in flight_sections:
            try:
                # Handle the flights array (each option may have multiple segments)
                flights_info = flight_option.get("flights", [])
                
                if flights_info:
                    # Get first flight segment for basic info
                    first_segment = flights_info[0]
                    
                    # Extract departure and arrival info
                    departure_airport = first_segment.get("departure_airport", {})
                    arrival_airport = flights_info[-1].get("arrival_airport", {})  # Last segment for final arrival
                    
                    # Build flight record
                    flight_record = {
                        "airline": ", ".join([f.get("airline", "Unknown") for f in flights_info]),
                        "flight_number": ", ".join([f.get("flight_number", "") for f in flights_info if f.get("flight_number")]),
                        "departure_time": departure_airport.get("time", ""),
                        "departure_airport": f"{departure_airport.get('name', '')} ({departure_airport.get('id', '')})",
                        "arrival_time": arrival_airport.get("time", ""),
                        "arrival_airport": f"{arrival_airport.get('name', '')} ({arrival_airport.get('id', '')})",
                        "duration": flight_option.get("total_duration", ""),
                        "price": flight_option.get("price", ""),
                        "stops": len(flights_info) - 1,  # Number of stops
                        "layovers": [f.get("arrival_airport", {}).get("name", "") for f in flights_info[:-1]],
                        "carbon_emissions": flight_option.get("carbon_emissions", {}).get("this_flight", ""),
                        "booking_token": flight_option.get("booking_token", ""),
                        "type": flight_option.get("type", ""),
                        "airline_logos": [f.get("airline_logo", "") for f in flights_info]
                    }
                    
                    flights.append(flight_record)
                    
            except Exception as e:
                logger.debug(f"Error parsing flight option: {e}")
                continue
        
        logger.info(f"Found {len(flights)} flights from SerpAPI")
        return flights
    
    
    async def _get_real_time_prices(self, origin: str, destination: str, date: str, passengers: int = 1) -> Optional[Dict[str, Any]]:
        """Try to get real-time flight prices from SerpAPI"""
        if not self.serpapi_key:
            return None
            
        try:
            params = {
                "api_key": self.serpapi_key,
                "engine": "google_flights",
                "departure_id": origin,
                "arrival_id": destination,
                "outbound_date": date,
                "adults": passengers,
                "currency": "USD",
                "hl": "en"
            }
            
            response = await self.http_client.get(
                "https://serpapi.com/search",
                params=params
            )
            
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.debug(f"Failed to get real-time prices: {e}")
        
        return None
    
    def _calculate_duration(self, departure: str, arrival: str) -> str:
        """Calculate flight duration from departure and arrival times"""
        try:
            dep_time = datetime.fromisoformat(departure.replace("Z", "+00:00"))
            arr_time = datetime.fromisoformat(arrival.replace("Z", "+00:00"))
            duration = arr_time - dep_time
            
            hours = int(duration.total_seconds() // 3600)
            minutes = int((duration.total_seconds() % 3600) // 60)
            
            return f"{hours}h {minutes}m"
        except:
            return "N/A"
    
    def _format_datetime(self, dt_str: str) -> str:
        """Format datetime string to readable format"""
        try:
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            return dt.strftime("%H:%M")
        except:
            return dt_str
    
    async def _get_mock_flights(
        self, origin: str, destination: str, departure_date: str,
        return_date: Optional[str], passengers: int, cabin_class: str
    ) -> List[Dict[str, Any]]:
        """Get real flight data from known routes or generate realistic mock data"""
        # First try to get real flight data
        try:
            real_flights = await get_real_flights(origin, destination, departure_date)
            if real_flights:
                # Filter by cabin class if needed
                if cabin_class == "business":
                    # Adjust prices for business class
                    for flight in real_flights:
                        # Convert economy to business prices (roughly 3-4x)
                        if "$" in flight.get("price", ""):
                            price_str = flight["price"].replace("$", "").replace(",", "")
                            try:
                                price = int(price_str)
                                flight["price"] = f"${price * 3:,}"
                                flight["cabin_class"] = "business"
                            except:
                                pass
                logger.info(f"Using real flight data: {len(real_flights)} flights")
                return real_flights
        except Exception as e:
            logger.debug(f"Could not get real flight data: {e}")
        
        # Fallback to realistic mock data
        airlines = ["United", "American", "Delta", "JetBlue", "Southwest"]
        base_price = 450 if cabin_class == "economy" else 1800
        
        flights = []
        for i, airline in enumerate(airlines[:3]):
            departure_time = f"{departure_date}T{8+i*2:02d}:00:00"
            arrival_time = f"{departure_date}T{18+i*2:02d}:30:00"
            
            flights.append({
                "airline": f"{airline} Airlines",
                "flight_number": f"{airline[:2].upper()}{100+i}",
                "departure_time": departure_time,
                "arrival_time": arrival_time,
                "duration": f"{10+i}h 30m",
                "price": f"${base_price + i*100:,}",
                "stops": 0 if i == 0 else 1,
                "departure_airport": f"{origin} International",
                "arrival_airport": f"{destination} International",
                "note": "Schedule subject to change",
                "booking_link": f"https://{airline.lower()}.com/flights"
            })
        
        logger.info(f"Generated {len(flights)} realistic mock flights")
        return flights
    
    async def _search_airport_code_online(self, city: str) -> str:
        """Search for airport code online using APIs"""
        # Try AviationStack first
        if self.aviationstack_key:
            try:
                # AviationStack doesn't have a direct city-to-airport endpoint,
                # but we can search for airports by country/city name
                logger.debug(f"Searching for airport code for: {city}")
            except Exception as e:
                logger.debug(f"AviationStack airport search failed: {e}")
        
        # Try SerpAPI as fallback
        if self.serpapi_key:
            try:
                # Method 1: Try Google Flights autocomplete
                params = {
                    "api_key": self.serpapi_key,
                    "engine": "google_flights",
                    "hl": "en",
                    "gl": "us",
                    "departure_id": city,  # This triggers autocomplete
                    "arrival_id": "LAX",   # Dummy destination
                    "outbound_date": "2024-12-01",  # Dummy date
                    "currency": "USD"
                }
                
                response = await self.http_client.get(
                    "https://serpapi.com/search",
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Check if we got airport suggestions
                    if "error" not in data:
                        # The API often auto-corrects city names to airport codes
                        logger.debug(f"Found airport code via Google Flights")
                        # Return the first valid result
                        
                # Method 2: Regular search as fallback
                params = {
                    "api_key": self.serpapi_key,
                    "q": f"{city} airport IATA code",
                    "num": 1
                }
                
                response = await self.http_client.get(
                    "https://serpapi.com/search",
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Try to extract from answer box
                    if "answer_box" in data:
                        answer = data["answer_box"].get("answer", "")
                        # Look for 3-letter IATA code pattern
                        matches = re.findall(r'\b[A-Z]{3}\b', answer)
                        if matches:
                            # Filter out common non-airport codes
                            for match in matches:
                                if match not in ["THE", "AND", "FOR", "ARE", "CAN", "HAS"]:
                                    logger.info(f"Found airport code {match} for {city}")
                                    return match
                    
                    # Try organic results
                    if "organic_results" in data:
                        for result in data["organic_results"][:3]:
                            snippet = result.get("snippet", "")
                            # Look for IATA code pattern
                            matches = re.findall(r'(?:IATA:?\s*|code:?\s*)([A-Z]{3})', snippet, re.IGNORECASE)
                            if matches:
                                code = matches[0].upper()
                                logger.info(f"Found airport code {code} for {city} in search results")
                                return code
                                
            except Exception as e:
                logger.warning(f"Online airport search failed: {e}")
        
        # Last resort: return first 3 letters uppercase
        fallback = city.upper()[:3]
        logger.warning(f"Could not find airport code for '{city}', using fallback: {fallback}")
        return fallback
    
    def _filter_by_airline(self, flights: List[Dict[str, Any]], airline: str) -> List[Dict[str, Any]]:
        """Filter flights by airline name"""
        airline_lower = airline.lower()
        filtered = []
        
        # Common airline name variations
        airline_aliases = {
            # US Airlines
            "american": ["american airlines", "aa"],
            "united": ["united airlines", "ua"],
            "delta": ["delta air lines", "delta airlines", "dl"],
            "southwest": ["southwest airlines", "wn"],
            "jetblue": ["jetblue airways", "b6"],
            "alaska": ["alaska airlines", "as"],
            "spirit": ["spirit airlines", "nk"],
            "frontier": ["frontier airlines", "f9"],
            # European Airlines
            "iberia": ["iberia airlines", "ib"],
            "british airways": ["british", "ba"],
            "lufthansa": ["lh"],
            "air france": ["af"],
            "klm": ["klm royal dutch airlines", "kl"],
            "ryanair": ["fr"],
            "easyjet": ["easy jet", "u2"],
            "swiss": ["swiss international", "swiss air", "lx"],
            "tap": ["tap air portugal", "tap portugal", "tp"],
            # Latin American Airlines
            "avianca": ["av"],
            "latam": ["latam airlines", "la"],
            "aeromexico": ["aeroméxico", "am"],
            "copa": ["copa airlines", "cm"],
            "gol": ["gol linhas aéreas", "g3"],
            "azul": ["azul brazilian airlines", "ad"],
            # Middle Eastern Airlines
            "emirates": ["ek"],
            "qatar": ["qatar airways", "qr"],
            "etihad": ["etihad airways", "ey"],
            "turkish": ["turkish airlines", "tk"],
            # Asian Airlines
            "singapore": ["singapore airlines", "sq"],
            "cathay": ["cathay pacific", "cx"],
            "ana": ["all nippon airways", "nh"],
            "jal": ["japan airlines", "jl"],
            "korean": ["korean air", "ke"],
            "asiana": ["oz"],
            # Others
            "air canada": ["ac"],
            "qantas": ["qf"],
            "air new zealand": ["nz"],
            "virgin": ["virgin atlantic", "virgin australia", "vs", "va"]
        }
        
        # Get all possible names for the requested airline
        possible_names = [airline_lower]
        for key, aliases in airline_aliases.items():
            if airline_lower in key or key in airline_lower:
                possible_names.extend(aliases)
            for alias in aliases:
                if airline_lower in alias or alias in airline_lower:
                    possible_names.append(key)
                    possible_names.extend(aliases)
        
        # Remove duplicates
        possible_names = list(set(possible_names))
        
        for flight in flights:
            flight_airline = flight.get('airline', '').lower()
            flight_code = flight.get('airline_code', '').lower()
            
            # Check against all possible names
            for name in possible_names:
                if name in flight_airline or flight_airline in name or flight_code == name:
                    filtered.append(flight)
                    break
        
        return filtered
    
    
    

# Create server instance
server = FlightSearchServer()

# API endpoints
@app.get("/")
async def root():
    return {"message": "Flight Search API", "version": "1.0.0"}

@app.post("/search_flights")
async def search_flights(request: FlightSearchRequest):
    """Search for flights"""
    flights = await server.search_flights(
        origin=request.origin,
        destination=request.destination,
        departure_date=request.departure_date,
        return_date=request.return_date,
        passengers=request.passengers,
        cabin_class=request.cabin_class,
        currency=request.currency
    )
    return {"flights": flights, "count": len(flights)}

@app.get("/airport_code/{city}")
async def get_airport_code(city: str):
    """Get airport code for a city"""
    code = await server.get_airport_code(city)
    return {"city": city, "airport_code": code}

@app.get("/flight/{flight_id}")
async def get_flight_details(flight_id: str):
    """Get flight details"""
    details = await server.get_flight_details(flight_id)
    return details

if __name__ == "__main__":
    port = int(os.getenv("FLIGHT_API_PORT", 8765))
    logger.info(f"Starting Flight Search API on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)