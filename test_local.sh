#!/bin/bash
# Quick local test script

echo "🧪 Testing Polyglot Voice Assistant Locally"
echo "=========================================="

# Check requirements
echo "Checking requirements..."
command -v livekit-server >/dev/null 2>&1 || { 
    echo "❌ livekit-server not found. Install with: brew install livekit"
    echo "   Or download from: https://github.com/livekit/livekit/releases"
    exit 1
}

# Kill any existing processes
echo "Cleaning up old processes..."
pkill -f "livekit-server" 2>/dev/null
pkill -f "flight_search_api" 2>/dev/null
pkill -f "livekit_voice_assistant" 2>/dev/null
sleep 2

# Start LiveKit server in dev mode
echo "1. Starting local LiveKit server..."
livekit-server --dev --bind 0.0.0.0 > logs/livekit-server.log 2>&1 &
LIVEKIT_PID=$!
sleep 3

# Start Flight API
echo "2. Starting Flight Search API..."
.venv/bin/python3 mcp_servers/flight_search_api.py > logs/flight-api-local.log 2>&1 &
FLIGHT_PID=$!
sleep 2

# Start the agent
echo "3. Starting Voice Agent..."
LIVEKIT_URL=ws://localhost:7880 \
LIVEKIT_API_KEY=devkey \
LIVEKIT_API_SECRET=secret \
.venv/bin/python3 livekit_voice_assistant.py dev > logs/agent-local.log 2>&1 &
AGENT_PID=$!

sleep 3

echo ""
echo "✅ Everything is running!"
echo ""
echo "Test your agent:"
echo "1. Open: https://meet.livekit.io"
echo "2. Settings → Custom Server"
echo "   - URL: ws://localhost:7880"
echo "   - API Key: devkey"
echo "   - API Secret: secret"
echo "3. Join room and start talking!"
echo ""
echo "Or use CLI to create a test room:"
echo "lk room create --name test-room --url ws://localhost:7880 --api-key devkey --api-secret secret"
echo ""
echo "Then join with token:"
echo "lk token create --join --room test-room --identity user --url ws://localhost:7880 --api-key devkey --api-secret secret"
echo ""
echo "Logs:"
echo "- LiveKit: tail -f logs/livekit-server.log"
echo "- Agent: tail -f logs/agent-local.log"
echo "- Flight API: tail -f logs/flight-api-local.log"
echo ""
echo "Press Ctrl+C to stop all services"

# Cleanup function
cleanup() {
    echo -e "\nStopping services..."
    kill $LIVEKIT_PID $FLIGHT_PID $AGENT_PID 2>/dev/null
    pkill -f "livekit-server" 2>/dev/null
    echo "✅ Stopped all services"
    exit 0
}

trap cleanup INT TERM
wait