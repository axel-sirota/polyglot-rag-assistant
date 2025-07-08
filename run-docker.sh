#!/bin/bash
# Run Polyglot RAG Assistant with Docker

set -e

# Check for environment argument
ENV_TYPE=${1:-dev}

if [ "$ENV_TYPE" = "prod" ]; then
    ENV_FILE=".env"
    echo "🐳 Starting Polyglot RAG Assistant with Docker (PRODUCTION)"
    echo "🔴 WARNING: Using PRODUCTION LiveKit environment!"
else
    ENV_FILE=".env.dev"
    echo "🐳 Starting Polyglot RAG Assistant with Docker (DEVELOPMENT)"
    echo "🟢 Using DEV LiveKit environment (safe for testing)"
fi

echo "=============================================="

# Check if env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ $ENV_FILE file not found!"
    echo "Please create $ENV_FILE with required API keys"
    exit 1
fi

# Export environment variables
export $(cat "$ENV_FILE" | grep -v '^#' | xargs)
echo "🔗 Using LiveKit URL: $LIVEKIT_URL"

# Build images
echo "🔨 Building Docker images..."
docker-compose build

# Start services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check services
echo ""
echo "🔍 Checking services..."
echo "========================"

# Check API
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ API Server: http://localhost:8000"
else
    echo "❌ API Server failed to start"
fi

# Check Agent
if curl -s http://localhost:8082/debug > /dev/null; then
    echo "✅ LiveKit Agent: http://localhost:8082/debug"
else
    echo "❌ LiveKit Agent might still be starting..."
fi

echo ""
echo "🌐 Web UI Access:"
echo "================="
echo "Production: https://polyglot-rag-ui.vercel.app"
echo ""
echo "📊 Monitoring:"
echo "============="
echo "All logs: docker-compose logs -f"
echo "API logs: docker-compose logs -f api"
echo "Agent logs: docker-compose logs -f agent"
echo ""
echo "🛑 To stop all services:"
echo "======================="
echo "docker-compose -f $COMPOSE_FILE down"
echo ""
echo "✨ Docker setup complete!"