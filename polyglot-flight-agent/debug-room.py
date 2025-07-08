#!/usr/bin/env python3
import os
import asyncio
from livekit import api
from dotenv import load_dotenv

load_dotenv("../.env")

async def debug_room():
    # Create LiveKit API client
    livekit_api = api.LiveKitAPI(
        os.getenv("LIVEKIT_URL", "wss://polyglot-rag-assistant-3l6xagej.livekit.cloud"),
        os.getenv("LIVEKIT_API_KEY"),
        os.getenv("LIVEKIT_API_SECRET")
    )
    
    # List all rooms
    print("=== LISTING ALL ROOMS ===")
    rooms = await livekit_api.room.list_rooms()
    
    if not rooms:
        print("No rooms found")
        return
        
    for room in rooms:
        print(f"\nRoom: {room.name}")
        print(f"  SID: {room.sid}")
        print(f"  Participants: {room.num_participants}")
        print(f"  Empty timeout: {room.empty_timeout}")
        print(f"  Max participants: {room.max_participants}")
        print(f"  Metadata: {room.metadata}")
        
        # List participants in the room
        participants = await livekit_api.room.list_participants(room.name)
        for p in participants:
            print(f"  - Participant: {p.identity} (SID: {p.sid})")
            print(f"    State: {p.state}")
            print(f"    Metadata: {p.metadata}")

if __name__ == "__main__":
    asyncio.run(debug_room())