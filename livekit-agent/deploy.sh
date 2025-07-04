#!/bin/bash
# Deploy LiveKit Agent to LiveKit Cloud

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 Deploying Polyglot Flight Assistant to LiveKit Cloud${NC}"

# Check for LiveKit CLI
if ! command -v lk &> /dev/null; then
    echo -e "${RED}❌ LiveKit CLI not found!${NC}"
    echo "Install it with: curl -sSL https://get.livekit.io/cli | bash"
    exit 1
fi

# Check for required environment variables
if [ -z "$LIVEKIT_API_KEY" ] || [ -z "$LIVEKIT_API_SECRET" ]; then
    echo -e "${RED}❌ Missing LiveKit credentials!${NC}"
    echo "Please set LIVEKIT_API_KEY and LIVEKIT_API_SECRET in your .env file"
    exit 1
fi

# Install dependencies
echo -e "${YELLOW}📦 Installing dependencies...${NC}"
pip install -r requirements.txt

# Deploy to LiveKit Cloud
echo -e "${YELLOW}☁️  Deploying to LiveKit Cloud...${NC}"
lk cloud agent deploy \
    --name "polyglot-flight-assistant" \
    --entry-point "agent.py" \
    --requirements "requirements.txt" \
    --env-file "../.env" \
    --instance-type "small" \
    --min-idle 1 \
    --max-idle 3 \
    --region "us-east-1"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Deployment successful!${NC}"
    echo -e "${GREEN}🎉 Your agent is now running on LiveKit Cloud${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Open web-app/livekit-client.html in your browser"
    echo "2. Click 'Connect' to start talking to your assistant"
    echo "3. Speak in any language to search for flights!"
else
    echo -e "${RED}❌ Deployment failed!${NC}"
    exit 1
fi