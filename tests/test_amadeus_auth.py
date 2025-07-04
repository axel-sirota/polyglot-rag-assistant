#!/usr/bin/env python3
"""
Test Amadeus API authentication and credentials
"""
import asyncio
import os
import httpx
from dotenv import load_dotenv

async def test_amadeus_auth():
    """Test Amadeus authentication"""
    load_dotenv()
    
    client_id = os.getenv("AMADEUS_CLIENT_ID")
    client_secret = os.getenv("AMADEUS_CLIENT_SECRET")
    base_url = os.getenv("AMADEUS_BASE_URL", "api.amadeus.com")
    
    print("🔍 Testing Amadeus API Authentication")
    print("=" * 60)
    print(f"Base URL: {base_url}")
    print(f"Client ID: {client_id[:10]}..." if client_id else "Client ID: Not found")
    print(f"Client Secret: {'*' * 10}" if client_secret else "Client Secret: Not found")
    
    # Test authentication
    auth_url = f"https://{base_url}/v1/security/oauth2/token"
    
    print(f"\n🔐 Testing authentication at: {auth_url}")
    
    async with httpx.AsyncClient() as client:
        try:
            # Get access token
            data = {
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret
            }
            
            response = await client.post(
                auth_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            print(f"\nResponse Status: {response.status_code}")
            
            if response.status_code == 200:
                token_data = response.json()
                print("✅ Authentication successful!")
                print(f"   Token type: {token_data.get('type')}")
                print(f"   Expires in: {token_data.get('expires_in')} seconds")
                print(f"   Token: {token_data.get('access_token')[:20]}...")
                
                # Test a simple API call
                print("\n🔍 Testing flight search endpoint...")
                
                headers = {
                    "Authorization": f"Bearer {token_data['access_token']}",
                    "Accept": "application/json"
                }
                
                params = {
                    "originLocationCode": "JFK",
                    "destinationLocationCode": "LAX",
                    "departureDate": "2025-07-15",
                    "adults": 1,
                    "max": 5
                }
                
                search_response = await client.get(
                    f"https://{base_url}/v2/shopping/flight-offers",
                    params=params,
                    headers=headers
                )
                
                print(f"Search Response Status: {search_response.status_code}")
                
                if search_response.status_code == 200:
                    data = search_response.json()
                    print(f"✅ Search successful! Found {len(data.get('data', []))} flights")
                else:
                    print(f"❌ Search failed: {search_response.text}")
                
            else:
                print(f"❌ Authentication failed!")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_amadeus_auth())