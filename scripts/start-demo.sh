#!/bin/bash
# Quick demo launcher for Polyglot RAG Assistant

echo "🚀 Starting Polyglot RAG Demo..."
echo "================================"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get local IP address
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    LOCAL_IP=$(ipconfig getifaddr en0 || ipconfig getifaddr en1)
else
    # Linux
    LOCAL_IP=$(hostname -I | awk '{print $1}')
fi

echo -e "${BLUE}Your local IP: ${LOCAL_IP}${NC}"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies if needed
echo -e "${YELLOW}Checking dependencies...${NC}"
pip install -q python-dotenv

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo -e "${YELLOW}Warning: .env file not found${NC}"
fi

# Start services in background
echo -e "${GREEN}Starting services...${NC}"

# 1. Start MCP server (if available)
echo "1. Starting MCP Flight Search Server..."
(.venv/bin/python3 mcp_servers/flight_search_server.py 2>/dev/null &)

# 2. Start main orchestrator
echo "2. Starting Main Orchestrator..."
(.venv/bin/python3 main.py > logs/orchestrator.log 2>&1 &)

# 3. Start Gradio interface
echo "3. Starting Gradio Web Interface..."
echo -e "${YELLOW}Gradio will create a public URL for testing${NC}"
.venv/bin/python3 frontend/gradio_app.py &
GRADIO_PID=$!

# Wait for Gradio to start
sleep 5

# 4. Create ngrok tunnel for local network access
if command -v ngrok &> /dev/null; then
    echo -e "${GREEN}4. Creating ngrok tunnel...${NC}"
    ngrok http 7860 --log=stdout > logs/ngrok.log 2>&1 &
    NGROK_PID=$!
    sleep 3
    
    # Get ngrok URL
    NGROK_URL=$(curl -s localhost:4040/api/tunnels | python3 -c "import sys, json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])" 2>/dev/null || echo "")
    
    if [ ! -z "$NGROK_URL" ]; then
        echo -e "${GREEN}Ngrok URL: ${NGROK_URL}${NC}"
    fi
else
    echo -e "${YELLOW}ngrok not found. Install with: brew install ngrok${NC}"
fi

echo ""
echo "================================"
echo -e "${GREEN}🎉 Demo is running!${NC}"
echo ""
echo "Access the app:"
echo -e "1. ${BLUE}Local:${NC} http://localhost:7860"
echo -e "2. ${BLUE}Network:${NC} http://${LOCAL_IP}:7860"
echo -e "3. ${BLUE}Public (Gradio):${NC} Check terminal for share link"
if [ ! -z "$NGROK_URL" ]; then
    echo -e "4. ${BLUE}Ngrok:${NC} ${NGROK_URL}"
fi
echo ""
echo "📱 To test on phone:"
echo "  - Use the Gradio share link (easiest)"
echo "  - Or connect to same WiFi and use http://${LOCAL_IP}:7860"
echo ""
echo "Press Ctrl+C to stop all services"
echo "================================"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down services...${NC}"
    pkill -f "python.*gradio_app.py"
    pkill -f "python.*main.py"
    pkill -f "python.*flight_search_server.py"
    if [ ! -z "$NGROK_PID" ]; then
        kill $NGROK_PID 2>/dev/null
    fi
    echo -e "${GREEN}Demo stopped.${NC}"
    exit 0
}

# Set up trap for cleanup
trap cleanup INT TERM

# Keep script running
wait $GRADIO_PID