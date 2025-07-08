#!/bin/bash
# Development environment for Polyglot RAG Assistant
# Uses .env.dev and docker-compose.dev.yml

set -e

echo "🐳 Polyglot RAG Assistant - Development Environment"
echo "=================================================="
echo ""

# Check if .env.dev exists
if [ ! -f .env.dev ]; then
    echo "❌ .env.dev file not found!"
    echo "Please ensure .env.dev exists with dev LiveKit credentials"
    exit 1
fi

# Show which environment we're using
echo "🟢 Using DEVELOPMENT environment (.env.dev)"
LIVEKIT_URL=$(grep LIVEKIT_URL .env.dev | cut -d '=' -f2)
echo "🔗 LiveKit URL: $LIVEKIT_URL"
echo ""

# Command handling
COMMAND=${1:-up}

case $COMMAND in
    up|start)
        echo "🔨 Building and starting all services..."
        docker-compose -f docker-compose.dev.yml up --build -d
        
        # Wait for services
        echo ""
        echo "⏳ Waiting for services to start..."
        sleep 10
        
        # Check service health
        echo ""
        echo "🔍 Checking services..."
        echo "========================"
        
        # Check API
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo "✅ API Server: http://localhost:8000"
        else
            echo "⚠️  API Server: Starting up..."
        fi
        
        # Check Agent
        if docker ps | grep -q polyglot-agent-dev; then
            echo "✅ LiveKit Agent: Running"
        else
            echo "❌ LiveKit Agent: Not running"
        fi
        
        # Web UI is always available
        echo "✅ Web UI Server: http://localhost:8080"
        
        echo ""
        echo "🌐 Access Points:"
        echo "================"
        echo "📱 Test UI: http://localhost:8080/polyglot-flight-agent/test-flight-ui.html"
        echo "💬 Chat UI: http://localhost:8080/web-app/livekit-voice-chat.html"
        echo "📚 API Docs: http://localhost:8000/docs"
        echo ""
        echo "📊 View Logs:"
        echo "============"
        echo "All services: docker-compose -f docker-compose.dev.yml logs -f"
        echo "API only: docker-compose -f docker-compose.dev.yml logs -f api"
        echo "Agent only: docker-compose -f docker-compose.dev.yml logs -f agent"
        echo ""
        ;;
        
    down|stop)
        echo "🛑 Stopping all services..."
        docker-compose -f docker-compose.dev.yml down
        echo "✅ All services stopped"
        ;;
        
    logs)
        SERVICE=${2:-}
        if [ -z "$SERVICE" ]; then
            docker-compose -f docker-compose.dev.yml logs -f
        else
            docker-compose -f docker-compose.dev.yml logs -f $SERVICE
        fi
        ;;
        
    restart)
        echo "🔄 Restarting services..."
        docker-compose -f docker-compose.dev.yml restart
        ;;
        
    ps|status)
        docker-compose -f docker-compose.dev.yml ps
        ;;
        
    build)
        echo "🔨 Building images..."
        docker-compose -f docker-compose.dev.yml build
        ;;
        
    *)
        echo "Usage: $0 [up|down|logs|restart|ps|build]"
        echo ""
        echo "Commands:"
        echo "  up/start  - Start all services"
        echo "  down/stop - Stop all services"
        echo "  logs [service] - View logs (optionally for specific service)"
        echo "  restart   - Restart all services"
        echo "  ps/status - Show service status"
        echo "  build     - Build Docker images"
        exit 1
        ;;
esac