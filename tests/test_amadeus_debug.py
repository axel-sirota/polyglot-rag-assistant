#!/usr/bin/env python3
"""
Debug Amadeus API connection
"""
import asyncio
import os
import httpx
from dotenv import load_dotenv
import time

async def debug_amadeus():
    """Debug Amadeus API connection"""
    load_dotenv()
    
    client_id = os.getenv("AMADEUS_CLIENT_ID")
    client_secret = os.getenv("AMADEUS_CLIENT_SECRET")
    base_url = os.getenv("AMADEUS_BASE_URL", "api.amadeus.com")
    
    print("🔍 Debugging Amadeus API")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        # Step 1: Get token
        auth_url = f"https://{base_url}/v1/security/oauth2/token"
        
        print(f"1. Getting token from: {auth_url}")
        
        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret
        }
        
        auth_response = await client.post(
            auth_url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if auth_response.status_code != 200:
            print(f"❌ Auth failed: {auth_response.status_code}")
            print(f"Response: {auth_response.text}")
            return
            
        token_data = auth_response.json()
        access_token = token_data["access_token"]
        
        print(f"✅ Got token: {access_token[:30]}...")
        print(f"   Type: {token_data.get('type')}")
        print(f"   Expires in: {token_data.get('expires_in')} seconds")
        
        # Step 2: Wait a moment
        print("\n2. Waiting 2 seconds...")
        await asyncio.sleep(2)
        
        # Step 3: Try search with explicit headers
        search_url = f"https://{base_url}/v2/shopping/flight-offers"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        params = {
            "originLocationCode": "JFK",
            "destinationLocationCode": "LAX",
            "departureDate": "2025-08-01",
            "adults": 1,
            "max": 5
        }
        
        print(f"\n3. Searching flights: {search_url}")
        print(f"   Headers: {list(headers.keys())}")
        print(f"   Params: {params}")
        
        search_response = await client.get(
            search_url,
            params=params,
            headers=headers
        )
        
        print(f"\n4. Response status: {search_response.status_code}")
        
        if search_response.status_code == 200:
            data = search_response.json()
            print(f"✅ Success! Found {len(data.get('data', []))} flights")
            
            if data.get('data'):
                flight = data['data'][0]
                print(f"\nFirst flight:")
                print(f"   ID: {flight.get('id')}")
                print(f"   Price: {flight.get('price', {}).get('total')} {flight.get('price', {}).get('currency')}")
        else:
            print(f"❌ Search failed!")
            print(f"Headers sent: {search_response.request.headers}")
            print(f"URL: {search_response.url}")
            print(f"Response: {search_response.text[:500]}")

if __name__ == "__main__":
    asyncio.run(debug_amadeus())