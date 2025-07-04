#!/usr/bin/env python3
"""
LiveKit Agent Entry Point
This file is required by LiveKit Cloud deployment
"""

# Import the actual agent implementation
from realtime_agent import entrypoint, WorkerOptions
import os
from livekit.agents import cli

if __name__ == "__main__":
    # Run the agent using LiveKit CLI
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            api_key=os.getenv("LIVEKIT_API_KEY"),
            api_secret=os.getenv("LIVEKIT_API_SECRET"),
            ws_url=os.getenv("LIVEKIT_URL"),
        )
    )