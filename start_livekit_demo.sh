#!/bin/bash
# Quick LiveKit Voice Assistant Demo

echo "🎤 Starting LiveKit Voice Assistant Demo"
echo "========================================"

# Kill any existing processes
pkill -f "livekit_voice_assistant.py"
pkill -f "flight_search_api.py"

# Start Flight API
echo "1. Starting Flight Search API..."
.venv/bin/python3 mcp_servers/flight_search_api.py &
FLIGHT_PID=$!
sleep 3

# Start LiveKit Agent
echo "2. Starting LiveKit Voice Assistant..."
echo ""
echo "To test your agent:"
echo "1. Go to: https://agents-playground.livekit.io/"
echo "2. Click 'Continue with LiveKit Cloud'"
echo "3. Or use the test web app (starting next)"
echo ""

# Run the agent
.venv/bin/python3 livekit_voice_assistant.py &
AGENT_PID=$!

echo ""
echo "================================"
echo "🎉 Voice Assistant is running!"
echo ""
echo "Test it at: https://agents-playground.livekit.io/"
echo "Or use LiveKit's React components"
echo ""
echo "Press Ctrl+C to stop"
echo "================================"

# Cleanup on exit
trap "kill $FLIGHT_PID $AGENT_PID 2>/dev/null; exit" INT TERM

# Keep running
wait