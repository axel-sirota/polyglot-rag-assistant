#!/bin/bash
# Deploy to LiveKit Cloud

echo "☁️  Deploying to LiveKit Cloud"
echo "============================"

# Check if logged in
if ! lk cloud project list >/dev/null 2>&1; then
    echo "Please login first:"
    echo "lk cloud login"
    exit 1
fi

# Create deployment package
echo "1. Creating deployment package..."
cat > agent.yaml << EOF
name: polyglot-voice-assistant
entry_point: livekit_voice_assistant.py
runtime: python3.11
api_version: v1
environment:
  OPENAI_API_KEY: \${OPENAI_API_KEY}
  SERPAPI_API_KEY: \${SERPAPI_API_KEY}
  FLIGHT_API_URL: https://your-flight-api.com
requirements:
  - livekit
  - livekit-agents
  - livekit-plugins-openai
  - livekit-plugins-silero  
  - python-dotenv
  - httpx
  - asyncio
scaling:
  min_instances: 1
  max_instances: 5
  target_concurrency: 3
health_check:
  path: /health
  interval: 30s
  timeout: 10s
EOF

# Create requirements file for cloud
echo "2. Creating requirements.txt for cloud..."
cat > requirements-cloud.txt << EOF
livekit
livekit-agents
livekit-plugins-openai
livekit-plugins-silero
python-dotenv
httpx
asyncio
EOF

# Deploy
echo "3. Deploying agent..."
lk cloud agent deploy \
  --project polyglot-voice-assistant \
  --file agent.yaml \
  --yes

# Get deployment info
echo ""
echo "4. Deployment Info:"
lk cloud agent list --project polyglot-voice-assistant

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Test your deployed agent:"
echo "1. Get your project URL and credentials from LiveKit Cloud dashboard"
echo "2. Use the test page: https://agents-playground.livekit.io/"
echo "3. Or test with CLI:"
echo "   lk cloud agent test --project polyglot-voice-assistant"
echo ""
echo "View logs:"
echo "lk cloud logs -f --project polyglot-voice-assistant"