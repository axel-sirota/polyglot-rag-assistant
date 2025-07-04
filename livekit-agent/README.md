# LiveKit Agent for Polyglot Flight Assistant

This is the LiveKit Cloud implementation of our multilingual flight search assistant using OpenAI's Realtime API.

## Features

- **Real-time voice interaction** with automatic speech detection
- **Multilingual support** - speaks 90+ languages automatically
- **Natural interruptions** - interrupt the assistant at any time
- **Flight search** - real-time flight search with pricing
- **WebRTC infrastructure** - reliable, low-latency audio streaming

## Setup

### 1. Get LiveKit Credentials

1. Go to [LiveKit Cloud](https://cloud.livekit.io)
2. Create a new project
3. Copy your API Key and Secret
4. Add them to your `.env` file:

```bash
LIVEKIT_API_KEY=your_api_key_here
LIVEKIT_API_SECRET=your_api_secret_here
LIVEKIT_URL=wss://your-project.livekit.cloud
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Locally (Development)

```bash
# Make sure the API server is running first
cd ..
python api_server.py

# In another terminal, run the agent
cd livekit-agent
./run_local.sh
```

### 4. Deploy to LiveKit Cloud

```bash
./deploy.sh
```

## Architecture

```
User Browser
    ↓ (WebRTC)
LiveKit Cloud
    ↓ (WebSocket)
LiveKit Agent (this code)
    ↓ (HTTP)
Flight Search API (api_server.py)
    ↓
Amadeus API
```

## How It Works

1. **User connects** to LiveKit room via web browser
2. **Agent joins** the same room automatically
3. **Voice Activity Detection** detects when user speaks
4. **OpenAI Realtime API** processes speech in real-time
5. **Interruptions** are handled natively by LiveKit
6. **Flight searches** call our backend API
7. **Responses** are streamed back with low latency

## Key Files

- `realtime_agent.py` - Main agent implementation
- `requirements.txt` - Python dependencies
- `deploy.sh` - Deploy to LiveKit Cloud
- `run_local.sh` - Run locally for development

## Testing

1. Start the API server (for flight search)
2. Run the agent locally
3. Open `web-app/livekit-client.html` in your browser
4. Click "Connect"
5. Start speaking in any language!

## Deployment

The agent can be deployed to LiveKit Cloud for production use:

```bash
./deploy.sh
```

This will:
- Upload your agent code
- Install dependencies
- Start the agent on LiveKit's infrastructure
- Auto-scale based on demand

## Troubleshooting

### "No module named 'livekit'"
```bash
pip install -r requirements.txt
```

### "LiveKit credentials not configured"
Make sure your `.env` file has:
```
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
```

### "Connection failed"
1. Check your internet connection
2. Verify LiveKit credentials are correct
3. Make sure the API server is running (for flight search)

## Language Support

The agent automatically detects and responds in the user's language:
- Spanish: "Buscar vuelos de Madrid a Barcelona"
- English: "Find flights from New York to London"
- French: "Chercher des vols de Paris à Rome"
- Chinese: "查找从北京到上海的航班"
- And 90+ more languages!

## Performance

- **Latency**: < 500ms typical response time
- **Interruptions**: Immediate (< 100ms)
- **Scalability**: Auto-scales with LiveKit Cloud
- **Reliability**: 99.9% uptime with LiveKit infrastructure