# Development Environment Setup

## Overview

We have a complete Docker-based development environment that's isolated from production:

- **Production**: Uses `.env` and production LiveKit project
- **Development**: Uses `.env.dev` and dedicated dev LiveKit project

## Quick Start

### Start Development Environment

```bash
./docker-dev.sh up
```

This starts:
- **API Server** on http://localhost:8000
- **LiveKit Agent** on port 8082
- **Web UI Server** on http://localhost:8080

### Access Points

- **Test UI**: http://localhost:8080/polyglot-flight-agent/test-flight-ui.html
- **Chat UI**: http://localhost:8080/web-app/livekit-voice-chat.html
- **API Docs**: http://localhost:8000/docs

### View Logs

```bash
# All services
./docker-dev.sh logs

# Specific service
./docker-dev.sh logs api
./docker-dev.sh logs agent
```

### Stop Everything

```bash
./docker-dev.sh down
```

## Architecture

```
docker-compose.dev.yml
├── api (API Server)
│   ├── Port: 8000
│   ├── Uses: .env.dev
│   └── Network: polyglot-dev
│
├── agent (LiveKit Agent)
│   ├── Port: 8082
│   ├── Uses: .env.dev
│   ├── API_SERVER_URL: http://api:8000 (internal)
│   └── Network: polyglot-dev
│
└── web-ui (Static file server)
    ├── Port: 8080
    ├── Serves: test UI and chat UI
    └── Network: polyglot-dev
```

## Key Features

1. **Complete Isolation**: Dev LiveKit project (polyglot-rag-dev) is completely separate from production
2. **Single Command**: `./docker-dev.sh up` starts everything
3. **Proper Networking**: Services communicate internally via Docker network
4. **Environment Variables**: All loaded from `.env.dev`
5. **Hot Reload**: Code changes reflected after container restart

## Testing Text-Audio Synchronization

1. Start the dev environment:
   ```bash
   ./docker-dev.sh up
   ```

2. Check agent logs for environment confirmation:
   ```bash
   ./docker-dev.sh logs agent | grep ENVIRONMENT
   ```
   Should show: "🟢 ENVIRONMENT: DEVELOPMENT"

3. Open test UI: http://localhost:8080/polyglot-flight-agent/test-flight-ui.html

4. Connect and observe:
   - Text should appear ~500ms before audio
   - Check logs for "Sent pre-speech text to data channel"

## Available Commands

```bash
./docker-dev.sh up       # Start all services
./docker-dev.sh down     # Stop all services
./docker-dev.sh logs     # View all logs
./docker-dev.sh restart  # Restart services
./docker-dev.sh ps       # Show service status
./docker-dev.sh build    # Rebuild images
```

## Environment Variables

The `.env.dev` file contains:
- Dev LiveKit credentials
- Local API server URL
- All necessary API keys

**Note**: The agent container uses `http://api:8000` internally to reach the API server, while browsers use `http://localhost:8000`.

## Troubleshooting

### Services not starting?
```bash
# Check status
./docker-dev.sh ps

# View logs
./docker-dev.sh logs
```

### Need to rebuild?
```bash
./docker-dev.sh down
./docker-dev.sh build
./docker-dev.sh up
```

### Port conflicts?
Make sure ports 8000, 8080, and 8082 are not in use by other services.

## Production Deployment

When ready for production:
1. Test thoroughly in dev environment
2. Use separate deployment scripts for production
3. Never use `.env.dev` in production
4. Always verify you're deploying the right environment