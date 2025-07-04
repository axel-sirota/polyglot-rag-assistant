#!/usr/bin/env python3
"""
Test flight search APIs to see which ones work
"""
import asyncio
import os
import httpx
from datetime import datetime, timedelta
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.amadeus_flight_search import AmadeusFlightSearch

async def test_amadeus():
    """Test Amadeus API with test credentials"""
    print("\n🔍 Testing Amadeus API (Test Environment)...")
    print(f"   Base URL: {os.getenv('AMADEUS_BASE_URL')}")
    client_id = os.getenv('AMADEUS_CLIENT_ID')
    if client_id:
        print(f"   Client ID: {client_id[:10]}...")
    else:
        print("   Client ID: Not found")
    
    try:
        amadeus = AmadeusFlightSearch()
        
        # Test authentication
        print("   Authenticating...")
        token = await amadeus._get_access_token()
        print(f"   ✅ Authentication successful! Token: {token[:20]}...")
        
        # Test flight search
        print("   Searching for flights JFK -> CDG...")
        results = await amadeus.search_flights(
            origin="JFK",
            destination="CDG", 
            departure_date="2025-07-20",
            adults=1,
            travel_class="ECONOMY"
        )
        
        if results and isinstance(results, list) and len(results) > 0:
            print(f"   ✅ Found {len(results)} flights!")
            flight = results[0]
            print(f"   Example: {flight.get('airline', 'Unknown')} - {flight.get('price', 'N/A')}")
        elif results and isinstance(results, dict) and results.get("flights"):
            print(f"   ✅ Found {len(results['flights'])} flights!")
            flight = results["flights"][0]
            print(f"   Example: {flight.get('airline', 'Unknown')} - {flight.get('price', 'N/A')}")
        else:
            print("   ⚠️  No flights found (API might be warming up)")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    return True

async def test_aviationstack():
    """Test AviationStack API"""
    print("\n🔍 Testing AviationStack API...")
    api_key = os.getenv("AVIATIONSTACK_API_KEY")
    
    if not api_key:
        print("   ❌ No API key found")
        return False
        
    try:
        async with httpx.AsyncClient() as client:
            # First try a simple airport lookup to test API key
            test_params = {
                "access_key": api_key
            }
            
            test_response = await client.get(
                "http://api.aviationstack.com/v1/airports",
                params=test_params
            )
            
            if test_response.status_code != 200:
                print(f"   ❌ API key test failed: {test_response.status_code}")
                print(f"   Response: {test_response.text[:200]}")
                return False
            
            print("   ✅ API key is valid")
            
            # Now try flights endpoint with correct format
            params = {
                "access_key": api_key,
                "dep_iata": "JFK",
                "arr_iata": "CDG",
                "limit": 5
            }
            
            response = await client.get(
                "http://api.aviationstack.com/v1/flights",
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("data"):
                    print(f"   ✅ API working! Found {len(data['data'])} flights")
                    return True
                else:
                    print(f"   ⚠️  API returned no data")
            else:
                print(f"   ❌ API error: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    return False

async def test_browserless_for_flights():
    """Test if Browserless.io can be used for flight searches"""
    print("\n🔍 Testing Browserless.io for flight searches...")
    api_key = os.getenv("BROWSERLESS_IO_API_KEY")
    
    if not api_key:
        print("   ❌ No API key found")
        return False
        
    print("   ℹ️  Browserless.io is a headless browser service")
    print("   ⚠️  Not ideal for flight searches because:")
    print("      - It's for web scraping, not structured flight data")
    print("      - Would need to scrape Google Flights or similar")
    print("      - Much slower than dedicated flight APIs")
    print("      - May violate terms of service of flight websites")
    print("   💡 Better to use Amadeus or fix AviationStack")
    
    return False

async def test_serpapi():
    """Test SerpAPI for Google Flights"""
    print("\n🔍 Testing SerpAPI (Google Flights)...")
    api_key = os.getenv("SERPAPI_API_KEY")
    
    if not api_key:
        print("   ❌ No API key found")
        return False
        
    try:
        async with httpx.AsyncClient() as client:
            params = {
                "engine": "google_flights",
                "api_key": api_key,
                "departure_id": "JFK",
                "arrival_id": "CDG",
                "outbound_date": "2025-07-20",
                "type": "2",  # One-way
                "currency": "USD",
                "hl": "en"
            }
            
            response = await client.get(
                "https://serpapi.com/search",
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    print(f"   ❌ API error: {data['error']}")
                elif data.get("best_flights") or data.get("other_flights"):
                    print(f"   ✅ API working! Found flight data")
                    return True
                else:
                    print(f"   ⚠️  No flight data in response")
            else:
                print(f"   ❌ HTTP error: {response.status_code}")
                
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    return False

async def main():
    """Test all flight APIs"""
    print("="*60)
    print("FLIGHT API TESTING")
    print("="*60)
    
    # Test each API
    amadeus_ok = await test_amadeus()
    aviationstack_ok = await test_aviationstack()
    serpapi_ok = await test_serpapi()
    browserless_ok = await test_browserless_for_flights()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"✅ Amadeus (Test): {'Working' if amadeus_ok else 'Failed'}")
    print(f"{'✅' if aviationstack_ok else '❌'} AviationStack: {'Working' if aviationstack_ok else 'Failed'}")
    print(f"{'✅' if serpapi_ok else '❌'} SerpAPI: {'Working' if serpapi_ok else 'Failed'}")
    print(f"❌ Browserless.io: Not suitable for flight searches")
    
    print("\n📝 RECOMMENDATION:")
    if amadeus_ok:
        print("   Use Amadeus as primary (most reliable)")
    elif aviationstack_ok:
        print("   Use AviationStack as primary")
    elif serpapi_ok:
        print("   Use SerpAPI as primary")
    else:
        print("   All APIs failed - will use mock data")
        
    print("\n⚠️  Note: Amadeus test environment may have 30-minute delay")
    print("   for new accounts. Try again later if it fails.")

if __name__ == "__main__":
    asyncio.run(main())