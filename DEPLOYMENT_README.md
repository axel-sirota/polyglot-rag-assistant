# Polyglot RAG Assistant - Deployment Guide

## Architecture Overview

The system consists of three main components:
1. **Web UI** - Deployed on Vercel
2. **API Server** - Running on ECS (or locally)
3. **LiveKit Agent** - Running locally → Docker → ECS

## Current Status

- ✅ **Web UI**: Deployed at https://polyglot-rag-ui.vercel.app
- ✅ **API Server**: Running on ECS at http://polyglot-rag-prod-alb-1838390148.us-east-1.elb.amazonaws.com
- ✅ **LiveKit Agent**: Working locally with audio output fixed!

## Local Development

### 1. Run Everything Locally

```bash
# Start all services locally
./run-local.sh

# Access:
# - API: http://localhost:8000
# - Agent Debug: http://localhost:8082/debug
# - Web UI: https://polyglot-rag-ui.vercel.app
```

### 2. Run with Docker

```bash
# Start all services in Docker
./run-docker.sh

# Monitor logs
docker-compose logs -f
```

## Deployment Steps

### 1. Deploy Web UI to Vercel

```bash
./scripts/deploy-ui-vercel.sh
```

The UI will be available at: https://polyglot-rag-ui.vercel.app

### 2. Deploy API to ECS (if needed)

The API is already deployed to ECS. To redeploy:

```bash
./scripts/deploy-api-docker.sh
```

### 3. Deploy Agent

#### Local Development
```bash
cd polyglot-flight-agent
../.venv/bin/python3 agent.py
```

#### Docker Local
```bash
docker-compose up agent
```

#### Deploy to ECS
```bash
./deploy-agent-ecs.sh
```

## Environment Variables

Create a `.env` file with:

```env
# LiveKit (Required)
LIVEKIT_URL=wss://polyglot-rag-assistant-3l6xagej.livekit.cloud
LIVEKIT_API_KEY=your_key
LIVEKIT_API_SECRET=your_secret

# AI Services
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
DEEPGRAM_API_KEY=your_key
CARTESIA_API_KEY=your_key

# Flight APIs
AMADEUS_CLIENT_ID=your_id
AMADEUS_CLIENT_SECRET=your_secret
AVIATIONSTACK_API_KEY=your_key
SERPAPI_API_KEY=your_key

# Deployment
VERCEL_TOKEN=your_token
API_SERVER_URL=http://polyglot-rag-prod-alb-1838390148.us-east-1.elb.amazonaws.com
```

## Testing the System

1. **Open the Web UI**: https://polyglot-rag-ui.vercel.app
2. **Click "Connect"**
3. **Wait for the agent to join** (you'll see "🤖 AI Assistant joined")
4. **Start speaking in any language!**

## Audio Fix Details

The agent now includes:
- Audio resampling from 24kHz (TTS) to 48kHz (WebRTC)
- Custom `ResamplingAudioOutput` class
- Proper async handling
- Test tone on connection (440Hz beep)

## Troubleshooting

### No Audio
- Check agent logs: `tail -f agent.log`
- Verify test tone plays on connection
- Check browser console for errors

### Agent Not Joining
- Verify agent is running: `curl http://localhost:8082/debug`
- Check LiveKit credentials in `.env`
- Ensure metadata triggers agent: `agent_request: true`

### API Issues
- Check API health: `curl http://localhost:8000/health`
- Verify API keys in `.env`
- Check logs: `tail -f api_server.log`

## Monitoring

### Local
```bash
# API logs
tail -f api_server.log

# Agent logs
tail -f agent.log

# All Docker logs
docker-compose logs -f
```

### ECS
```bash
# API logs
aws logs tail /ecs/polyglot-api --follow

# Agent logs
aws logs tail /ecs/polyglot-agent --follow
```

## Next Steps

1. ✅ Local development working
2. ✅ Docker setup ready
3. 🔄 Deploy agent to ECS
4. 🔄 Add auto-scaling
5. 🔄 Set up monitoring/alerting