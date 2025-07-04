#!/bin/bash
# Simple start script for Polyglot Flight Assistant

echo "🚀 Starting Polyglot Flight Assistant..."
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please create it: python3 -m venv .venv"
    exit 1
fi

# Check if dependencies are installed
if ! .venv/bin/python3 -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    .venv/bin/python3 -m pip install -r requirements.txt
fi

# Start the backend
echo "✅ Starting backend API on http://localhost:8000"
echo "📖 API docs available at http://localhost:8000/docs"
echo ""
echo "To start the web interface:"
echo "  cd web-app && python3 -m http.server 3000"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run the server
