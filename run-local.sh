#!/bin/bash
# Run the entire Polyglot RAG Assistant locally

set -e

echo "🚀 Starting Polyglot RAG Assistant Local Setup"
echo "============================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Please create a .env file with required API keys"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Function to check if a process is running
check_process() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "✅ Port $1 is already in use (service running)"
        return 0
    else
        return 1
    fi
}

# Kill existing processes if requested
if [ "$1" == "--restart" ]; then
    echo "🔄 Stopping existing services..."
    pkill -f "python.*api_server.py" || true
    pkill -f "python.*agent.py" || true
    sleep 2
fi

# Start API Server
if ! check_process 8000; then
    echo "🌐 Starting API Server on port 8000..."
    cd /Users/axelsirota/repos/polyglot-rag-assistant
    nohup .venv/bin/python3 api_server.py > api_server.log 2>&1 &
    echo "   Waiting for API to start..."
    sleep 5
else
    echo "ℹ️  API Server already running on port 8000"
fi

# Start LiveKit Agent
if ! check_process 8082; then
    echo "🤖 Starting LiveKit Agent on port 8082..."
    cd /Users/axelsirota/repos/polyglot-rag-assistant/polyglot-flight-agent
    nohup ../.venv/bin/python3 agent.py > ../agent.log 2>&1 &
    echo "   Waiting for agent to register..."
    sleep 5
else
    echo "ℹ️  LiveKit Agent already running on port 8082"
fi

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
    echo "❌ LiveKit Agent failed to start"
fi

# Display UI information
echo ""
echo "🌐 Web UI Access:"
echo "================="
echo "Local Test: http://localhost:3000/livekit-client-local.html"
echo "Production: https://polyglot-rag-ui.vercel.app"
echo ""
echo "📊 Monitoring:"
echo "============="
echo "API Logs: tail -f api_server.log"
echo "Agent Logs: tail -f agent.log"
echo ""
echo "🛑 To stop all services:"
echo "======================="
echo "./run-local.sh --restart"
echo ""
echo "✨ Setup complete! Open the web UI to start testing."