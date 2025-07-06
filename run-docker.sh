#!/bin/bash
# Run Polyglot RAG Assistant with Docker

set -e

echo "🐳 Starting Polyglot RAG Assistant with Docker"
echo "=============================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Please create a .env file with required API keys"
    exit 1
fi

# Export environment variables
export $(cat .env | grep -v '^#' | xargs)

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
echo "docker-compose down"
echo ""
echo "✨ Docker setup complete!"