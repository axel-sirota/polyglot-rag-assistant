#!/bin/bash

# Load dev environment variables
if [ -f ../.env.dev ]; then
    echo "📋 Loading dev environment from .env.dev"
    export $(cat ../.env.dev | grep -v '^#' | xargs)
    echo "🔗 Using LiveKit Dev URL: $LIVEKIT_URL"
else
    echo "❌ .env.dev not found! Please create it first."
    exit 1
fi

echo ""
echo "🚀 Starting local HTTP server for test UI..."
echo "📍 Open http://localhost:8080/test-flight-ui.html in your browser"
echo "🌐 LiveKit Project: polyglot-rag-dev"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start Python HTTP server
python3 -m http.server 8080