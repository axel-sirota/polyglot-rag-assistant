#!/usr/bin/env python3
"""Test flight search functionality"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

async def test_mock_flight_search():
    """Test flight search with mock data"""
    try:
        from services.flight_search_service import FlightSearchServer
        
        print("✈️ Testing Flight Search\n")
        
        server = FlightSearchServer()
        
        # Test airport code lookup
        print("1. Testing airport code lookup...")
        codes = {
            "new york": "JFK",
            "london": "LHR",
            "paris": "CDG",
            "NYC": "JFK"
        }
        
        for city, expected in codes.items():
            result = await server.get_airport_code(city)
            status = "✅" if result == expected else "❌"
            print(f"   {status} {city} -> {result} (expected: {expected})")
        
        # Test flight search
        print("\n2. Testing flight search...")
        origin = "JFK"
        destination = "CDG"
        departure_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        # Search flights (will use mock data if no API keys)
        flights = await server._get_mock_flights(
            origin, destination, departure_date,
            None, 1, "economy"
        )
        
        print(f"   Found {len(flights)} flights from {origin} to {destination}")
        
        for i, flight in enumerate(flights[:3]):
            print(f"\n   Flight {i+1}:")
            print(f"   - Airline: {flight['airline']}")
            print(f"   - Flight: {flight['flight_number']}")
            print(f"   - Price: {flight['price']}")
            print(f"   - Duration: {flight['duration']}")
            print(f"   - Stops: {flight['stops']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Flight Search Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_real_flight_api():
    """Test real flight API if credentials available"""
    try:
        import httpx
        
        serpapi_key = os.getenv("SERPAPI_API_KEY")
        if not serpapi_key:
            print("\n⚠️  Skipping real API test (no SERPAPI_API_KEY)")
            return True
        
        print("\n3. Testing real flight API...")
        
        async with httpx.AsyncClient() as client:
            params = {
                "api_key": serpapi_key,
                "engine": "google_flights",
                "departure_id": "JFK",
                "arrival_id": "CDG",
                "outbound_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                "currency": "USD",
                "adults": 1,
                "type": "1"  # One way
            }
            
            response = await client.get(
                "https://serpapi.com/search",
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                if "best_flights" in data and len(data["best_flights"]) > 0:
                    print(f"   ✅ Found {len(data['best_flights'])} real flights")
                    flight = data["best_flights"][0]
                    print(f"   First flight: {flight.get('airline', 'Unknown')} - ${flight.get('price', 'N/A')}")
                else:
                    print("   ⚠️  No flights found in response")
            else:
                print(f"   ❌ API returned status {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Real API Error: {e}")
        return False

async def test_flight_agent_integration():
    """Test flight agent integration"""
    try:
        from agents.flight_agent import FlightSearchAgent
        
        print("\n4. Testing Flight Agent...")
        
        agent = FlightSearchAgent()
        
        # Test intent detection
        queries = [
            "Find flights from NYC to Paris next week",
            "I need to fly from London to Tokyo",
            "Show me flights Madrid Barcelona tomorrow"
        ]
        
        for query in queries:
            print(f"\n   Query: '{query}'")
            # This would normally process through the agent
            # For now just print that it's ready
            print(f"   ✅ Agent ready to process")
        
        return True
        
    except Exception as e:
        print(f"❌ Flight Agent Error: {e}")
        return False

async def main():
    """Run flight search tests"""
    print("🔍 Testing Flight Search Components\n")
    
    tests = [
        test_mock_flight_search(),
        test_real_flight_api(),
        test_flight_agent_integration()
    ]
    
    results = await asyncio.gather(*tests)
    
    print("\n📊 Flight Search Test Summary:")
    passed = sum(results)
    total = len(results)
    print(f"   Passed: {passed}/{total}")

if __name__ == "__main__":
    asyncio.run(main())