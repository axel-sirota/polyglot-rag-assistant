#!/usr/bin/env python3
"""
Test real flight searches with various routes
"""
import asyncio
import os
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.amadeus_flight_search import AmadeusFlightSearch
from datetime import datetime, timedelta

async def test_real_flights():
    """Test real flight routes"""
    load_dotenv()
    
    print("🔍 Testing Real Flight Routes")
    print("=" * 60)
    
    amadeus = AmadeusFlightSearch()
    
    # Test popular routes with likely direct flights
    test_routes = [
        # Domestic US routes (likely to have direct flights)
        {"origin": "JFK", "destination": "LAX", "name": "New York to Los Angeles"},
        {"origin": "JFK", "destination": "MIA", "name": "New York to Miami"},
        {"origin": "LAX", "destination": "JFK", "name": "Los Angeles to New York"},
        
        # International routes
        {"origin": "JFK", "destination": "LHR", "name": "New York to London"},
        {"origin": "EZE", "destination": "JFK", "name": "Buenos Aires to New York"},
        {"origin": "JFK", "destination": "CDG", "name": "New York to Paris"},
    ]
    
    # Test date (2 weeks from now for better availability)
    test_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    
    for route in test_routes:
        print(f"\n✈️  Testing: {route['name']}")
        print(f"   Route: {route['origin']} → {route['destination']}")
        print(f"   Date: {test_date}")
        
        try:
            # Search for flights
            results = await amadeus.search_flights(
                origin=route['origin'],
                destination=route['destination'],
                departure_date=test_date,
                adults=1,
                travel_class="ECONOMY"
            )
            
            if results:
                print(f"   ✅ Found {len(results)} flights")
                
                # Check for direct flights
                direct_flights = [f for f in results if f.get("stops", 0) == 0]
                print(f"   Direct flights: {len(direct_flights)}")
                
                # Show airlines
                airlines = set(f["airline_code"] for f in results)
                print(f"   Airlines: {', '.join(sorted(airlines))}")
                
                # Check for specific airlines
                aa_flights = [f for f in results if f.get("airline_code") == "AA"]
                if aa_flights:
                    print(f"   🎯 American Airlines flights: {len(aa_flights)}")
                    aa_direct = [f for f in aa_flights if f.get("stops", 0) == 0]
                    if aa_direct:
                        print(f"   🎯 American Airlines DIRECT: {len(aa_direct)}")
                
                # Show first direct flight if available
                if direct_flights:
                    flight = direct_flights[0]
                    print(f"\n   First direct flight:")
                    print(f"   {flight['airline']} ({flight['airline_code']}) - {flight['flight_number']}")
                    print(f"   Departure: {flight['departure_time']} from {flight['departure_airport']}")
                    print(f"   Arrival: {flight['arrival_time']} at {flight['arrival_airport']}")
                    print(f"   Duration: {flight['duration']}")
                    print(f"   Price: {flight['price_formatted']}")
            else:
                print(f"   ❌ No flights found")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Test specific American Airlines route on specific date
    print("\n" + "="*60)
    print("🎯 Testing American Airlines EZE-JFK on July 7, 2025")
    
    try:
        results = await amadeus.search_flights(
            origin="EZE",
            destination="JFK",
            departure_date="2025-07-07",
            adults=1,
            travel_class="ECONOMY"
        )
        
        if results:
            aa_flights = [f for f in results if f.get("airline_code") == "AA"]
            if aa_flights:
                print(f"✅ Found {len(aa_flights)} American Airlines flights")
                for flight in aa_flights[:3]:  # Show first 3
                    print(f"\n   Flight: {flight['flight_number']}")
                    print(f"   Stops: {flight.get('stops', 0)}")
                    print(f"   Departure: {flight['departure_time']}")
                    print(f"   Price: {flight['price_formatted']}")
            else:
                print("❌ No American Airlines flights found on this route/date")
                print("   Available airlines:", set(f["airline_code"] for f in results))
        else:
            print("❌ No flights found at all")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_real_flights())