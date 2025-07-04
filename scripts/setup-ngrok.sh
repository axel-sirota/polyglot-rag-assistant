#!/bin/bash
# Setup ngrok for Gradio app

echo "🔧 Ngrok Setup for Polyglot RAG"
echo "==============================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if ngrok is running
CURRENT_TUNNEL=$(curl -s localhost:4040/api/tunnels 2>/dev/null | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['tunnels'][0]['config']['addr'] if 'tunnels' in data and data['tunnels'] else '')" 2>/dev/null || echo "")

if [ ! -z "$CURRENT_TUNNEL" ]; then
    echo -e "${YELLOW}Ngrok is currently running and forwarding to: ${CURRENT_TUNNEL}${NC}"
    echo ""
    echo "To use with Gradio (port 7860):"
    echo "1. Press Ctrl+C in the ngrok terminal to stop it"
    echo "2. Run this script again"
    exit 0
fi

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo -e "${YELLOW}Ngrok not installed!${NC}"
    echo "Install with: brew install ngrok/ngrok/ngrok"
    exit 1
fi

# Check for authtoken
if [ -f "ngrok.yml" ]; then
    echo -e "${GREEN}Found ngrok.yml configuration${NC}"
    AUTHTOKEN=$(grep authtoken ngrok.yml | awk '{print $2}')
    if [ ! -z "$AUTHTOKEN" ]; then
        echo "Authtoken found: ${AUTHTOKEN:0:10}..."
    fi
fi

# Start ngrok for Gradio
echo ""
echo -e "${GREEN}Starting ngrok tunnel for Gradio (port 7860)...${NC}"
echo ""

# Run ngrok
ngrok http 7860

# Note: ngrok will take over the terminal, so this won't execute until ngrok stops
echo -e "${YELLOW}Ngrok stopped.${NC}"