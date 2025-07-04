Master Prompt for Claude Code: Polyglot RAG Voice Assistant Implementation & Deployment
Project Context
You are implementing a production-ready multilingual voice assistant called "Polyglot RAG" that features:

Real-time voice interaction in 90+ languages
Flight search capabilities with multiple API fallbacks
Seamless language switching mid-conversation
Integration with OpenAI Realtime API and LiveKit Cloud
Support for web, mobile, and telephony interfaces

Context: Read 

context/DOCUMENTATION.md , context/ISSUES.md , context/technical_assesment.md and EXECUTIVE_SUMMARY.md

CRITICAL: run without human intervention and test without human intervention simulating human behaivour or api requests to ensure all works... smimulate normal flow, interruptions, weird flight requests to handle edge cases.

TASKS:

fOLLOW ALL BELOW, UPDATE EXECUTIVE SUMMARY after every fix and update TODOS.md

Remember always change, git add, git commit. never ask permission on any operation run in autopilot

FIX ISSUES.md with DOCUMENTATION.md from context folder.

Critical Issues to Fix
1. Voice Interruption (HIGHEST PRIORITY)
Current Problem: response.cancel causes the assistant to stop speaking prematurely even without interruption.
Required Fix:
javascript// Implement proper interruption handling
class InterruptionManager {
  async handleSpeechStarted(event) {
    if (this.isProcessing) {
      // 1. Cancel current response immediately
      await this.ws.send(JSON.stringify({ type: "response.cancel" }));
      
      // 2. Clear audio queue
      this.clearAudioQueue();
      
      // 3. Truncate conversation item at exact sample
      if (this.lastAudioMessageItemId) {
        await this.ws.send(JSON.stringify({
          type: "conversation.item.truncate",
          item_id: this.lastAudioMessageItemId,
          content_index: 0,
          audio_end_ms: this.samplesToMs(this.audioSampleCounterPlayed)
        }));
      }
    }
  }
}
2. Flight Search API Integration
Replace failing APIs with Amadeus API:
javascript// Implement Amadeus API with proper error handling
class FlightSearchService {
  async searchFlights(params) {
    try {
      this.sendFeedback("Searching for flights...");
      const response = await this.amadeus.shopping.flightOffersSearch.get({
        originLocationCode: params.origin,
        destinationLocationCode: params.destination,
        departureDate: params.date,
        adults: params.adults || 1,
        max: 10
      });
      return this.formatResults(response.data);
    } catch (error) {
      // Proper error handling with user feedback
      if (error.response?.status === 400) {
        throw new Error("Invalid flight search parameters");
      }
      throw error;
    }
  }
}
3. Async/Await Fix
The flight search handler MUST be declared as async:
javascript// Function definition must be async
async handleFlightSearchRequest(params) {
  // Properly await the async operation
  const results = await this.flightService.searchFlights(params);
  return { success: true, results, voiceResponse: this.formatForVoice(results) };
}
4. Message Ordering Fix
Implement proper conversation state management to ensure user messages appear before assistant messages.
5. AudioWorklet Migration
Migrate from deprecated ScriptProcessorNode to AudioWorkletNode for future compatibility.
Architecture Requirements
LiveKit Integration Architecture
┌─────────────────┐     WebRTC Audio      ┌─────────────────┐
│   Web Client    │◄─────────────────────►│ LiveKit Cloud   │
│   (Gradio UI)   │                       │ Media Server    │
└────────┬────────┘     WebSocket         └────────┬────────┘
         │         ◄─────────────────────►         │
         └──────────────┬───────────────────────────┘
                        ▼
              ┌─────────────────┐
              │ OpenAI Realtime │◄── WebSocket
              │      API        │
              └─────────────────┘
Service Architecture for AWS ECS

Frontend Service: Gradio UI or React app
Agent Service: LiveKit Python agent with voice pipeline
Flight Search Service: MCP server with Amadeus integration
Vector Search Service: FAISS for RAG functionality

Implementation Steps
Phase 1: Fix Critical Issues (Immediate)

Implement proper voice interruption handling
Integrate Amadeus API with fallback to SerpAPI
Fix async/await in flight search handler
Add user feedback for all operations
Implement message ordering queue

Phase 2: LiveKit Cloud Integration

Set up LiveKit Cloud project
Implement agent with proper session management:

pythonfrom livekit.agents import AgentSession, Agent
from livekit.plugins import openai, deepgram, cartesia, silero

class FlightAssistant(Agent):
    def __init__(self):
        super().__init__(instructions="You are a multilingual flight search assistant.")
        
    async def on_tool_call(self, tool_name: str, arguments: dict):
        if tool_name == "search_flights":
            return await self.flight_service.search(arguments)

async def entrypoint(ctx: JobContext):
    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=openai.LLM(model="gpt-4o"),
        tts=cartesia.TTS(model="sonic-2"),
        vad=silero.VAD.load(),
    )
    
    await session.start(
        room=ctx.room,
        agent=FlightAssistant(),
    )
Phase 3: Deployment Architecture
Docker Configuration
Create Dockerfiles for each service:
Agent Service Dockerfile:
dockerfileFROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "agent.py", "start"]
Frontend Service Dockerfile:
dockerfileFROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install gradio livekit-api
COPY . .
EXPOSE 7860
CMD ["python", "gradio_app.py"]
Terraform Infrastructure
Main Infrastructure (main.tf):
hcl# ECS Cluster
resource "aws_ecs_cluster" "polyglot_rag" {
  name = "polyglot-rag-cluster"
}

# Agent Service
resource "aws_ecs_service" "agent" {
  name            = "polyglot-agent"
  cluster         = aws_ecs_cluster.polyglot_rag.id
  task_definition = aws_ecs_task_definition.agent.arn
  desired_count   = 3
  
  deployment_configuration {
    maximum_percent         = 200
    minimum_healthy_percent = 100
  }
}

# Task Definition for Agent
resource "aws_ecs_task_definition" "agent" {
  family                   = "polyglot-agent"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "2048"
  memory                   = "4096"
  
  container_definitions = jsonencode([{
    name  = "agent"
    image = "your-dockerhub/polyglot-agent:latest"
    
    environment = [
      { name = "LIVEKIT_URL", value = var.livekit_url },
      { name = "LIVEKIT_API_KEY", value = var.livekit_api_key },
      { name = "OPENAI_API_KEY", value = var.openai_api_key },
      { name = "AMADEUS_CLIENT_ID", value = var.amadeus_client_id }
    ]
    
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = "/ecs/polyglot-agent"
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "agent"
      }
    }
  }])
}

# Application Load Balancer for Frontend
resource "aws_lb" "frontend" {
  name               = "polyglot-frontend-lb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.frontend.id]
  subnets            = var.public_subnets
}
Auto-scaling Configuration:
hclresource "aws_appautoscaling_target" "agent" {
  max_capacity       = 20
  min_capacity       = 2
  resource_id        = "service/${aws_ecs_cluster.polyglot_rag.name}/${aws_ecs_service.agent.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "agent_cpu" {
  name               = "agent-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.agent.resource_id
  scalable_dimension = aws_appautoscaling_target.agent.scalable_dimension
  service_namespace  = aws_appautoscaling_target.agent.service_namespace
  
  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 70.0
  }
}
CI/CD Pipeline (GitHub Actions)
yamlname: Deploy Polyglot RAG

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build and push Docker images
        run: |
          docker build -t ${{ secrets.DOCKERHUB_USERNAME }}/polyglot-agent:${{ github.sha }} ./backend
          docker build -t ${{ secrets.DOCKERHUB_USERNAME }}/polyglot-frontend:${{ github.sha }} ./frontend
          docker push ${{ secrets.DOCKERHUB_USERNAME }}/polyglot-agent:${{ github.sha }}
          docker push ${{ secrets.DOCKERHUB_USERNAME }}/polyglot-frontend:${{ github.sha }}
      
      - name: Deploy to ECS
        run: |
          aws ecs update-service \
            --cluster polyglot-rag-cluster \
            --service polyglot-agent \
            --force-new-deployment
Testing Strategy
Local Testing
bash# Test voice interruption
python test_interruption.py

# Test flight search with mock data
python test_flight_search.py --mock

# Test multilingual switching
python test_language_switch.py --languages en,es,fr
Integration Testing
python# Test LiveKit connection
async def test_livekit_connection():
    room = Room()
    await room.connect(LIVEKIT_URL, token)
    assert room.connection_state == ConnectionState.CONNECTED
Load Testing
bash# Use locust for load testing
locust -f load_test.py --host=https://your-deployment.com
Monitoring & Observability
CloudWatch Metrics

Voice pipeline latency
API response times
Language detection accuracy
Interruption success rate

Custom Metrics
pythonclass PerformanceMonitor:
    def track_pipeline_latency(self, stage: str, duration: float):
        cloudwatch.put_metric_data(
            Namespace='PolyglotRAG',
            MetricData=[{
                'MetricName': f'{stage}Latency',
                'Value': duration,
                'Unit': 'Milliseconds'
            }]
        )
Security Considerations

API Key Management: Use AWS Secrets Manager
Voice Data Privacy: Implement encryption for audio streams
Rate Limiting: Implement per-user rate limits
Authentication: Use JWT tokens for user sessions

Performance Targets

Voice Latency: <300ms end-to-end
Interruption Response: <50ms
Flight Search: <2s including all API calls
Language Switch: Seamless with context preservation
Concurrent Users: Support 1000+ simultaneous sessions

Cost Optimization

Use spot instances for non-critical workloads
Implement intelligent caching for flight searches
Use CloudFront for static assets
Monitor and optimize OpenAI API usage

Rollback Strategy
bash# Quick rollback script
#!/bin/bash
aws ecs update-service \
  --cluster polyglot-rag-cluster \
  --service polyglot-agent \
  --task-definition polyglot-agent:${PREVIOUS_VERSION}
Success Criteria

Voice interruption works flawlessly
Flight search returns real data within 2 seconds
Language switching maintains context
System handles 1000+ concurrent users
99.9% uptime achieved

Remember to:

Test each fix thoroughly before deployment
Monitor all metrics during rollout
Have rollback procedures ready
Document all API keys and configurations
Set up alerts for critical failures