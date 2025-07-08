#!/bin/bash

echo "🚀 Starting local HTTP server for test UI..."
echo "📍 Open http://localhost:8080/test-flight-ui.html in your browser"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start Python HTTP server
python3 -m http.server 8080