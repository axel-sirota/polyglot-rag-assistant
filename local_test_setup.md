# Local Testing & Deployment Guide

## 🧪 Phase 1: Local Testing

### 1. Test with LiveKit CLI (Simplest)

```bash
# Install LiveKit CLI if not already installed
brew install livekit-cli

# Start local LiveKit server
livekit-server --dev

# In another terminal, run your agent
.venv/bin/python3 livekit_voice_assistant.py dev

# Test with CLI
livekit-cli test-agent \
  --url ws://localhost:7880 \
  --api-key devkey \
  --api-secret secret
```

### 2. Test with Local Web App

```bash
# Start all services
./start_livekit_demo.sh

# Open web test
open simple_web_test.html

# Or use LiveKit's test app
open https://meet.livekit.io
# Connect to: ws://localhost:7880
# API Key: devkey
# API Secret: secret
```

### 3. Test with Docker (Production-like)

```bash
# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY . .

# Run agent
CMD ["python", "livekit_voice_assistant.py"]
EOF

# Build and run
docker build -t polyglot-agent .
docker run -e OPENAI_API_KEY=$OPENAI_API_KEY polyglot-agent
```

## 🚀 Phase 2: Deploy to LiveKit Cloud

### 1. Prepare for LiveKit Cloud

```bash
# Install LiveKit Cloud CLI
pip install livekit-cloud-cli

# Login to LiveKit Cloud
lk cloud login

# Create project if needed
lk cloud project create polyglot-voice-assistant
```

### 2. Create agent.yaml

```yaml
# agent.yaml
name: polyglot-voice-assistant
entry_point: livekit_voice_assistant.py
runtime: python3.11
environment:
  OPENAI_API_KEY: ${OPENAI_API_KEY}
  ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
  SERPAPI_API_KEY: ${SERPAPI_API_KEY}
  FLIGHT_API_URL: ${FLIGHT_API_URL}
requirements:
  - livekit
  - livekit-agents
  - livekit-plugins-openai
  - livekit-plugins-silero
  - python-dotenv
  - httpx
scaling:
  min_instances: 1
  max_instances: 10
  target_concurrency: 5
```

### 3. Deploy to LiveKit Cloud

```bash
# Deploy agent
lk cloud agent deploy \
  --project polyglot-voice-assistant \
  --file agent.yaml

# Check deployment status
lk cloud agent list

# View logs
lk cloud logs -f

# Test deployed agent
lk cloud agent test --project polyglot-voice-assistant
```

## 🔧 Phase 3: Deploy to AWS ECS

### 1. Create ECS Task Definition

```json
{
  "family": "polyglot-voice-agent",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "voice-agent",
      "image": "YOUR_ECR_REPO/polyglot-agent:latest",
      "essential": true,
      "environment": [
        {"name": "LIVEKIT_URL", "value": "wss://your-instance.livekit.cloud"},
        {"name": "LIVEKIT_API_KEY", "value": "YOUR_API_KEY"},
        {"name": "LIVEKIT_API_SECRET", "value": "YOUR_API_SECRET"}
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:openai-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/polyglot-agent",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "agent"
        }
      }
    },
    {
      "name": "flight-api",
      "image": "YOUR_ECR_REPO/flight-api:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8765,
          "protocol": "tcp"
        }
      ]
    }
  ]
}
```

### 2. Deploy Script

```bash
#!/bin/bash
# deploy_to_ecs.sh

# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ECR_REPO

# Build images
docker build -t polyglot-agent -f Dockerfile.agent .
docker build -t flight-api -f Dockerfile.api .

# Tag and push
docker tag polyglot-agent:latest YOUR_ECR_REPO/polyglot-agent:latest
docker tag flight-api:latest YOUR_ECR_REPO/flight-api:latest

docker push YOUR_ECR_REPO/polyglot-agent:latest
docker push YOUR_ECR_REPO/flight-api:latest

# Update ECS service
aws ecs update-service \
  --cluster your-cluster \
  --service polyglot-agent \
  --force-new-deployment

# Check deployment
aws ecs describe-services \
  --cluster your-cluster \
  --services polyglot-agent
```

### 3. Auto-scaling Configuration

```bash
# Register scalable target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/your-cluster/polyglot-agent \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 1 \
  --max-capacity 10

# Create scaling policy
aws application-autoscaling put-scaling-policy \
  --policy-name polyglot-agent-scaling \
  --service-namespace ecs \
  --resource-id service/your-cluster/polyglot-agent \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    }
  }'
```

## 🎯 Testing Flow

### Local Testing Checklist:
- [ ] Voice recording works
- [ ] Speech-to-text accurate
- [ ] Flight search returns results
- [ ] Text-to-speech plays audio
- [ ] Multiple languages work
- [ ] Error handling works

### LiveKit Cloud Testing:
- [ ] Agent connects to cloud
- [ ] Can handle multiple sessions
- [ ] Logs are accessible
- [ ] Metrics look good
- [ ] Auto-scaling works

### Production Testing:
- [ ] Load testing with multiple users
- [ ] Failover testing
- [ ] Monitoring alerts work
- [ ] Cost optimization verified

## 🔍 Monitoring

```bash
# LiveKit Cloud monitoring
lk cloud metrics --project polyglot-voice-assistant

# AWS CloudWatch dashboard
aws cloudwatch put-dashboard \
  --dashboard-name PolyglotAgent \
  --dashboard-body file://dashboard.json

# Custom metrics
aws cloudwatch put-metric-data \
  --namespace PolyglotAgent \
  --metric-name FlightSearchLatency \
  --value $LATENCY \
  --unit Milliseconds
```

## 🚨 Troubleshooting

### Common Issues:

1. **WebSocket connection fails**
   ```bash
   # Check LiveKit server is running
   livekit-cli room list --url $LIVEKIT_URL
   ```

2. **Agent doesn't respond**
   ```bash
   # Check logs
   lk cloud logs --tail 100
   ```

3. **High latency**
   ```bash
   # Check region proximity
   # Use LiveKit edge servers
   ```

## 💰 Cost Optimization

### LiveKit Cloud:
- Use auto-scaling
- Set max instance limits
- Monitor usage patterns

### AWS ECS:
- Use Fargate Spot for non-critical
- Right-size containers
- Use CloudWatch to identify waste