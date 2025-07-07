#!/bin/bash

# Docker run script with fixed networking for LiveKit agent

# Load environment variables
source ../.env
docker stop polyglot-flight-agent
docker rm polyglot-flight-agent

# Build the Docker image
echo "Building Docker image..."
docker build -t polyglot-flight-agent .

# Run with host networking and expose debug ports
echo "Running agent with host networking and debug ports..."
docker run \
  --name polyglot-flight-agent \
  -d \
  --network=host \
  -p 8081:8081 \
  -p 55099:55099 \
  -e API_SERVER_URL="${API_SERVER_URL:-http://localhost:8000}" \
  -e LIVEKIT_API_KEY="${LIVEKIT_API_KEY}" \
  -e LIVEKIT_API_SECRET="${LIVEKIT_API_SECRET}" \
  -e LIVEKIT_URL="${LIVEKIT_URL:-wss://polyglot-rag-assistant-3l6xagej.livekit.cloud}" \
  -e OPENAI_API_KEY="${OPENAI_API_KEY}" \
  -e DEEPGRAM_API_KEY="${DEEPGRAM_API_KEY}" \
  -e CARTESIA_API_KEY="${CARTESIA_API_KEY}" \
  -e AMADEUS_CLIENT_ID="${AMADEUS_CLIENT_ID}" \
  -e AMADEUS_CLIENT_SECRET="${AMADEUS_CLIENT_SECRET}" \
  polyglot-flight-agent

# Alternative: Run with custom DNS if host networking doesn't work
# docker run \
#   --name polyglot-flight-agent \
#   --rm \
#   --dns=8.8.8.8 \
#   --dns=8.8.4.4 \
#   -p 8081:8081 \
#   -e API_SERVER_URL="${API_SERVER_URL:-http://host.docker.internal:8000}" \
#   -e LIVEKIT_API_KEY="${LIVEKIT_API_KEY}" \
#   -e LIVEKIT_API_SECRET="${LIVEKIT_API_SECRET}" \
#   -e LIVEKIT_URL="${LIVEKIT_URL:-wss://polyglot-rag-assistant-3l6xagej.livekit.cloud}" \
#   -e OPENAI_API_KEY="${OPENAI_API_KEY}" \
#   -e DEEPGRAM_API_KEY="${DEEPGRAM_API_KEY}" \
#   -e ELEVENLABS_API_KEY="${ELEVENLABS_API_KEY}" \
#   -e AMADEUS_CLIENT_ID="${AMADEUS_CLIENT_ID}" \
#   -e AMADEUS_CLIENT_SECRET="${AMADEUS_CLIENT_SECRET}" \
#   polyglot-flight-agent