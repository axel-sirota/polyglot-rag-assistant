#!/bin/bash
# Simple deploy script for LiveKit Agent

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}🚀 Deploying to LiveKit Cloud${NC}"

# Change to agent directory
cd "$(dirname "$0")"

# Load environment variables
if [ -f "../.env" ]; then
    export $(cat ../.env | grep -v '^#' | xargs)
fi

# Install dependencies locally first
echo -e "${YELLOW}📦 Installing dependencies...${NC}"
pip install -r requirements.txt

# Deploy using current directory
echo -e "${YELLOW}☁️  Deploying agent...${NC}"
lk agent deploy \
    --project "${LIVEKIT_PROJECT:-default}" \
    --secrets-file "../.env" \
    .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Success!${NC}"
else
    echo -e "${RED}❌ Failed!${NC}"
fi