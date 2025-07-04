"""
Amadeus Flight Search using Official SDK
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from amadeus import Client, ResponseError
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class AmadeusSDKFlightSearch:
    """Flight search using official Amadeus Python SDK"""
    
    def __init__(self):
        load_dotenv()
        
        # Initialize Amadeus client
        self.amadeus = Client(
            client_id=os.getenv("AMADEUS_CLIENT_ID"),
            client_secret=os.getenv("AMADEUS_CLIENT_SECRET"),
            hostname='production'  # Use production environment
        )
        
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
        max_results: int = 50,
        nonstop: bool = False
    ) -> List[Dict[str, Any]]:
        """Search flights using Amadeus SDK"""
        try:
            logger.info(f"Searching flights: {origin} -> {destination} on {departure_date}")
            
            # Build search parameters
            params = {
                'originLocationCode': origin.upper(),
                'destinationLocationCode': destination.upper(),
                'departureDate': departure_date,
                'adults': adults,
                'currencyCode': currency,
                'max': max_results
            }
            
            # Add optional parameters
            if return_date:
                params['returnDate'] = return_date
            if children > 0:
                params['children'] = children
            if travel_class != "ECONOMY":
                params['travelClass'] = travel_class.upper()
            if nonstop:
                params['nonStop'] = 'true'
            
            # Search flights
            response = self.amadeus.shopping.flight_offers_search.get(**params)
            
            # Format results
            results = self._format_sdk_results(response.data)
            
            # Log statistics
            airlines = set(f["airline_code"] for f in results)
            direct_flights = [f for f in results if f.get("stops", 0) == 0]
            
            logger.info(f"Found {len(results)} flights from {len(airlines)} airlines")
            logger.info(f"Direct flights: {len(direct_flights)}")
            logger.info(f"Airlines: {', '.join(sorted(airlines))}")
            
            return results
            
        except ResponseError as error:
            logger.error(f"Amadeus SDK error: {error}")
            logger.error(f"Error details: {error.response.body}")
            return []
        except Exception as e:
            logger.error(f"Error searching flights: {e}")
            return []
    
    def _format_sdk_results(self, offers: List[Any]) -> List[Dict[str, Any]]:
        """Format SDK results into standard format"""
        flights = []
        
        try:
            for offer in offers[:50]:  # Limit results
                # Get first itinerary
                itinerary = offer['itineraries'][0]
                segments = itinerary['segments']
                
                # Build flight info
                first_segment = segments[0]
                last_segment = segments[-1]
                
                # Parse duration
                duration_minutes = self._parse_duration(itinerary.get('duration', 'PT0H'))
                
                flight = {
                    "id": offer['id'],
                    "airline": self._get_carrier_name(first_segment['carrierCode']),
                    "airline_code": first_segment['carrierCode'],
                    "flight_number": f"{first_segment['carrierCode']}{first_segment['number']}",
                    "departure_time": self._format_datetime(first_segment['departure']['at']),
                    "departure_airport": f"{self._get_airport_name(first_segment['departure']['iataCode'])} ({first_segment['departure']['iataCode']})",
                    "departure_terminal": first_segment['departure'].get('terminal', ''),
                    "arrival_time": self._format_datetime(last_segment['arrival']['at']),
                    "arrival_airport": f"{self._get_airport_name(last_segment['arrival']['iataCode'])} ({last_segment['arrival']['iataCode']})",
                    "arrival_terminal": last_segment['arrival'].get('terminal', ''),
                    "duration": self._format_duration(duration_minutes),
                    "duration_minutes": duration_minutes,
                    "price": float(offer['price']['total']),
                    "currency": offer['price']['currency'],
                    "price_formatted": f"{offer['price']['currency']} {offer['price']['total']}",
                    "stops": len(segments) - 1,
                    "segments": []
                }
                
                # Add segment details
                for seg in segments:
                    flight["segments"].append({
                        "carrier": seg['carrierCode'],
                        "flight_number": f"{seg['carrierCode']}{seg['number']}",
                        "departure": seg['departure']['iataCode'],
                        "departure_time": self._format_datetime(seg['departure']['at']),
                        "arrival": seg['arrival']['iataCode'],
                        "arrival_time": self._format_datetime(seg['arrival']['at']),
                        "duration": self._parse_duration(seg.get('duration', 'PT0H')),
                        "aircraft": seg.get('aircraft', {}).get('code', '')
                    })
                
                # Add layover info
                if len(segments) > 1:
                    layovers = []
                    for i in range(len(segments) - 1):
                        layover_airport = segments[i]['arrival']['iataCode']
                        layover_duration = self._calculate_layover_duration(
                            segments[i]['arrival']['at'],
                            segments[i + 1]['departure']['at']
                        )
                        layovers.append(f"{layover_airport} ({layover_duration})")
                    flight["layovers"] = ", ".join(layovers)
                
                # Add cabin class
                if offer.get('travelerPricings'):
                    cabin = offer['travelerPricings'][0]['fareDetailsBySegment'][0].get('cabin', 'ECONOMY')
                    flight["cabin_class"] = cabin
                
                flights.append(flight)
                
        except Exception as e:
            logger.error(f"Error formatting SDK results: {e}")
        
        return flights
    
    def _parse_duration(self, duration_str: str) -> int:
        """Parse ISO 8601 duration to minutes"""
        import re
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
        # Return code for now - can be enhanced with airport database
        return code