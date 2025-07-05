#!/usr/bin/env python3
"""
Test script to run the agent locally for debugging
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set environment variables for local testing
os.environ['LIVEKIT_URL'] = os.getenv('LIVEKIT_URL', 'wss://polyglot-rag-assistant-3l6xagej.livekit.cloud')
os.environ['API_SERVER_URL'] = os.getenv('API_SERVER_URL', 'http://localhost:8000')

# Import and run the agent
from agent import cli, WorkerOptions, entrypoint, prewarm

if __name__ == "__main__":
    print("Starting LiveKit agent locally...")
    print(f"LiveKit URL: {os.getenv('LIVEKIT_URL')}")
    print(f"API Server: {os.getenv('API_SERVER_URL')}")
    
    # Run the agent
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm
        )
    )