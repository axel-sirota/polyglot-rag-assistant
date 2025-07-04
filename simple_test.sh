#!/bin/bash
# Simple test with minimal setup

echo "🎤 Simple Voice Assistant Test"
echo "=============================="

# Kill any existing processes
pkill -9 -f livekit-server 2>/dev/null
pkill -9 -f python 2>/dev/null
sleep 2

# Start LiveKit server
echo "1. Starting LiveKit server..."
livekit-server --dev &
LIVEKIT_PID=$!
echo "   LiveKit PID: $LIVEKIT_PID"
sleep 5

# Check if server is running
echo "2. Checking server..."
curl -s http://localhost:7880/healthz && echo "   ✅ Server is healthy!" || echo "   ❌ Server not responding"

# Start agent
echo "3. Starting agent..."
cd /Users/axelsirota/repos/polyglot-rag-assistant
export LIVEKIT_URL=ws://localhost:7880
export LIVEKIT_API_KEY=devkey
export LIVEKIT_API_SECRET=secret
.venv/bin/python3 working_voice_agent.py dev &
AGENT_PID=$!
echo "   Agent PID: $AGENT_PID"

sleep 3

echo ""
echo "✅ Everything should be running!"
echo ""
echo "To test:"
echo "1. Go to: https://meet.livekit.io"
echo "2. Custom tab"
echo "3. Enter:"
echo "   URL: ws://localhost:7880"
echo "   API Key: devkey"
echo "   API Secret: secret"
echo "4. Join any room name"
echo ""
echo "You should hear: 'Hello! I'm your voice assistant...'"
echo ""
echo "Press Ctrl+C to stop"

# Cleanup on exit
trap "kill $LIVEKIT_PID $AGENT_PID 2>/dev/null; exit" INT

# Keep script running
while true; do
    sleep 1
done