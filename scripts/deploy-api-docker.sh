#!/bin/bash
# Deploy API to Docker Hub

set -e

# Configuration
DOCKER_USERNAME=${DOCKER_USERNAME:-"your-dockerhub-username"}
IMAGE_NAME="polyglot-api"
TAG=${1:-"latest"}

echo "🐳 Building Docker image..."
docker build -f Dockerfile.api -t ${IMAGE_NAME}:${TAG} .

echo "🏷️  Tagging image..."
docker tag ${IMAGE_NAME}:${TAG} ${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}
docker tag ${IMAGE_NAME}:${TAG} ${DOCKER_USERNAME}/${IMAGE_NAME}:latest

echo "🔐 Logging in to Docker Hub..."
echo "${DOCKER_PASSWORD}" | docker login -u "${DOCKER_USERNAME}" --password-stdin

echo "📤 Pushing to Docker Hub..."
docker push ${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}
docker push ${DOCKER_USERNAME}/${IMAGE_NAME}:latest

echo "✅ Successfully pushed ${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}"