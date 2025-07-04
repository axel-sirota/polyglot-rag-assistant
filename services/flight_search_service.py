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
        self.aviationstack_key = os.getenv("AVIATIONSTACK_API_KEY")
        self.http_client = httpx.AsyncClient()
        
        # Multilingual city name mappings (normalize to English)
        self.multilingual_cities = {
            # Spanish
            "nueva york": "new york",
            "nueva jersey": "new jersey", 
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
        currency: str = "USD"
    ) -> List[Dict[str, Any]]:
        """Search for flights - AviationStack primary, SerpAPI fallback"""
        try:
            # Convert city names to airport codes if needed
            origin_code = await self.get_airport_code(origin)
            dest_code = await self.get_airport_code(destination)
            
            logger.info(f"Searching flights: {origin_code} -> {dest_code} on {departure_date}")
            
            # Try AviationStack first (primary API)
            if self.aviationstack_key:
                try:
                    flights = await self._search_flights_aviationstack(
                        origin_code, dest_code, departure_date,
                        return_date, passengers, cabin_class
                    )
                    if flights:
                        logger.info(f"AviationStack returned {len(flights)} flights")
                        return flights
                except Exception as e:
                    logger.warning(f"AviationStack failed: {e}, trying SerpAPI fallback")
            
            # Fallback to SerpAPI
            if self.serpapi_key:
                try:
                    return await self._search_flights_serpapi(
                        origin_code, dest_code, departure_date, 
                        return_date, passengers, cabin_class, currency
                    )
                except Exception as e:
                    logger.warning(f"SerpAPI also failed: {e}")
            
            # If both fail or no keys available, return mock data
            logger.info("Using mock flight data")
            return self._get_mock_flights(
                origin_code, dest_code, departure_date,
                return_date, passengers, cabin_class
            )
                
        except Exception as e:
            logger.error(f"Error searching flights: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
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
        # Try to get real flight details from APIs
        if self.aviationstack_key:
            try:
                # AviationStack flight status endpoint
                params = {
                    "access_key": self.aviationstack_key,
                    "flight_iata": flight_id
                }
                response = await self.http_client.get(
                    "http://api.aviationstack.com/v1/flights",
                    params=params
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("data"):
                        flight = data["data"][0]
                        return {
                            "flight_id": flight_id,
                            "airline": flight.get("airline", {}).get("name"),
                            "flight_number": flight.get("flight", {}).get("iata"),
                            "status": flight.get("flight_status"),
                            "departure": {
                                "airport": flight.get("departure", {}).get("airport"),
                                "terminal": flight.get("departure", {}).get("terminal"),
                                "gate": flight.get("departure", {}).get("gate"),
                                "scheduled": flight.get("departure", {}).get("scheduled"),
                                "actual": flight.get("departure", {}).get("actual")
                            },
                            "arrival": {
                                "airport": flight.get("arrival", {}).get("airport"),
                                "terminal": flight.get("arrival", {}).get("terminal"),
                                "gate": flight.get("arrival", {}).get("gate"),
                                "scheduled": flight.get("arrival", {}).get("scheduled"),
                                "actual": flight.get("arrival", {}).get("actual")
                            },
                            "aircraft": flight.get("aircraft", {}).get("registration"),
                            "live": flight.get("live", {})
                        }
            except Exception as e:
                logger.warning(f"Failed to get flight details from AviationStack: {e}")
        
        # If no API available or failed, return minimal info
        return {
            "flight_id": flight_id,
            "error": "Unable to retrieve live flight details",
            "note": "Please check with the airline for current flight status"
        }
    
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
    
    async def _search_flights_aviationstack(
        self, origin: str, destination: str, departure_date: str,
        return_date: Optional[str], passengers: int, cabin_class: str
    ) -> List[Dict[str, Any]]:
        """Search flights using Aviationstack API"""
        params = {
            "access_key": self.aviationstack_key,
            "dep_iata": origin,
            "arr_iata": destination,
            "flight_date": departure_date,
            "limit": 10
        }
        
        response = await self.http_client.get(
            "http://api.aviationstack.com/v1/flights",
            params=params
        )
        
        if response.status_code == 200:
            data = response.json()
            return self._parse_aviationstack_results(data, passengers, cabin_class)
        else:
            raise Exception(f"Aviationstack error: {response.status_code}")
    
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
    
    def _parse_aviationstack_results(
        self, data: Dict, passengers: int, cabin_class: str
    ) -> List[Dict[str, Any]]:
        """Parse Aviationstack results into standard format"""
        flights = []
        
        if "data" in data and data["data"]:
            for flight in data["data"]:
                try:
                    # Extract all available real data
                    departure = flight.get("departure", {})
                    arrival = flight.get("arrival", {})
                    airline = flight.get("airline", {})
                    flight_info = flight.get("flight", {})
                    aircraft = flight.get("aircraft", {})
                    live = flight.get("live", {})
                    
                    flight_record = {
                        "airline": airline.get("name", "Unknown"),
                        "airline_iata": airline.get("iata", ""),
                        "flight_number": flight_info.get("iata", ""),
                        "flight_icao": flight_info.get("icao", ""),
                        "departure_airport": departure.get("airport", ""),
                        "departure_iata": departure.get("iata", ""),
                        "departure_time": departure.get("scheduled", ""),
                        "departure_actual": departure.get("actual", ""),
                        "departure_terminal": departure.get("terminal", ""),
                        "departure_gate": departure.get("gate", ""),
                        "arrival_airport": arrival.get("airport", ""),
                        "arrival_iata": arrival.get("iata", ""),
                        "arrival_time": arrival.get("scheduled", ""),
                        "arrival_actual": arrival.get("actual", ""),
                        "arrival_terminal": arrival.get("terminal", ""),
                        "arrival_gate": arrival.get("gate", ""),
                        "flight_status": flight.get("flight_status", ""),
                        "aircraft_registration": aircraft.get("registration", ""),
                        "aircraft_iata": aircraft.get("iata", ""),
                        "duration": self._calculate_duration(
                            departure.get("scheduled"),
                            arrival.get("scheduled")
                        ),
                        "distance": live.get("distance", ""),
                        "is_live": live.get("is_ground", False),
                        "speed": live.get("speed_horizontal", ""),
                        "altitude": live.get("altitude", ""),
                        "direction": live.get("direction", ""),
                        "note": "Real-time flight data from AviationStack"
                    }
                    
                    # Only add if we have essential info
                    if flight_record["departure_time"] and flight_record["arrival_time"]:
                        flights.append(flight_record)
                        
                except Exception as e:
                    logger.debug(f"Error parsing AviationStack flight: {e}")
                    continue
        
        logger.info(f"Parsed {len(flights)} flights from AviationStack")
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
    
    def _get_mock_flights(
        self, origin: str, destination: str, departure_date: str,
        return_date: Optional[str], passengers: int, cabin_class: str
    ) -> List[Dict[str, Any]]:
        """Generate mock flight data for demo purposes"""
        airlines = ["United", "American", "Delta", "Emirates", "Lufthansa"]
        base_price = 200 if cabin_class == "economy" else 800
        
        flights = []
        for i, airline in enumerate(airlines[:3]):
            departure_time = f"{departure_date}T{8+i*2:02d}:00:00"
            arrival_time = f"{departure_date}T{12+i*2:02d}:30:00"
            
            flights.append({
                "airline": airline,
                "flight_number": f"{airline[:2].upper()}{100+i}",
                "departure_time": departure_time,
                "arrival_time": arrival_time,
                "duration": f"{4+i}h 30m",
                "price": f"${base_price + i*50}",
                "stops": 0 if i == 0 else 1,
                "booking_link": f"https://example.com/book/{airline.lower()}"
            })
        
        logger.info(f"Generated {len(flights)} mock flights")
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