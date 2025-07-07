#!/usr/bin/env python3
"""Check LiveKit room metadata"""

import os
from dotenv import load_dotenv
from livekit import api

load_dotenv()

# Create room service client
room_service = api.RoomServiceClient(
    "https://polyglot-rag-assistant-3l6xagej.livekit.cloud",
    api_key=os.getenv("LIVEKIT_API_KEY"),
    api_secret=os.getenv("LIVEKIT_API_SECRET")
)

# List rooms
rooms = room_service.list_rooms()
print("Current rooms:")
for room in rooms:
    print(f"\nRoom: {room.name}")
    print(f"  SID: {room.sid}")
    print(f"  Metadata: '{room.metadata}'")
    print(f"  Participants: {room.num_participants}")
    
    # If it's the flight-demo room, show participants
    if room.name == "flight-demo":
        participants = room_service.list_participants(room.name)
        for p in participants:
            print(f"  - Participant: {p.identity}")
            print(f"    Metadata: '{p.metadata}'")