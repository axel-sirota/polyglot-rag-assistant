#!/usr/bin/env python3
"""List all active rooms in LiveKit Cloud"""
import os
from livekit import api
from dotenv import load_dotenv
import asyncio

load_dotenv()

async def list_rooms():
    # Initialize LiveKit API
    lkapi = api.LiveKitAPI(
        url=os.getenv('LIVEKIT_URL'),
        api_key=os.getenv('LIVEKIT_API_KEY'),
        api_secret=os.getenv('LIVEKIT_API_SECRET')
    )
    
    try:
        # List all rooms
        response = await lkapi.room.list_rooms(api.ListRoomsRequest())
        rooms = response.rooms
        
        print(f"Found {len(rooms)} active rooms:\n")
        for room in rooms:
            print(f"Room: {room.name}")
            print(f"  SID: {room.sid}")
            print(f"  Participants: {room.num_participants}")
            print(f"  Created: {room.creation_time}")
            print(f"  Metadata: {room.metadata}")
            print()
            
    finally:
        await lkapi.aclose()

if __name__ == "__main__":
    asyncio.run(list_rooms())