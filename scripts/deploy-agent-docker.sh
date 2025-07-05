#!/bin/bash
# Build and push LiveKit agent Docker image

set -e

# Default tag
TAG=${1:-latest}

# Load environment variables
if [ -f .env ]; then
  source .env
fi

echo "🔨 Building LiveKit agent Docker image..."

# Build the image
cd polyglot-flight-agent
docker build -t polyglot-agent:$TAG .

# Test locally first as requested
echo "🧪 Testing Docker container locally..."
docker run --rm -d \
  --name polyglot-agent-test \
  -p 8081:8081 \
  -e LIVEKIT_URL=$LIVEKIT_URL \
  -e LIVEKIT_API_KEY=$LIVEKIT_API_KEY \
  -e LIVEKIT_API_SECRET=$LIVEKIT_API_SECRET \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e API_SERVER_URL="http://polyglot-rag-prod-alb-1838390148.us-east-1.elb.amazonaws.com" \
  polyglot-agent:$TAG

echo "⏳ Waiting for container to start..."
sleep 10

# Check health
echo "🏥 Checking health endpoint..."
if curl -f http://localhost:8081/; then
  echo "✅ Health check passed!"
else
  echo "❌ Health check failed!"
  docker logs polyglot-agent-test
  docker stop polyglot-agent-test
  exit 1
fi

# Check logs
echo "📋 Container logs:"
docker logs polyglot-agent-test

# Stop test container
docker stop polyglot-agent-test

# Ask for confirmation before pushing
read -p "🚀 Push to Docker Hub? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  # Tag for Docker Hub
  docker tag polyglot-agent:$TAG ${DOCKER_USERNAME}/polyglot-agent:$TAG
  docker tag polyglot-agent:$TAG ${DOCKER_USERNAME}/polyglot-agent:latest
  
  # Push to Docker Hub
  echo "📤 Pushing to Docker Hub..."
  docker push ${DOCKER_USERNAME}/polyglot-agent:$TAG
  docker push ${DOCKER_USERNAME}/polyglot-agent:latest
  
  echo "✅ Agent Docker image pushed successfully!"
  echo "🎯 Image: ${DOCKER_USERNAME}/polyglot-agent:$TAG"
else
  echo "⏸️  Push cancelled. Image is built locally as polyglot-agent:$TAG"
fi