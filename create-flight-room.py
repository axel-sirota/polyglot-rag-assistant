#!/usr/bin/env python3
"""Create flight-assistant room with proper metadata"""
import os
from livekit import api
from dotenv import load_dotenv
import asyncio
import json

load_dotenv()

async def setup_flight_room():
    # Initialize LiveKit API
    lkapi = api.LiveKitAPI(
        url=os.getenv('LIVEKIT_URL'),
        api_key=os.getenv('LIVEKIT_API_KEY'),
        api_secret=os.getenv('LIVEKIT_API_SECRET')
    )
    
    room_name = "flight-demo"  # New room name
    
    try:
        # First, try to delete existing room if it exists
        try:
            await lkapi.room.delete_room(api.DeleteRoomRequest(room=room_name))
            print(f"Deleted existing room: {room_name}")
        except:
            pass
        
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
        print(f"\nUpdate your UI to use room name: '{room_name}'")
        
    finally:
        await lkapi.aclose()

if __name__ == "__main__":
    asyncio.run(setup_flight_room())