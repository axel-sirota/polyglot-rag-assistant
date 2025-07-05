#!/bin/bash
# Test Docker build and run locally without pushing

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🐳 Building Docker image locally..."
docker build -f Dockerfile.api -t polyglot-api:test .

echo ""
echo "✅ Build successful!"
echo ""
echo "🏃 Running container locally for testing..."
echo "   Stop with Ctrl+C"
echo ""

# Run with environment variables from .env
docker run --rm -it \
  -p 8000:8000 \
  --env-file .env \
  polyglot-api:test

echo ""
echo "🧹 Cleaning up test image..."
docker rmi polyglot-api:test

echo "✅ Local test complete!"