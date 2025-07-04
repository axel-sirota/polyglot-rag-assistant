#!/bin/bash
# Clean test with new room

echo "🧹 Cleaning up..."
pkill -9 -f livekit-server 2>/dev/null
pkill -9 -f python 2>/dev/null
sleep 2

echo "🚀 Starting fresh..."

# Start LiveKit server
echo "1. Starting LiveKit server (dev mode)..."
livekit-server --dev --bind 127.0.0.1 &
LIVEKIT_PID=$!
sleep 5

# Test server is running
echo "2. Testing server..."
curl -s http://localhost:7880/healthz || echo "Server not ready"

# Start agent
echo "3. Starting agent..."
cd /Users/axelsirota/repos/polyglot-rag-assistant
LIVEKIT_URL=ws://localhost:7880 \
LIVEKIT_API_KEY=devkey \
LIVEKIT_API_SECRET=secret \
.venv/bin/python3 working_voice_agent.py dev &
AGENT_PID=$!

sleep 3

# Create a new room with unique name
ROOM_NAME="test-$(date +%s)"

echo ""
echo "✅ Everything running!"
echo ""
echo "Join at: https://meet.livekit.io"
echo ""
echo "Connection settings:"
echo "  LiveKit URL: ws://localhost:7880"
echo "  API Key: devkey"
echo "  API Secret: secret"
echo "  Room name: $ROOM_NAME"
echo ""
echo "Or use this test page:"
echo "http://localhost:7880/test-page?room=$ROOM_NAME"
echo ""
echo "Press Ctrl+C to stop"

trap "kill $LIVEKIT_PID $AGENT_PID 2>/dev/null; exit" INT
wait