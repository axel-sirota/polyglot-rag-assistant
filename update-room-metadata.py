#!/usr/bin/env python3
import asyncio
import os
from livekit import api
from dotenv import load_dotenv

load_dotenv()

async def update_room_metadata():
    # Create API client
    livekit_api = api.LiveKitAPI(
        'https://polyglot-rag-assistant-3l6xagej.livekit.cloud',
        os.getenv('LIVEKIT_API_KEY'),
        os.getenv('LIVEKIT_API_SECRET'),
    )
    
    room_name = 'flight-demo'
    metadata = '{"require_agent": true, "agent_name": "polyglot-flight-agent"}'
    
    try:
        # Update room metadata
        await livekit_api.room.update_room_metadata(
            api.UpdateRoomMetadataRequest(
                room=room_name,
                metadata=metadata
            )
        )
        print(f'✅ Updated room metadata for {room_name}')
        print(f'   Metadata: {metadata}')
    except Exception as e:
        print(f'❌ Error updating room: {e}')
    finally:
        await livekit_api.aclose()

if __name__ == "__main__":
    asyncio.run(update_room_metadata())