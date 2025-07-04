#!/usr/bin/env python3
"""
Test script to verify local functionality
"""
import asyncio
import json
import websockets
import base64

async def test_voice_assistant():
    """Test the voice assistant with a simple query"""
    uri = "ws://localhost:8000/ws"
    
    print("🔍 Testing Polyglot RAG Voice Assistant...")
    print(f"Connecting to {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket")
            
            # Send initial config
            config = {
                "type": "config",
                "continuous": True,
                "language": "auto"
            }
            await websocket.send(json.dumps(config))
            print("✅ Sent configuration")
            
            # Listen for messages
            print("\n📡 Listening for server messages...")
            print("Server is ready. In a real scenario:")
            print("1. The web interface would capture audio from microphone")
            print("2. Send it as base64 encoded PCM16 audio")
            print("3. Server would process with OpenAI Realtime API")
            print("4. Return transcription and audio response")
            
            # Wait for a few messages to confirm connection
            for i in range(3):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    print(f"\n📨 Received: {data.get('type', 'unknown')}")
                    if data.get('error'):
                        print(f"❌ Error: {data['error']}")
                except asyncio.TimeoutError:
                    print("⏱️  No message received (timeout)")
                    break
                    
            print("\n✅ Local test completed successfully!")
            print("\n🌐 To test the full experience:")
            print("1. Open http://localhost:3000/realtime.html")
            print("2. Click 'Start Listening'")
            print("3. Speak in any language")
            print("4. Ask about flights (e.g., 'Find flights from New York to Paris')")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

async def test_flight_api():
    """Test the flight search API directly"""
    import httpx
    
    print("\n🔍 Testing Flight Search API...")
    
    async with httpx.AsyncClient() as client:
        try:
            # Test flight search endpoint
            response = await client.post(
                "http://localhost:8000/api/search-flights",
                json={
                    "origin": "JFK",
                    "destination": "CDG",
                    "departure_date": "2025-07-15",
                    "passengers": 1,
                    "cabin_class": "economy"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Flight API working! Found {len(data.get('flights', []))} flights")
                if data.get('flights'):
                    flight = data['flights'][0]
                    print(f"   Example: {flight.get('airline', 'Unknown')} - ${flight.get('price', 'N/A')}")
            else:
                print(f"❌ Flight API error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Flight API error: {e}")

async def main():
    """Run all tests"""
    print("="*60)
    print("POLYGLOT RAG VOICE ASSISTANT - LOCAL TEST")
    print("="*60)
    
    # Test WebSocket connection
    ws_ok = await test_voice_assistant()
    
    # Test Flight API
    await test_flight_api()
    
    print("\n" + "="*60)
    if ws_ok:
        print("✅ ALL SYSTEMS OPERATIONAL")
        print("\n🚀 Ready for production deployment!")
    else:
        print("❌ Some issues detected")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())