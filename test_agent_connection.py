#!/usr/bin/env python3
"""Test if agent is properly connected and responding"""

import asyncio
from livekit import api
import os
from dotenv import load_dotenv

load_dotenv()

async def test_agent():
    # Create a room
    livekit_api = api.LiveKitAPI(
        'ws://localhost:7880',
        'devkey',
        'secret'
    )
    
    # Create or get room
    room_name = "test-room"
    try:
        rooms = await livekit_api.room.list_rooms()
        print(f"Existing rooms: {[r.name for r in rooms]}")
        
        # Create room if doesn't exist
        room_exists = any(r.name == room_name for r in rooms)
        if not room_exists:
            await livekit_api.room.create_room(api.CreateRoomRequest(name=room_name))
            print(f"Created room: {room_name}")
        else:
            print(f"Room already exists: {room_name}")
            
        # List participants
        participants = await livekit_api.room.list_participants(api.ListParticipantsRequest(room=room_name))
        print(f"Participants in room: {[p.identity for p in participants]}")
        
        # Create a token for user
        token = api.AccessToken('devkey', 'secret') \
            .with_identity('test-user') \
            .with_name('Test User') \
            .with_grants(api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True
            ))
        
        jwt = token.to_jwt()
        print(f"\nJoin the room with this token:")
        print(f"URL: ws://localhost:7880")
        print(f"Token: {jwt}")
        print(f"\nOr join at: https://meet.livekit.io")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_agent())