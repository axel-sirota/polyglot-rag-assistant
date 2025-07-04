from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import os
import json
import asyncio
from dotenv import load_dotenv

load_dotenv()

class FlightSearchServer:
    def __init__(self):
        self.server = Server("flight-search")
        self.serpapi_key = os.getenv("SERPAPI_API_KEY")
        self.aviationstack_key = os.getenv("AVIATIONSTACK_API_KEY")
        self.http_client = httpx.AsyncClient()
        self.setup_tools()
        
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
    
    def setup_tools(self):
        @self.server.tool()
        async def search_flights(
            origin: str,
            destination: str,
            departure_date: str,
            return_date: Optional[str] = None,
            passengers: int = 1,
            cabin_class: str = "economy",
            currency: str = "USD"
        ) -> List[Dict[str, Any]]:
            """
            Search for flights between origin and destination.
            
            Args:
                origin: Origin airport code or city name
                destination: Destination airport code or city name
                departure_date: Departure date in YYYY-MM-DD format
                return_date: Return date in YYYY-MM-DD format (optional)
                passengers: Number of passengers
                cabin_class: Class of service (economy, business, first)
                currency: Currency code for prices
            
            Returns:
                List of flight options with prices and details
            """
            try:
                # Convert city names to airport codes if needed
                origin_code = await self.get_airport_code(origin)
                dest_code = await self.get_airport_code(destination)
                
                if self.serpapi_key:
                    return await self._search_flights_serpapi(
                        origin_code, dest_code, departure_date, 
                        return_date, passengers, cabin_class, currency
                    )
                elif self.aviationstack_key:
                    return await self._search_flights_aviationstack(
                        origin_code, dest_code, departure_date,
                        return_date, passengers, cabin_class
                    )
                else:
                    # Return mock data for demo purposes
                    return self._get_mock_flights(
                        origin_code, dest_code, departure_date,
                        return_date, passengers, cabin_class
                    )
                    
            except Exception as e:
                return [{
                    "error": str(e),
                    "message": "Failed to search flights"
                }]
        
        @self.server.tool()
        async def get_airport_code(self, city: str) -> str:
            """
            Convert city name to airport code.
            
            Args:
                city: City name
                
            Returns:
                Primary airport code for the city
            """
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
        
        @self.server.tool()
        async def get_flight_details(self, flight_id: str) -> Dict[str, Any]:
            """
            Get detailed information about a specific flight.
            
            Args:
                flight_id: Unique identifier for the flight
                
            Returns:
                Detailed flight information
            """
            # This would integrate with the actual API
            return {
                "flight_id": flight_id,
                "status": "scheduled",
                "aircraft": "Boeing 737-800",
                "meal": "Complimentary snack",
                "entertainment": "In-flight WiFi available",
                "baggage": "1 carry-on + 1 checked bag included"
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
        
        response = await self.http_client.get(
            "https://serpapi.com/search",
            params=params
        )
        
        if response.status_code == 200:
            data = response.json()
            return self._parse_serpapi_results(data)
        else:
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
        """Parse SerpAPI results into standard format"""
        flights = []
        
        if "best_flights" in data:
            for flight in data["best_flights"]:
                flights.append({
                    "airline": flight.get("airline", "Unknown"),
                    "flight_number": flight.get("flight_number", ""),
                    "departure_time": flight.get("departure_time", ""),
                    "arrival_time": flight.get("arrival_time", ""),
                    "duration": flight.get("duration", ""),
                    "price": flight.get("price", ""),
                    "stops": flight.get("stops", 0),
                    "booking_link": flight.get("booking_link", "")
                })
        
        return flights
    
    def _parse_aviationstack_results(
        self, data: Dict, passengers: int, cabin_class: str
    ) -> List[Dict[str, Any]]:
        """Parse Aviationstack results into standard format"""
        flights = []
        
        if "data" in data:
            for flight in data["data"][:10]:  # Limit to 10 results
                flights.append({
                    "airline": flight["airline"]["name"],
                    "flight_number": flight["flight"]["iata"],
                    "departure_time": flight["departure"]["scheduled"],
                    "arrival_time": flight["arrival"]["scheduled"],
                    "duration": self._calculate_duration(
                        flight["departure"]["scheduled"],
                        flight["arrival"]["scheduled"]
                    ),
                    "price": f"${150 + (100 if cabin_class == 'business' else 0)}",  # Mock price
                    "stops": 0,  # Aviationstack doesn't provide this
                    "booking_link": "#"  # Would need separate booking API
                })
        
        return flights
    
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
        
        return flights
    
    async def _search_airport_code_online(self, city: str) -> str:
        """Search for airport code online using SerpAPI"""
        params = {
            "api_key": self.serpapi_key,
            "q": f"{city} airport code IATA",
            "num": 1
        }
        
        response = await self.http_client.get(
            "https://serpapi.com/search",
            params=params
        )
        
        if response.status_code == 200:
            data = response.json()
            # Try to extract airport code from search results
            # This is a simplified extraction
            if "answer_box" in data and "answer" in data["answer_box"]:
                answer = data["answer_box"]["answer"]
                # Look for 3-letter code
                import re
                match = re.search(r'\b[A-Z]{3}\b', answer)
                if match:
                    return match.group()
        
        return city.upper()[:3]
    
    async def run(self):
        """Run the MCP server"""
        print(f"Starting Flight Search MCP Server on port {os.getenv('MCP_SERVER_PORT', 8765)}")
        await self.server.run(
            transport="tcp",
            host="localhost",
            port=int(os.getenv("MCP_SERVER_PORT", 8765))
        )

# Run the server
if __name__ == "__main__":
    server = FlightSearchServer()
    asyncio.run(server.run())