#!/usr/bin/env python3
"""
Test script for text injection functionality in LiveKit Agents
Demonstrates how to inject text without microphone input
"""
import asyncio
import json
import time
from livekit import rtc, api
import os
from dotenv import load_dotenv

load_dotenv()

# LiveKit server configuration
LIVEKIT_URL = os.getenv("LIVEKIT_URL", "ws://localhost:7880")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

# Test messages to send
TEST_MESSAGES = [
    "Find me flights from New York to Paris tomorrow",
    "What about morning flights only?",
    "Show me business class options",
    "Search for Delta Airlines flights specifically"
]


async def create_room_and_token(room_name: str, participant_name: str):
    """Create a room and generate a token for testing"""
    # Create room using LiveKit API
    room_service = api.RoomService(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
    
    # Create room with metadata
    room_metadata = json.dumps({"language": "en"})
    await room_service.create_room(
        api.CreateRoomRequest(
            name=room_name,
            metadata=room_metadata
        )
    )
    
    # Generate access token
    token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
    token.with_identity(participant_name)\
        .with_name(participant_name)\
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish_data=True,
                can_update_own_metadata=True
            )
        )
    
    return token.to_jwt()


async def test_text_injection():
    """Main test function"""
    print("🧪 LiveKit Text Injection Test")
    print("=" * 50)
    
    # Create test room
    room_name = f"test-room-{int(time.time())}"
    participant_name = f"test-user-{int(time.time())}"
    
    print(f"📍 Creating room: {room_name}")
    token = await create_room_and_token(room_name, participant_name)
    
    # Connect to room
    room = rtc.Room()
    
    @room.on("data_received")
    def on_data_received(data: bytes, participant: rtc.RemoteParticipant):
        """Handle responses from agent"""
        try:
            message = json.loads(data.decode('utf-8'))
            if message.get('type') == 'transcription':
                speaker = message.get('speaker', 'unknown')
                text = message.get('text', '')
                print(f"\n💬 {speaker.upper()}: {text}")
        except:
            pass
    
    @room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant):
        print(f"✅ Agent connected: {participant.identity}")
    
    print(f"🔌 Connecting to LiveKit...")
    await room.connect(LIVEKIT_URL, token)
    print(f"✅ Connected as {participant_name}")
    
    # Wait for agent to join
    print("⏳ Waiting for agent to join...")
    await asyncio.sleep(3)
    
    # Send test messages
    print("\n🧪 Sending test messages:")
    print("=" * 50)
    
    for i, message in enumerate(TEST_MESSAGES):
        print(f"\n📤 Test {i+1}: {message}")
        
        # Create test input message
        test_data = json.dumps({
            "type": "test_user_input",
            "text": message,
            "timestamp": int(time.time() * 1000)
        }).encode('utf-8')
        
        # Send to agent
        await room.local_participant.publish_data(test_data, reliable=True)
        
        # Wait for response
        await asyncio.sleep(10)  # Give agent time to process and respond
    
    # Test the automated harness
    print("\n🧪 Running automated test harness:")
    print("=" * 50)
    
    harness_data = json.dumps({
        "type": "run_test_harness"
    }).encode('utf-8')
    
    await room.local_participant.publish_data(harness_data, reliable=True)
    
    # Wait for harness to complete
    await asyncio.sleep(30)
    
    print("\n✅ Test complete!")
    await room.disconnect()


async def test_generate_reply_direct():
    """
    Alternative test showing how to use generate_reply directly
    This would be used within the agent code itself
    """
    print("\n📝 Example of using generate_reply within agent:")
    print("=" * 50)
    print("""
    # In your agent code:
    async def test_text_injection(session: AgentSession):
        # Interrupt any ongoing speech
        session.interrupt()
        
        # Inject text as if user spoke it
        speech_handle = await session.generate_reply(
            user_input="Find me a flight from New York to Paris tomorrow",
            instructions="Help the user find flights using the search tool",
            allow_interruptions=True
        )
        
        # Wait for agent to complete response
        await speech_handle.wait_for_completion()
        
        # Continue conversation with context maintained
        speech_handle = await session.generate_reply(
            user_input="What about morning flights only?",
            allow_interruptions=True
        )
    """)


if __name__ == "__main__":
    print("""
    🧪 LiveKit Text Injection Test Suite
    
    This script demonstrates how to inject text into the LiveKit agent
    without using a microphone. Perfect for testing in noisy environments!
    
    The agent must be running and connected to LiveKit.
    """)
    
    # Run the test
    asyncio.run(test_text_injection())
    
    # Show direct usage example
    asyncio.run(test_generate_reply_direct())