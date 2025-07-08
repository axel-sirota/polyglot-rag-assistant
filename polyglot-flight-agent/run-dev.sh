#!/bin/bash
# Run agent with dev environment

echo "🚀 Starting LiveKit Agent with DEV environment"
echo "=============================================="

# Load dev environment
if [ -f ../.env.dev ]; then
    echo "📋 Loading environment from .env.dev"
    export $(cat ../.env.dev | grep -v '^#' | xargs)
    echo "🔗 LiveKit URL: $LIVEKIT_URL"
    echo "🏷️  Project: polyglot-rag-dev"
    echo ""
else
    echo "❌ .env.dev not found!"
    echo "Please create .env.dev with dev LiveKit credentials"
    exit 1
fi

# Run the agent
echo "Starting agent..."
echo "================"
.venv/bin/python3 agent.py