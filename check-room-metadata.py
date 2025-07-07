#!/usr/bin/env python3
"""Check LiveKit room metadata"""

import os
import asyncio
from dotenv import load_dotenv
from livekit import api

load_dotenv()

async def check_rooms():
    # Initialize LiveKitAPI
    lkapi = api.LiveKitAPI(
        "https://polyglot-rag-assistant-3l6xagej.livekit.cloud",
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET")
    )
    
    try:
        # List rooms
        rooms = await lkapi.room.list_rooms(api.ListRoomsRequest())
        print("Current rooms:")
        for room in rooms.rooms:
            print(f"\nRoom: {room.name}")
            print(f"  SID: {room.sid}")
            print(f"  Metadata: '{room.metadata}'")
            print(f"  Participants: {room.num_participants}")
            
            # Show participants for flight-demo rooms
            if room.name.startswith("flight-demo"):
                participants = await lkapi.room.list_participants(
                    api.ListParticipantsRequest(room=room.name)
                )
                for p in participants.participants:
                    print(f"  - Participant: {p.identity}")
                    print(f"    Metadata: '{p.metadata}'")
    finally:
        await lkapi.aclose()

asyncio.run(check_rooms())