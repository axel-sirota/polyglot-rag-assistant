#!/usr/bin/env python3
"""Test creating a room with metadata to trigger agent dispatch"""
import os
from livekit import api
from dotenv import load_dotenv
import asyncio
import json

load_dotenv()

async def create_room_with_agent():
    # Initialize LiveKit API
    lkapi = api.LiveKitAPI(
        url=os.getenv('LIVEKIT_URL'),
        api_key=os.getenv('LIVEKIT_API_KEY'),
        api_secret=os.getenv('LIVEKIT_API_SECRET')
    )
    
    room_name = "test-agent-room"
    
    try:
        # Create room with metadata
        room = await lkapi.room.create_room(
            api.CreateRoomRequest(
                name=room_name,
                metadata=json.dumps({
                    "require_agent": True,
                    "agent_name": "polyglot-flight-agent"
                }),
                empty_timeout=300,  # 5 minutes
                max_participants=10
            )
        )
        
        print(f"Room created: {room.name}")
        print(f"Room metadata: {room.metadata}")
        
        # Generate a token to join
        token = api.AccessToken(
            api_key=os.getenv('LIVEKIT_API_KEY'),
            api_secret=os.getenv('LIVEKIT_API_SECRET')
        ).with_identity("test-user") \
         .with_name("Test User") \
         .with_grants(api.VideoGrants(
             room_join=True,
             room=room_name,
             can_publish=True,
             can_subscribe=True
         )).to_jwt()
        
        print(f"\nToken generated for room '{room_name}'")
        print(f"Token: {token[:50]}...")
        print(f"\nUse this token to join the room and test if agent joins")
        
    finally:
        await lkapi.aclose()

if __name__ == "__main__":
    asyncio.run(create_room_with_agent())