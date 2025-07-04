#!/bin/bash
# Quick test with working agent

echo "🎤 Starting Voice Assistant Test"
echo "================================"

# Start LiveKit server
echo "1. Starting LiveKit server..."
livekit-server --dev > logs/livekit-test.log 2>&1 &
LIVEKIT_PID=$!
sleep 3

# Start the working agent
echo "2. Starting voice agent..."
LIVEKIT_URL=ws://localhost:7880 \
LIVEKIT_API_KEY=devkey \
LIVEKIT_API_SECRET=secret \
.venv/bin/python3 working_voice_agent.py dev &
AGENT_PID=$!

sleep 3

echo ""
echo "✅ Ready to test!"
echo ""
echo "Join at: https://meet.livekit.io"
echo "Settings:"
echo "  URL: ws://localhost:7880"
echo "  API Key: devkey"  
echo "  API Secret: secret"
echo ""
echo "The agent will greet you when you join!"
echo ""
echo "Press Ctrl+C to stop"

trap "kill $LIVEKIT_PID $AGENT_PID 2>/dev/null; exit" INT
wait