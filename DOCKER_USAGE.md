# Docker Usage Guide

## Development (Recommended for Testing)

Use the development environment for all local testing:

```bash
# Start everything (API, Agent, Web UI)
./docker-dev.sh up

# View logs
./docker-dev.sh logs

# Stop everything
./docker-dev.sh down
```

**Access Points:**
- Test UI: http://localhost:8080/polyglot-flight-agent/test-flight-ui.html
- Chat UI: http://localhost:8080/web-app/livekit-voice-chat.html
- API: http://localhost:8000

This uses:
- `.env.dev` file
- Dev LiveKit project (polyglot-rag-dev)
- All services in Docker containers
- Isolated from production

## Production Deployment

For production, use the deployment scripts in `scripts/`:

```bash
# Deploy API to Docker Hub
./scripts/deploy-api-docker.sh

# Deploy Agent to Docker Hub
./scripts/deploy-agent-docker.sh

# Then use Terraform for ECS deployment
```

## Key Differences

| Aspect | Development | Production |
|--------|------------|------------|
| Config | `.env.dev` | `.env` |
| LiveKit | polyglot-rag-dev | polyglot-rag-assistant |
| Command | `./docker-dev.sh` | Terraform/ECS |
| Purpose | Local testing | Live service |

## Quick Commands

```bash
# Development
./docker-dev.sh up      # Start dev environment
./docker-dev.sh logs    # View logs
./docker-dev.sh down    # Stop everything

# Check what's running
docker ps

# Clean up everything
docker system prune -a
```