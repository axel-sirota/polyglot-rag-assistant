#!/bin/bash
# Start demo with OpenAI Realtime Voice

echo "🎙️ Starting Polyglot Voice Assistant (OpenAI Realtime)"
echo "===================================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Kill any existing processes
echo -e "${YELLOW}Stopping any existing services...${NC}"
pkill -f "flight_search_api.py" 2>/dev/null
pkill -f "realtime_gradio_app.py" 2>/dev/null
pkill -f "realtime_voice_agent.py" 2>/dev/null
sleep 2

# Create logs directory
mkdir -p logs

# 1. Start Flight Search API
echo -e "${GREEN}1. Starting Flight Search API...${NC}"
.venv/bin/python3 mcp_servers/flight_search_api.py > logs/flight_api_realtime.log 2>&1 &
FLIGHT_PID=$!
sleep 3

# 2. Start Realtime Gradio Interface
echo -e "${GREEN}2. Starting Realtime Voice Interface...${NC}"
.venv/bin/python3 frontend/realtime_gradio_app.py &
GRADIO_PID=$!

echo -e "${GREEN}All services started!${NC}"
echo ""
echo "================================"
echo -e "${BLUE}Access the Voice Assistant at:${NC}"
echo "- Local: http://localhost:7860"
echo "- Public: Check terminal for Gradio share link"
echo ""
echo -e "${YELLOW}For LiveKit deployment:${NC}"
echo "livekit-cli dev --agent-config agents/realtime_voice_agent.py"
echo ""
echo "Press Ctrl+C to stop all services"
echo "================================"

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Shutting down...${NC}"
    kill $FLIGHT_PID 2>/dev/null
    kill $GRADIO_PID 2>/dev/null
    pkill -f "realtime" 2>/dev/null
    echo -e "${GREEN}Stopped all services${NC}"
    exit 0
}

trap cleanup INT TERM

# Keep running
wait $GRADIO_PID