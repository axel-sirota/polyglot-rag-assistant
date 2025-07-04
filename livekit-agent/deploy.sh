#!/bin/bash
# Deploy LiveKit Agent to LiveKit Cloud

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 Deploying Polyglot Flight Assistant to LiveKit Cloud${NC}"

# Change to agent directory
cd "$(dirname "$0")"

# Load environment variables
if [ -f "../.env" ]; then
    export $(cat ../.env | grep -v '^#' | xargs)
else
    echo -e "${RED}❌ No .env file found!${NC}"
    exit 1
fi

# Check for project
if [ -z "$LIVEKIT_PROJECT" ]; then
    echo -e "${RED}❌ LIVEKIT_PROJECT not set in .env${NC}"
    echo "Add to your .env file: LIVEKIT_PROJECT=your-project-name"
    echo ""
    echo "To find your project name, run: lk project list"
    exit 1
fi


# Deploy to LiveKit Cloud
echo -e "${YELLOW}☁️  Deploying to LiveKit Cloud...${NC}"
echo "Project: $LIVEKIT_PROJECT"
echo ""

# Deploy from current directory with secrets
lk agent deploy \
    --project "$LIVEKIT_PROJECT" \
    --secrets-file "../.env" \
    .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Deployment successful!${NC}"
    echo -e "${GREEN}🎉 Your agent is now running on LiveKit Cloud${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Check status: lk agent list --project $LIVEKIT_PROJECT"
    echo "2. View logs: lk logs --project $LIVEKIT_PROJECT --follow"
    echo "3. Open web-app/livekit-client.html in your browser"
    echo "4. Click 'Connect' to start talking to your assistant"
else
    echo -e "${RED}❌ Deployment failed!${NC}"
    echo ""
    echo "Common fixes:"
    echo "1. Run: lk cloud auth"
    echo "2. Check project name: lk project list"
    echo "3. Add to .env: LIVEKIT_PROJECT=your-project-name"
    exit 1
fi