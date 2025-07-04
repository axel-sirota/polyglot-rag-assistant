#!/usr/bin/env python3
"""
Test direct flights from Buenos Aires to New York
"""
import asyncio
import os
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.amadeus_flight_search import AmadeusFlightSearch

async def test_direct_flights():
    """Test searching for direct flights"""
    load_dotenv()
    
    print("🔍 Testing direct flights EZE -> JFK")
    print("=" * 60)
    
    amadeus = AmadeusFlightSearch()
    
    # Test different dates
    test_dates = [
        "2025-07-07",
        "2025-07-08", 
        "2025-07-09",
        "2025-07-10"
    ]
    
    for date in test_dates:
        print(f"\n📅 Testing date: {date}")
        
        # Search for flights
        results = await amadeus.search_flights(
            origin="EZE",
            destination="JFK",
            departure_date=date,
            adults=1,
            travel_class="BUSINESS"
        )
        
        print(f"   Total flights found: {len(results)}")
        
        # Check for direct flights
        direct_flights = [f for f in results if f.get("stops", 0) == 0]
        print(f"   Direct flights: {len(direct_flights)}")
        
        # Check for American Airlines
        aa_flights = [f for f in results if f.get("airline_code") == "AA"]
        aa_direct = [f for f in aa_flights if f.get("stops", 0) == 0]
        
        print(f"   American Airlines flights: {len(aa_flights)}")
        print(f"   American Airlines DIRECT: {len(aa_direct)}")
        
        if aa_direct:
            for flight in aa_direct:
                print(f"\n   ✈️  AA Direct Flight Found!")
                print(f"      Flight: {flight['flight_number']}")
                print(f"      Departure: {flight['departure_time']} from {flight['departure_airport']}")
                print(f"      Arrival: {flight['arrival_time']} at {flight['arrival_airport']}")
                print(f"      Duration: {flight['duration']}")
                print(f"      Price: {flight['price_formatted']}")
                print(f"      Cabin: {flight.get('cabin_class', 'Unknown')}")
        
        # Show all airlines found
        airlines = set(f["airline_code"] for f in results)
        print(f"   Airlines in results: {sorted(airlines)}")
    
    print("\n" + "=" * 60)
    print("💡 Note: Amadeus test environment may have limited data")
    print("   Production environment would have more complete results")

if __name__ == "__main__":
    asyncio.run(test_direct_flights())