#!/bin/bash
# Deploy Agent to Docker Hub

set -e

# Load environment variables from .env file
if [ -f .env ]; then
    set -a
    source .env
    set +a
else
    echo "❌ ERROR: .env file not found in project root"
    echo "Please create .env file with required variables"
    exit 1
fi

# Check required environment variables
if [ -z "$DOCKER_USERNAME" ]; then
    echo "❌ ERROR: DOCKER_USERNAME not set in .env file"
    echo "Add DOCKER_USERNAME=your-docker-hub-username to .env"
    exit 1
fi

# Configuration
IMAGE_NAME="polyglot-agent"
TAG=${1:-"latest"}

echo "🐳 Building LiveKit Agent Docker image..."

# Build the image
cd polyglot-flight-agent
docker build -t ${IMAGE_NAME}:${TAG} .

echo "🏷️  Tagging image..."
docker tag ${IMAGE_NAME}:${TAG} ${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}
docker tag ${IMAGE_NAME}:${TAG} ${DOCKER_USERNAME}/${IMAGE_NAME}:latest

echo "📤 Pushing to Docker Hub..."
docker push ${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}
docker push ${DOCKER_USERNAME}/${IMAGE_NAME}:latest

echo "✅ Successfully pushed ${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}"
echo ""
echo "📝 To deploy to ECS, run: cd terraform && terraform apply"