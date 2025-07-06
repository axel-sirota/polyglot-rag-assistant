#!/usr/bin/env python3
"""Test LiveKit connection and room joining"""
import asyncio
import os
from dotenv import load_dotenv
from livekit import api
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_connection():
    """Test LiveKit connection"""
    # Get credentials
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    ws_url = os.getenv("LIVEKIT_WS_URL", "wss://polyglot-rag-assistant-3l6xagej.livekit.cloud")
    
    logger.info(f"Testing connection to: {ws_url}")
    logger.info(f"API Key: {api_key[:10]}...")
    
    # Create access token
    token = api.AccessToken(api_key, api_secret)
    token = token.with_identity("test-participant").with_name("Test Participant")
    grant = api.VideoGrant()
    grant.room_join = True
    grant.room = "flight-demo"
    token = token.with_grants(grant)
    
    jwt_token = token.to_jwt()
    logger.info(f"Generated token: {jwt_token[:50]}...")
    
    # Test room creation
    room_service = api.RoomService(ws_url, api_key, api_secret)
    
    try:
        # List rooms
        rooms = await room_service.list_rooms()
        logger.info(f"Found {len(rooms)} rooms")
        for room in rooms:
            logger.info(f"  Room: {room.name}, Participants: {room.num_participants}")
        
        # Create or get room
        try:
            room = await room_service.create_room(api.CreateRoomRequest(name="flight-demo"))
            logger.info(f"Created room: {room.name}")
        except Exception as e:
            logger.info(f"Room might already exist: {e}")
            
    except Exception as e:
        logger.error(f"Failed to connect: {e}")
        raise
    
    logger.info("✅ LiveKit connection test successful!")

if __name__ == "__main__":
    asyncio.run(test_connection())