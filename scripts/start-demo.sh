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

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo -e "${YELLOW}Warning: .env file not found${NC}"
fi

# Start services in background
echo -e "${GREEN}Starting services...${NC}"

# Create logs directory if it doesn't exist
mkdir -p logs

# 1. Start MCP server (if available)
echo "1. Starting MCP Flight Search Server..."
(.venv/bin/python3 mcp_servers/flight_search_server.py &)
MCP_PID=$!

# 2. Start main orchestrator
echo "2. Starting Main Orchestrator..."
(.venv/bin/python3 main.py &)
ORCHESTRATOR_PID=$!

# 3. Start Gradio interface
echo "3. Starting Gradio Web Interface..."
echo -e "${YELLOW}Gradio will create a public URL for testing${NC}"
.venv/bin/python3 frontend/gradio_app.py &
GRADIO_PID=$!

echo -e "${GREEN}All services started. Check logs/ directory for detailed logs${NC}"

# Wait for Gradio to start
sleep 5

# 4. Handle ngrok tunnel
echo -e "${GREEN}4. Checking ngrok status...${NC}"

# Check if ngrok is already running and get details
NGROK_INFO=$(curl -s localhost:4040/api/tunnels 2>/dev/null || echo "{}")
EXISTING_NGROK=$(echo "$NGROK_INFO" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['tunnels'][0]['public_url'] if 'tunnels' in data and data['tunnels'] else '')" 2>/dev/null || echo "")
NGROK_PORT=$(echo "$NGROK_INFO" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['tunnels'][0]['config']['addr'].split(':')[-1] if 'tunnels' in data and data['tunnels'] else '')" 2>/dev/null || echo "")

if [ ! -z "$EXISTING_NGROK" ]; then
    if [ "$NGROK_PORT" = "7860" ]; then
        echo -e "${GREEN}✅ Ngrok is already running and correctly configured!${NC}"
        echo -e "${GREEN}   URL: ${EXISTING_NGROK}${NC}"
        NGROK_URL="$EXISTING_NGROK"
    else
        echo -e "${YELLOW}⚠️  Ngrok is running but forwarding to port ${NGROK_PORT}${NC}"
        echo -e "${YELLOW}   Current URL: ${EXISTING_NGROK}${NC}"
        echo -e "${YELLOW}   To use with Gradio (port 7860):${NC}"
        echo -e "${YELLOW}   1. Stop ngrok (Ctrl+C in ngrok terminal)${NC}"
        echo -e "${YELLOW}   2. Run: ./scripts/setup-ngrok.sh${NC}"
        NGROK_URL=""
    fi
else
    # Check if ngrok is installed
    if command -v ngrok &> /dev/null; then
        echo -e "${GREEN}Starting ngrok tunnel...${NC}"
        
        # Check for ngrok config
        if [ -f "ngrok.yml" ]; then
            echo -e "${BLUE}Using ngrok.yml configuration${NC}"
        fi
        
        # Start ngrok pointing to Gradio port
        ngrok http 7860 --log=stdout > logs/ngrok.log 2>&1 &
        NGROK_PID=$!
        sleep 5
        
        # Get ngrok URL
        NGROK_URL=$(curl -s localhost:4040/api/tunnels 2>/dev/null | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['tunnels'][0]['public_url'] if 'tunnels' in data and data['tunnels'] else '')" 2>/dev/null || echo "")
        
        if [ ! -z "$NGROK_URL" ]; then
            echo -e "${GREEN}Ngrok URL: ${NGROK_URL}${NC}"
        else
            echo -e "${YELLOW}Ngrok started but URL not available yet${NC}"
        fi
    else
        echo -e "${YELLOW}ngrok not found. Install with: brew install ngrok/ngrok/ngrok${NC}"
        NGROK_URL=""
    fi
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
if [ ! -z "$NGROK_URL" ]; then
    echo "  - Or use your ngrok URL: ${NGROK_URL}"
fi
echo ""
echo "Press Ctrl+C to stop all services"
echo "================================"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down services...${NC}"
    
    # Kill specific PIDs if available
    [ ! -z "$GRADIO_PID" ] && kill $GRADIO_PID 2>/dev/null
    [ ! -z "$ORCHESTRATOR_PID" ] && kill $ORCHESTRATOR_PID 2>/dev/null
    [ ! -z "$MCP_PID" ] && kill $MCP_PID 2>/dev/null
    [ ! -z "$NGROK_PID" ] && kill $NGROK_PID 2>/dev/null
    
    # Also kill by name as backup
    pkill -f "python.*gradio_app.py" 2>/dev/null
    pkill -f "python.*main.py" 2>/dev/null
    pkill -f "python.*flight_search_server.py" 2>/dev/null
    
    echo -e "${GREEN}Demo stopped.${NC}"
    echo -e "${BLUE}Check logs/ directory for session logs${NC}"
    exit 0
}

# Set up trap for cleanup
trap cleanup INT TERM

# Keep script running
wait $GRADIO_PID