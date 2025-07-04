#!/usr/bin/env python3
"""
Test Amadeus SDK flight search
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.amadeus_sdk_flight_search import AmadeusSDKFlightSearch
from datetime import datetime, timedelta

async def test_amadeus_sdk():
    """Test Amadeus SDK implementation"""
    print("🔍 Testing Amadeus SDK Flight Search")
    print("=" * 60)
    
    amadeus = AmadeusSDKFlightSearch()
    
    # Test routes
    test_routes = [
        {"origin": "JFK", "destination": "LAX", "name": "New York to Los Angeles"},
        {"origin": "EZE", "destination": "JFK", "name": "Buenos Aires to New York"},
        {"origin": "JFK", "destination": "LHR", "name": "New York to London"},
        {"origin": "MAD", "destination": "BCN", "name": "Madrid to Barcelona"},
    ]
    
    # Test multiple dates for American Airlines EZE-JFK
    print("\n🎯 Testing American Airlines EZE-JFK flights")
    print("-" * 40)
    
    test_dates = [
        "2025-07-07",  # Original date requested
        "2025-07-15",
        "2025-08-01",
        "2025-08-15"
    ]
    
    for date in test_dates:
        print(f"\n📅 Date: {date}")
        
        try:
            results = await amadeus.search_flights(
                origin="EZE",
                destination="JFK",
                departure_date=date,
                adults=1,
                travel_class="ECONOMY"
            )
            
            if results:
                # Filter American Airlines flights
                aa_flights = [f for f in results if f.get("airline_code") == "AA"]
                aa_direct = [f for f in aa_flights if f.get("stops", 0) == 0]
                
                print(f"   Total flights: {len(results)}")
                print(f"   American Airlines: {len(aa_flights)}")
                print(f"   AA Direct flights: {len(aa_direct)}")
                
                if aa_direct:
                    flight = aa_direct[0]
                    print(f"\n   ✈️  {flight['flight_number']} - DIRECT")
                    print(f"   Departure: {flight['departure_time']} from {flight['departure_airport']}")
                    print(f"   Arrival: {flight['arrival_time']} at {flight['arrival_airport']}")
                    print(f"   Duration: {flight['duration']}")
                    print(f"   Price: {flight['price_formatted']}")
            else:
                print("   ❌ No flights found")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Test other routes
    print("\n\n📍 Testing Other Routes")
    print("-" * 40)
    
    test_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    
    for route in test_routes:
        print(f"\n✈️  {route['name']}")
        print(f"   Date: {test_date}")
        
        try:
            results = await amadeus.search_flights(
                origin=route['origin'],
                destination=route['destination'],
                departure_date=test_date,
                adults=1
            )
            
            if results:
                direct_flights = [f for f in results if f.get("stops", 0) == 0]
                airlines = set(f["airline_code"] for f in results)
                
                print(f"   Found: {len(results)} flights")
                print(f"   Direct: {len(direct_flights)}")
                print(f"   Airlines: {', '.join(sorted(airlines))}")
                
                if direct_flights:
                    flight = direct_flights[0]
                    print(f"   First direct: {flight['airline']} {flight['flight_number']} - {flight['price_formatted']}")
            else:
                print("   ❌ No flights found")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_amadeus_sdk())