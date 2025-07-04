#!/usr/bin/env python3
"""
Test AviationStack API
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.flight_search_service import FlightSearchServer
from datetime import datetime, timedelta

async def test_aviationstack():
    """Test AviationStack flight search"""
    print("🔍 Testing AviationStack API")
    print("=" * 60)
    
    # Use the existing FlightSearchServer that has AviationStack integration
    flight_service = FlightSearchServer()
    
    # Test routes
    test_cases = [
        {
            "origin": "JFK",
            "destination": "LAX",
            "name": "New York to Los Angeles"
        },
        {
            "origin": "LHR",
            "destination": "CDG",
            "name": "London to Paris"
        },
        {
            "origin": "NRT",
            "destination": "SIN",
            "name": "Tokyo to Singapore"
        }
    ]
    
    test_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    
    for test in test_cases:
        print(f"\n✈️  Testing: {test['name']}")
        print(f"   Route: {test['origin']} → {test['destination']}")
        print(f"   Date: {test_date}")
        
        try:
            # Call the service directly
            results = await flight_service.search_flights(
                origin=test['origin'],
                destination=test['destination'],
                departure_date=test_date
            )
            
            if results:
                print(f"   ✅ Found {len(results)} flights")
                
                # Check response format
                if results[0].get("source") == "aviationstack":
                    print("   Source: AviationStack API")
                elif results[0].get("source") == "amadeus":
                    print("   Source: Amadeus API (fallback)")
                else:
                    print("   Source: Mock data (APIs failed)")
                
                # Show first flight
                flight = results[0]
                print(f"\n   First flight:")
                print(f"   {flight.get('airline', 'Unknown')} - {flight.get('flight_number', 'N/A')}")
                print(f"   Departure: {flight.get('departure_time', 'N/A')}")
                print(f"   Price: {flight.get('price_formatted', 'N/A')}")
                
            else:
                print("   ❌ No flights found")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Test error handling
    print("\n\n🧪 Testing Error Handling")
    print("-" * 40)
    
    # Test invalid route
    print("\nTesting invalid airport code:")
    try:
        results = await flight_service.search_flights(
            origin="XXX",
            destination="YYY",
            departure_date=test_date
        )
        if results:
            print(f"   Got {len(results)} results (likely mock data)")
        else:
            print("   No results returned")
    except Exception as e:
        print(f"   Handled error: {e}")

if __name__ == "__main__":
    asyncio.run(test_aviationstack())