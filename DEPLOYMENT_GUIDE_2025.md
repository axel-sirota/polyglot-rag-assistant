# Complete Deployment Guide for Polyglot Flight Assistant (2025)

## Overview

This guide addresses all the deployment issues and implements the correct patterns for LiveKit Agents in 2025.

## Architecture

```
User → WebRTC → LiveKit Cloud → Agent → API Server → Amadeus API
```

## Step 1: Deploy API Server (with Amadeus) to AWS ECS

### Build and push Docker image:

```bash
# Build the API server image
docker build -f Dockerfile.api -t polyglot-api .

# Tag for ECR
docker tag polyglot-api:latest YOUR_ECR_URL/polyglot-api:latest

# Push to ECR
docker push YOUR_ECR_URL/polyglot-api:latest
```

### Deploy to ECS:

```bash
# Create task definition
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json

# Create service
aws ecs create-service \
  --cluster your-cluster \
  --service-name polyglot-api \
  --task-definition polyglot-api:1 \
  --desired-count 2 \
  --launch-type FARGATE
```

### Set environment variables in ECS:

```json
{
  "environment": [
    {"name": "OPENAI_API_KEY", "value": "your-key"},
    {"name": "AMADEUS_CLIENT_ID", "value": "your-id"},
    {"name": "AMADEUS_CLIENT_SECRET", "value": "your-secret"},
    {"name": "LIVEKIT_API_KEY", "value": "your-key"},
    {"name": "LIVEKIT_API_SECRET", "value": "your-secret"}
  ]
}
```

## Step 2: Deploy LiveKit Agent (NEW Method)

### Fix the CLI issue first:

```bash
# Clear old config
rm -rf ~/.livekit/

# Re-authenticate
lk cloud auth

# Add your project properly
lk project add \
  --api-key ***REMOVED*** \
  --api-secret ***REMOVED*** \
  --url wss://polyglot-rag-assistant-3l6xagej.livekit.cloud \
  polyglot-rag-assistant-cloud

# Set as default
lk project set-default polyglot-rag-assistant-cloud
```

### Create agent using template (NEW approach):

```bash
# Use the template approach instead of direct creation
lk app create --template voice-pipeline-agent-python polyglot-flight-agent

# Copy our files into the template
cd polyglot-flight-agent
cp ../livekit-agent/agent.py .
cp ../livekit-agent/requirements.txt .
```

### Update environment variables:

Create `.env.production`:
```bash
LIVEKIT_URL=wss://polyglot-rag-assistant-3l6xagej.livekit.cloud
LIVEKIT_API_KEY=***REMOVED***
LIVEKIT_API_SECRET=***REMOVED***
OPENAI_API_KEY=your-openai-key
API_SERVER_URL=https://your-ecs-alb-url.amazonaws.com
```

### Deploy the agent:

```bash
# Development test
python agent.py dev

# Production deployment
python agent.py start
```

## Step 3: Alternative - Dashboard Deployment

If CLI continues to fail:

1. Go to https://cloud.livekit.io
2. Select your project: `polyglot-rag-assistant-cloud`
3. Navigate to **Agents** → **Deploy New Agent**
4. Upload these files:
   - `agent.py` (our corrected version)
   - `requirements.txt`
   - `.env.production`
5. Set entry point: `agent.py`
6. Deploy

## Step 4: Test the Complete System

### Test API Server:
```bash
curl https://your-api-server.com/health

curl "https://your-api-server.com/api/flights?origin=JFK&destination=LAX&departure_date=2025-07-10"
```

### Test LiveKit Token:
```bash
curl -X POST https://your-api-server.com/api/livekit/token \
  -H "Content-Type: application/json" \
  -d '{"identity": "test-user", "room": "test-room"}'
```

### Test Agent:
1. Open `web-app/livekit-client.html`
2. Update the API_URL to your deployed server
3. Click Connect
4. Speak in any language!

## Key Changes from Original Implementation

1. **Agent Pattern**: Used new `AgentSession` pattern instead of deprecated classes
2. **OpenAI Realtime**: Fixed syntax to use `openai.realtime.RealtimeModel`
3. **Function Tools**: Used `@function_tool` decorator for flight search
4. **Token Generation**: Used LiveKit SDK instead of manual JWT
5. **Deployment**: Template-based approach instead of deprecated CLI commands

## Troubleshooting

### "project does not match agent subdomain []"
- Clear LiveKit config and re-authenticate
- Use template-based creation
- Or use dashboard deployment

### Agent not connecting
- Check LIVEKIT_URL matches your project
- Verify API credentials
- Check agent logs: `lk logs --project your-project --follow`

### Flight search not working
- Verify API_SERVER_URL is set correctly
- Check API server is accessible from internet
- Test Amadeus credentials separately

## Production Checklist

- [ ] API Server deployed to ECS with public ALB
- [ ] Environment variables set in ECS task definition  
- [ ] LiveKit agent deployed (via template or dashboard)
- [ ] Agent environment variables include API_SERVER_URL
- [ ] Web client updated with production URLs
- [ ] SSL certificates configured on ALB
- [ ] Health checks passing
- [ ] Monitoring configured (CloudWatch, etc.)

## Architecture Benefits

1. **Separation of Concerns**: Agent handles voice, API handles flights
2. **Scalability**: Each component scales independently
3. **Security**: Amadeus credentials only in API server
4. **Flexibility**: Can update flight logic without touching agent
5. **Reliability**: ECS provides auto-restart and health checks

This deployment approach solves all the issues identified in the research and provides a production-ready system!