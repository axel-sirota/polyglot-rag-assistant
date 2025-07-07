#!/bin/bash

# Script to build and run the Polyglot Flight Agent in Docker
# This handles all the environment variables and container management

set -e  # Exit on error

echo "🛑 Stopping existing container if running..."
docker stop polyglot-agent 2>/dev/null || true
docker rm polyglot-agent 2>/dev/null || true

echo "🔨 Building Docker image..."
docker build -t polyglot-agent .

echo "🚀 Starting container with environment variables..."
docker run -d \
  -e LIVEKIT_URL=$LIVEKIT_URL \
  -e LIVEKIT_API_KEY=$LIVEKIT_API_KEY \
  -e LIVEKIT_API_SECRET=$LIVEKIT_API_SECRET \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e DEEPGRAM_API_KEY=$DEEPGRAM_API_KEY \
  -e CARTESIA_API_KEY=$CARTESIA_API_KEY \
  -e API_URL="http://polyglot-rag-prod-alb-1838390148.us-east-1.elb.amazonaws.com" \
  --name polyglot-agent \
  polyglot-agent

echo "✅ Container started! Showing logs..."
echo "Press Ctrl+C to stop viewing logs (container will keep running)"
echo ""

# Show logs
docker logs -f polyglot-agent