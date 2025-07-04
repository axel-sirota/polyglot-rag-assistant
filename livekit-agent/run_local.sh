#!/bin/bash
# Run LiveKit Agent locally for development

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 Starting Polyglot Flight Assistant (LiveKit Agent) locally${NC}"

# Load environment variables
if [ -f "../.env" ]; then
    export $(cat ../.env | grep -v '^#' | xargs)
else
    echo -e "${RED}❌ No .env file found!${NC}"
    exit 1
fi

# Check for required environment variables
if [ -z "$LIVEKIT_API_KEY" ] || [ -z "$LIVEKIT_API_SECRET" ]; then
    echo -e "${RED}❌ Missing LiveKit credentials!${NC}"
    echo "Please set LIVEKIT_API_KEY and LIVEKIT_API_SECRET in your .env file"
    echo ""
    echo "Get them from: https://cloud.livekit.io/projects"
    exit 1
fi

# Install dependencies
echo -e "${YELLOW}📦 Installing dependencies...${NC}"
pip install -r requirements.txt

# Set the API server URL to local
export API_SERVER_URL="http://localhost:8000"

# Run the agent
echo -e "${GREEN}✅ Starting agent...${NC}"
echo -e "${YELLOW}📡 Connecting to LiveKit Cloud...${NC}"
echo ""

python realtime_agent.py dev \
    --log-level debug \
    --production false