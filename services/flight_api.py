import httpx
from typing import Dict, List, Optional, Any
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class FlightAPIWrapper:
    """Wrapper for various flight search APIs"""
    
    def __init__(self):
        self.serpapi_key = os.getenv("SERPAPI_API_KEY")
        self.aviationstack_key = os.getenv("AVIATIONSTACK_API_KEY")
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
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
        """
        Search for flights using available APIs.
        
        Returns:
            List of flight options
        """
        if self.serpapi_key:
            return await self._search_serpapi(
                origin, destination, departure_date,
                return_date, passengers, cabin_class, currency
            )
        elif self.aviationstack_key:
            return await self._search_aviationstack(
                origin, destination, departure_date,
                return_date, passengers, cabin_class
            )
        else:
            # Return mock data for demo
            return self._generate_mock_flights(
                origin, destination, departure_date,
                return_date, passengers, cabin_class
            )
    
    async def _search_serpapi(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str],
        passengers: int,
        cabin_class: str,
        currency: str
    ) -> List[Dict[str, Any]]:
        """Search using SerpAPI Google Flights"""
        try:
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
                logger.error(f"SerpAPI error: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error calling SerpAPI: {e}")
            return []
    
    async def _search_aviationstack(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str],
        passengers: int,
        cabin_class: str
    ) -> List[Dict[str, Any]]:
        """Search using Aviationstack API"""
        try:
            params = {
                "access_key": self.aviationstack_key,
                "dep_iata": origin,
                "arr_iata": destination,
                "flight_date": departure_date
            }
            
            response = await self.http_client.get(
                "http://api.aviationstack.com/v1/flights",
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_aviationstack_results(data, cabin_class)
            else:
                logger.error(f"Aviationstack error: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error calling Aviationstack: {e}")
            return []
    
    def _parse_serpapi_results(self, data: Dict) -> List[Dict[str, Any]]:
        """Parse SerpAPI response into standard format"""
        flights = []
        
        for flight_group in ["best_flights", "other_flights"]:
            if flight_group in data:
                for flight in data[flight_group][:5]:  # Limit results
                    flights.append({
                        "airline": flight.get("airline", ["Unknown"])[0],
                        "flight_number": flight.get("flight_number", ""),
                        "departure_time": flight.get("departure_time", ""),
                        "arrival_time": flight.get("arrival_time", ""),
                        "duration": flight.get("duration", ""),
                        "price": flight.get("price", "N/A"),
                        "stops": len(flight.get("layovers", [])),
                        "aircraft": flight.get("airplane", ""),
                        "booking_link": flight.get("booking_link", "")
                    })
        
        return flights
    
    def _parse_aviationstack_results(self, data: Dict, cabin_class: str) -> List[Dict[str, Any]]:
        """Parse Aviationstack response into standard format"""
        flights = []
        
        if "data" in data:
            for flight in data["data"][:10]:
                # Calculate duration
                dep_time = datetime.fromisoformat(flight["departure"]["scheduled"].replace("Z", "+00:00"))
                arr_time = datetime.fromisoformat(flight["arrival"]["scheduled"].replace("Z", "+00:00"))
                duration = arr_time - dep_time
                hours = int(duration.total_seconds() // 3600)
                minutes = int((duration.total_seconds() % 3600) // 60)
                
                # Estimate price based on duration and class
                base_price = 100 + (hours * 50)
                if cabin_class == "business":
                    base_price *= 3
                elif cabin_class == "first":
                    base_price *= 5
                
                flights.append({
                    "airline": flight["airline"]["name"],
                    "flight_number": flight["flight"]["iata"],
                    "departure_time": flight["departure"]["scheduled"],
                    "arrival_time": flight["arrival"]["scheduled"],
                    "duration": f"{hours}h {minutes}m",
                    "price": f"${base_price}",
                    "stops": 0,
                    "aircraft": flight.get("aircraft", {}).get("registration", ""),
                    "booking_link": ""
                })
        
        return flights
    
    def _generate_mock_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str],
        passengers: int,
        cabin_class: str
    ) -> List[Dict[str, Any]]:
        """Generate realistic mock flight data for demos"""
        airlines_data = [
            {"name": "United Airlines", "code": "UA", "base_price": 250},
            {"name": "American Airlines", "code": "AA", "base_price": 240},
            {"name": "Delta Airlines", "code": "DL", "base_price": 245},
            {"name": "Emirates", "code": "EK", "base_price": 380},
            {"name": "Lufthansa", "code": "LH", "base_price": 320}
        ]
        
        flights = []
        dep_date = datetime.strptime(departure_date, "%Y-%m-%d")
        
        for i, airline in enumerate(airlines_data[:3]):
            # Morning flight
            morning_dep = dep_date.replace(hour=6 + i*2, minute=30)
            morning_arr = morning_dep.replace(hour=10 + i*2, minute=45)
            
            price = airline["base_price"]
            if cabin_class == "business":
                price *= 3
            elif cabin_class == "first":
                price *= 5
            
            price *= passengers
            
            flights.append({
                "airline": airline["name"],
                "flight_number": f"{airline['code']}{100 + i}",
                "departure_time": morning_dep.isoformat(),
                "arrival_time": morning_arr.isoformat(),
                "duration": "4h 15m",
                "price": f"${price}",
                "stops": 0 if i == 0 else 1,
                "aircraft": "Boeing 737-800",
                "booking_link": f"https://example.com/book/{airline['code'].lower()}"
            })
            
            # Evening flight
            evening_dep = dep_date.replace(hour=16 + i, minute=20)
            evening_arr = evening_dep.replace(hour=20 + i, minute=50)
            
            flights.append({
                "airline": airline["name"],
                "flight_number": f"{airline['code']}{200 + i}",
                "departure_time": evening_dep.isoformat(),
                "arrival_time": evening_arr.isoformat(),
                "duration": "4h 30m",
                "price": f"${int(price * 0.9)}",  # Slightly cheaper evening flight
                "stops": 1 if i > 0 else 0,
                "aircraft": "Airbus A320",
                "booking_link": f"https://example.com/book/{airline['code'].lower()}"
            })
        
        return flights
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()