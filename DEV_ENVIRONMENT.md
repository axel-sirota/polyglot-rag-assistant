# Development Environment Setup

## Overview

We now have separate LiveKit projects for development and production:

- **Production**: `polyglot-rag-assistant` (wss://polyglot-rag-assistant-3l6xagej.livekit.cloud)
- **Development**: `polyglot-rag-dev` (wss://polyglot-rag-dev-qieglig5.livekit.cloud)

This separation ensures safe testing without affecting production users.

## Quick Start

### 1. Test Agent Locally

```bash
cd polyglot-flight-agent
./run-dev.sh
```

This will:
- Load `.env.dev` automatically
- Show "🟢 ENVIRONMENT: DEVELOPMENT" in logs
- Connect to the dev LiveKit project

### 2. Test with Docker

```bash
# Run with dev environment (default)
./run-docker.sh

# Run with prod environment (be careful!)
./run-docker.sh prod
```

### 3. Test Web UI

```bash
cd polyglot-flight-agent
./serve-test-ui.sh
```

Then open http://localhost:8080/test-flight-ui.html

## Environment Files

- `.env` - Production credentials (don't modify unless deploying)
- `.env.dev` - Development credentials (safe for testing)

## How It Works

1. Scripts detect which environment to use
2. Dev environment uses separate LiveKit project
3. Agent logs show which environment is active
4. No risk of affecting production during testing

## Testing the Text-Audio Synchronization

1. Start the agent with dev environment:
   ```bash
   cd polyglot-flight-agent
   ./run-dev.sh
   ```

2. Look for these key logs:
   - "🟢 ENVIRONMENT: DEVELOPMENT"
   - "🔄 Creating synchronized speech controller"
   - "📤 Sent pre-speech text to data channel"

3. Connect via web UI and verify:
   - Greeting text appears before audio
   - No production users are affected

## Safety Features

- Dev environment clearly labeled in logs
- Different LiveKit URL prevents accidental production access
- `.env.dev` is gitignored to prevent credential leaks
- Default to dev environment for local testing

## Troubleshooting

If you see "🔴 ENVIRONMENT: PRODUCTION", stop immediately and check:
- Which script you're running
- Which .env file is being loaded
- The LIVEKIT_URL value

Always verify you see "🟢 ENVIRONMENT: DEVELOPMENT" before testing!