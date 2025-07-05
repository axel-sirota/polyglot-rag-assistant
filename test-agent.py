#!/usr/bin/env python3
"""Test script to verify agent connection"""
import asyncio
import os
from livekit import api
from dotenv import load_dotenv

load_dotenv()

async def test_agent():
    # Generate a token
    token = api.AccessToken(
        api_key=os.getenv('LIVEKIT_API_KEY'),
        api_secret=os.getenv('LIVEKIT_API_SECRET')
    ).with_identity("test-user") \
     .with_name("Test User") \
     .with_grants(api.VideoGrants(
         room_join=True,
         room="flight-assistant",
         can_publish=True,
         can_subscribe=True
     )).to_jwt()
    
    print(f"Token generated for room 'flight-assistant'")
    print(f"Token: {token[:50]}...")
    
    # Check if agent is needed
    print("\nTo test:")
    print("1. Make sure agent is running: docker logs polyglot-agent-test")
    print("2. Use this token to join the room")
    print("3. Agent should automatically join")

if __name__ == "__main__":
    asyncio.run(test_agent())