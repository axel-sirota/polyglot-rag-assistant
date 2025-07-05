#!/usr/bin/env python3
"""
Debug script for testing LiveKit agent audio processing
"""
import os
import logging
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Test imports
print("Testing imports...")
try:
    from livekit.agents import cli, WorkerOptions
    print("✅ LiveKit agents imported successfully")
except Exception as e:
    print(f"❌ Failed to import LiveKit agents: {e}")
    exit(1)

# Test environment variables
print("\nChecking environment variables...")
required_vars = [
    "LIVEKIT_API_KEY",
    "LIVEKIT_API_SECRET", 
    "LIVEKIT_URL",
    "OPENAI_API_KEY",
    "API_SERVER_URL"
]

for var in required_vars:
    value = os.getenv(var)
    if value:
        print(f"✅ {var}: {'*' * 10}{value[-4:]}")
    else:
        print(f"❌ {var}: Not set")

# Test API connectivity
print("\nTesting API connectivity...")
import aiohttp

async def test_api():
    api_url = os.getenv('API_SERVER_URL', 'http://localhost:8000')
    print(f"Testing connection to: {api_url}")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test health endpoint
            async with session.get(f"{api_url}/health", timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ API Server is healthy: {data}")
                else:
                    print(f"❌ API Server returned: {response.status}")
            
            # Test flight search endpoint
            async with session.get(
                f"{api_url}/api/flights",
                params={
                    "origin": "NYC",
                    "destination": "LAX",
                    "departure_date": "2025-07-10"
                },
                timeout=10
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Flight search works: {data.get('count', 0)} flights found")
                else:
                    print(f"❌ Flight search failed: {response.status}")
                    
    except aiohttp.ClientError as e:
        print(f"❌ Connection error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

# Test LiveKit connection
print("\nTesting LiveKit connection...")
from livekit import api

async def test_livekit():
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    livekit_url = os.getenv("LIVEKIT_URL", "wss://polyglot-rag-assistant-3l6xagej.livekit.cloud")
    
    if not api_key or not api_secret:
        print("❌ LiveKit credentials not set")
        return
    
    try:
        # Create a test token
        token = api.AccessToken(
            api_key=api_key,
            api_secret=api_secret
        ).with_identity(
            "test-user"
        ).with_grants(
            api.VideoGrants(
                room_join=True,
                room="test-room"
            )
        )
        
        jwt = token.to_jwt()
        print(f"✅ Token generated successfully: {jwt[:50]}...")
        
        # Try to list rooms
        from livekit.api import RoomServiceClient
        room_service = RoomServiceClient(
            host=livekit_url.replace("wss://", "https://").replace("ws://", "http://"),
            api_key=api_key,
            api_secret=api_secret
        )
        
        rooms = await room_service.list_rooms(api.ListRoomsRequest())
        print(f"✅ Connected to LiveKit Cloud, {len(rooms.rooms)} active rooms")
        
    except Exception as e:
        print(f"❌ LiveKit connection failed: {e}")

# Test VAD loading
print("\nTesting VAD loading...")
try:
    from livekit.plugins import silero
    vad = silero.VAD.load(force_cpu=True)
    print("✅ VAD loaded successfully")
except Exception as e:
    print(f"❌ VAD loading failed: {e}")

# Test OpenAI Realtime
print("\nTesting OpenAI Realtime...")
try:
    from livekit.plugins import openai
    # Just test import, don't create client yet
    print("✅ OpenAI plugin imported successfully")
except Exception as e:
    print(f"❌ OpenAI plugin import failed: {e}")

# Run all async tests
async def main():
    await test_api()
    await test_livekit()

if __name__ == "__main__":
    print("\n" + "="*50)
    print("Running diagnostic tests...")
    print("="*50 + "\n")
    
    asyncio.run(main())
    
    print("\n" + "="*50)
    print("Diagnostic complete!")
    print("="*50)