#!/usr/bin/env python3
"""Generate a test token for LiveKit"""
import os
from dotenv import load_dotenv
from livekit import api

load_dotenv()

# Get credentials
api_key = os.getenv("LIVEKIT_API_KEY")
api_secret = os.getenv("LIVEKIT_API_SECRET")

# Create access token
token = api.AccessToken(api_key, api_secret)
token = token.with_identity("test-user").with_name("Test User")

# Grant permissions
grant = api.VideoGrants(
    room_join=True,
    room="flight-demo",
    can_publish=True,
    can_subscribe=True
)

token = token.with_grants(grant)

# Generate JWT
jwt_token = token.to_jwt()

print("\n🎫 Your test token:")
print("=" * 80)
print(jwt_token)
print("=" * 80)
print("\n📋 Copy this token and use it in test_trigger.html")
print(f"\n🌐 LiveKit URL: wss://polyglot-rag-assistant-3l6xagej.livekit.cloud")
print(f"🏠 Room: flight-demo")