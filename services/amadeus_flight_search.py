"""
Amadeus Flight Search Integration
Replaces failing AviationStack and SerpAPI with more reliable Amadeus API
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import httpx

logger = logging.getLogger(__name__)

class AmadeusFlightSearch:
    """Flight search using Amadeus API with proper authentication"""
    
    def __init__(self):
        self.client_id = os.getenv("AMADEUS_CLIENT_ID", "pu69gvJcqzHXJfNQDjFGGHT6s4oC8V9e")
        self.client_secret = os.getenv("AMADEUS_CLIENT_SECRET", "p8M2AAkmJnJvn82E")
        # Use test or production URL based on environment variable
        amadeus_base = os.getenv("AMADEUS_BASE_URL", "api.amadeus.com")
        self.base_url = f"https://{amadeus_base}/v2"
        self.auth_url = f"https://{amadeus_base}/v1/security/oauth2/token"
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.access_token = None
        self.token_expiry = None
        
    async def _get_access_token(self) -> str:
        """Get or refresh Amadeus access token"""
        # Check if we have a valid token
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.access_token
            
        # Get new token
        try:
            data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
            
            response = await self.http_client.post(
                self.auth_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                # Token expires in seconds, convert to datetime
                expires_in = token_data.get("expires_in", 1799)  # Default 30 min
                self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)  # Refresh 1 min early
                logger.info("Amadeus token obtained successfully")
                return self.access_token
            else:
                logger.error(f"Failed to get Amadeus token: {response.status_code} - {response.text}")
                raise Exception(f"Amadeus authentication failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error getting Amadeus token: {e}")
            raise
    
    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        children: int = 0,
        travel_class: str = "ECONOMY",
        currency: str = "USD",
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Search flights using Amadeus API"""
        try:
            # Get access token
            token = await self._get_access_token()
            
            # Build request parameters
            params = {
                "originLocationCode": origin.upper(),
                "destinationLocationCode": destination.upper(),
                "departureDate": departure_date,
                "adults": adults,
                "currencyCode": currency,
                "max": max_results
            }
            
            # Add optional parameters
            if return_date:
                params["returnDate"] = return_date
            if children > 0:
                params["children"] = children
            if travel_class != "ECONOMY":
                params["travelClass"] = travel_class.upper()
            
            # Add non-stop filter if looking for direct flights
            params["nonStop"] = "false"  # Include both direct and connecting flights
            params["max"] = 50  # Get more results to find direct flights
            
            # Make API request
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            response = await self.http_client.get(
                f"{self.base_url}/shopping/flight-offers",
                params=params,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                results = self._format_amadeus_results(data)
                
                # Log airlines found
                airlines = set(f["airline_code"] for f in results)
                logger.info(f"Airlines found: {airlines}")
                
                # Check for direct flights
                direct_flights = [f for f in results if f.get("stops", 0) == 0]
                logger.info(f"Direct flights found: {len(direct_flights)}")
                
                # Check for American Airlines
                aa_flights = [f for f in results if f.get("airline_code") == "AA"]
                logger.info(f"American Airlines flights found: {len(aa_flights)}")
                
                return results
            else:
                logger.error(f"Amadeus search failed: {response.status_code} - {response.text}")
                # Return empty list to fall back to mock data
                return []
                
        except Exception as e:
            logger.error(f"Error searching Amadeus flights: {e}")
            return []
    
    def _format_amadeus_results(self, data: Dict) -> List[Dict[str, Any]]:
        """Format Amadeus results into standard format"""
        flights = []
        
        try:
            for offer in data.get("data", [])[:10]:  # Limit to 10 results
                # Get first itinerary (outbound)
                itinerary = offer["itineraries"][0]
                segments = itinerary["segments"]
                
                # Build flight info
                first_segment = segments[0]
                last_segment = segments[-1]
                
                # Calculate total duration
                duration_str = itinerary.get("duration", "PT0H")
                duration_minutes = self._parse_duration(duration_str)
                
                flight = {
                    "id": offer["id"],
                    "airline": self._get_carrier_name(first_segment["carrierCode"]),
                    "airline_code": first_segment["carrierCode"],
                    "flight_number": f"{first_segment['carrierCode']}{first_segment['number']}",
                    "departure_time": self._format_datetime(first_segment["departure"]["at"]),
                    "departure_airport": f"{self._get_airport_name(first_segment['departure']['iataCode'])} ({first_segment['departure']['iataCode']})",
                    "departure_terminal": first_segment["departure"].get("terminal", ""),
                    "arrival_time": self._format_datetime(last_segment["arrival"]["at"]),
                    "arrival_airport": f"{self._get_airport_name(last_segment['arrival']['iataCode'])} ({last_segment['arrival']['iataCode']})",
                    "arrival_terminal": last_segment["arrival"].get("terminal", ""),
                    "duration": self._format_duration(duration_minutes),
                    "duration_minutes": duration_minutes,
                    "price": float(offer["price"]["total"]),
                    "currency": offer["price"]["currency"],
                    "price_formatted": f"{offer['price']['currency']} {offer['price']['total']}",
                    "stops": len(segments) - 1,
                    "segments": []
                }
                
                # Add segment details
                for seg in segments:
                    flight["segments"].append({
                        "carrier": seg["carrierCode"],
                        "flight_number": f"{seg['carrierCode']}{seg['number']}",
                        "departure": seg["departure"]["iataCode"],
                        "departure_time": self._format_datetime(seg["departure"]["at"]),
                        "arrival": seg["arrival"]["iataCode"],
                        "arrival_time": self._format_datetime(seg["arrival"]["at"]),
                        "duration": self._parse_duration(seg.get("duration", "PT0H")),
                        "aircraft": seg.get("aircraft", {}).get("code", "")
                    })
                
                # Add layover info if applicable
                if len(segments) > 1:
                    layovers = []
                    for i in range(len(segments) - 1):
                        layover_airport = segments[i]["arrival"]["iataCode"]
                        layover_duration = self._calculate_layover_duration(
                            segments[i]["arrival"]["at"],
                            segments[i + 1]["departure"]["at"]
                        )
                        layovers.append(f"{layover_airport} ({layover_duration})")
                    flight["layovers"] = ", ".join(layovers)
                
                # Add cabin class
                if offer.get("travelerPricings"):
                    cabin = offer["travelerPricings"][0]["fareDetailsBySegment"][0].get("cabin", "ECONOMY")
                    flight["cabin_class"] = cabin
                
                flights.append(flight)
                
        except Exception as e:
            logger.error(f"Error formatting Amadeus results: {e}")
        
        return flights
    
    def _parse_duration(self, duration_str: str) -> int:
        """Parse ISO 8601 duration to minutes"""
        import re
        # Example: PT2H30M
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?', duration_str)
        if match:
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            return hours * 60 + minutes
        return 0
    
    def _format_duration(self, minutes: int) -> str:
        """Format minutes to readable duration"""
        hours = minutes // 60
        mins = minutes % 60
        if hours > 0 and mins > 0:
            return f"{hours}h {mins}m"
        elif hours > 0:
            return f"{hours}h"
        else:
            return f"{mins}m"
    
    def _format_datetime(self, dt_str: str) -> str:
        """Format datetime string to readable format"""
        try:
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            return dt.strftime("%H:%M")
        except:
            return dt_str
    
    def _calculate_layover_duration(self, arrival_time: str, departure_time: str) -> str:
        """Calculate layover duration between flights"""
        try:
            arrival = datetime.fromisoformat(arrival_time.replace('Z', '+00:00'))
            departure = datetime.fromisoformat(departure_time.replace('Z', '+00:00'))
            duration = departure - arrival
            hours = int(duration.total_seconds() // 3600)
            minutes = int((duration.total_seconds() % 3600) // 60)
            return f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
        except:
            return ""
    
    def _get_carrier_name(self, code: str) -> str:
        """Get airline name from IATA code"""
        carriers = {
            "AA": "American Airlines",
            "DL": "Delta Air Lines",
            "UA": "United Airlines",
            "WN": "Southwest Airlines",
            "B6": "JetBlue Airways",
            "AS": "Alaska Airlines",
            "NK": "Spirit Airlines",
            "F9": "Frontier Airlines",
            "G4": "Allegiant Air",
            "SY": "Sun Country Airlines",
            "BA": "British Airways",
            "LH": "Lufthansa",
            "AF": "Air France",
            "KL": "KLM",
            "IB": "Iberia",
            "LX": "Swiss International",
            "AZ": "Alitalia",
            "EW": "Eurowings",
            "FR": "Ryanair",
            "U2": "easyJet",
            "EI": "Aer Lingus",
            "TP": "TAP Air Portugal",
            "SN": "Brussels Airlines",
            "LO": "LOT Polish Airlines",
            "OK": "Czech Airlines",
            "RO": "TAROM",
            "JU": "Air Serbia",
            "A3": "Aegean Airlines",
            "TK": "Turkish Airlines",
            "SU": "Aeroflot",
            "EK": "Emirates",
            "QR": "Qatar Airways",
            "EY": "Etihad Airways",
            "SQ": "Singapore Airlines",
            "CX": "Cathay Pacific",
            "NH": "All Nippon Airways",
            "JL": "Japan Airlines",
            "KE": "Korean Air",
            "OZ": "Asiana Airlines",
            "CA": "Air China",
            "MU": "China Eastern",
            "CZ": "China Southern",
            "AI": "Air India",
            "6E": "IndiGo",
            "SG": "SpiceJet",
            "QF": "Qantas",
            "VA": "Virgin Australia",
            "NZ": "Air New Zealand",
            "AC": "Air Canada",
            "WS": "WestJet",
            "AM": "Aeroméxico",
            "CM": "Copa Airlines",
            "AV": "Avianca",
            "LA": "LATAM Airlines",
            "AR": "Aerolíneas Argentinas",
            "G3": "Gol Linhas Aéreas",
            "AD": "Azul Brazilian Airlines",
            "ET": "Ethiopian Airlines",
            "MS": "EgyptAir",
            "SA": "South African Airways",
            "KQ": "Kenya Airways",
            "RJ": "Royal Jordanian"
        }
        return carriers.get(code, code)
    
    def _get_airport_name(self, code: str) -> str:
        """Get airport name from IATA code"""
        # This would ideally use a comprehensive airport database
        # For now, return the code - the flight search service already has airport mappings
        return code