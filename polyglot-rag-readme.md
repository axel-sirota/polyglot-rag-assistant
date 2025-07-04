# Polyglot RAG Assistant - Setup & Deployment Guide

🌍 A multilingual, voice-enabled flight search assistant powered by LiveKit, OpenAI, Anthropic Claude, and LangGraph for autonomous RAG capabilities.

## 📁 Project Structure

```
polyglot-rag-assistant/
│
├── backend/                    # Core backend services
│   ├── agent/                  # LiveKit agent implementation
│   │   ├── __init__.py
│   │   ├── main.py            # LiveKit agent entry point
│   │   └── requirements.txt
│   │
│   ├── mcp_servers/           # Model Context Protocol servers
│   │   ├── __init__.py
│   │   └── flight_search_server.py
│   │
│   ├── rag/                   # RAG implementation
│   │   ├── __init__.py
│   │   ├── embeddings.py      # OpenAI embeddings
│   │   ├── vector_store.py    # FAISS vector store
│   │   └── retrieval.py       # RAG pipeline
│   │
│   ├── langgraph/             # Autonomous agent logic
│   │   ├── __init__.py
│   │   ├── flight_agent.py    # Flight search agent
│   │   └── workflows.py       # LangGraph workflows
│   │
│   ├── api/                   # FastAPI services
│   │   ├── __init__.py
│   │   └── main.py
│   │
│   └── utils/                 # Shared utilities
│       ├── __init__.py
│       ├── config.py
│       └── flight_apis.py     # Flight API integrations
│
├── web-app/                   # Web interface
│   ├── gradio_demo.py         # Gradio interface
│   ├── static/                # Static assets
│   └── requirements.txt
│
├── mobile-app/                # Mobile applications
│   └── react-native/          # React Native app
│       ├── App.tsx
│       ├── package.json
│       └── components/
│
├── docker/                    # Docker configurations
│   ├── docker-compose.yml
│   ├── Dockerfile.backend
│   └── Dockerfile.web
│
├── scripts/                   # Deployment scripts
│   ├── demo.sh               # Quick demo launcher
│   └── deploy.sh             # Production deployment
│
├── .env.example              # Environment template
├── requirements.txt          # Root requirements
└── README.md                # This file
```

## 🚀 Quick Start (3-Day Sprint Guide)

### Day 1: Core Setup & Backend
```bash
# Clone and setup
git clone https://github.com/axel-sirota/polyglot-rag-assistant
cd polyglot-rag-assistant

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install LiveKit CLI
curl -sSL https://get.livekit.io/cli | bash

# Copy and configure environment
cp .env.example .env
# Add your API keys (see credentials section)

# Test backend components
cd backend && python -m pytest
```

### Day 2: Voice & Web Interface
```bash
# Start MCP Server
cd backend
python -m mcp_servers.flight_search_server

# Deploy LiveKit agent (new terminal)
cd backend/agent
lk cloud agent deploy --project polyglot-rag

# Launch Gradio interface (new terminal)
cd web-app
python gradio_demo.py --share
```

### Day 3: Mobile & Integration Testing
```bash
# Setup mobile app
cd mobile-app/react-native
npm install
expo start --tunnel

# Run full system test
./scripts/demo.sh
```

## 🔑 Required Credentials

### 1. LiveKit Cloud (REQUIRED for voice features)
Sign up at https://cloud.livekit.io

```bash
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxxxxxxxxx
LIVEKIT_API_SECRET=secretxxxxxxxxxxxxx
```

### 2. OpenAI (REQUIRED for STT/TTS/embeddings)
Get from https://platform.openai.com/api-keys

```bash
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx

# Required models:
# - whisper-1 (speech-to-text)
# - tts-1 (text-to-speech)
# - gpt-4o-mini (agent logic)
# - text-embedding-3-small (RAG embeddings)
```

### 3. Anthropic Claude (REQUIRED for advanced reasoning)
Get from https://console.anthropic.com/

```bash
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
# Requires: claude-3-5-sonnet-20241022
```

### 4. Flight Search API (CHOOSE ONE)

#### Option A: Aviationstack (Free tier available)
```bash
AVIATIONSTACK_API_KEY=xxxxxxxxxxxxx
# Free: 100 requests/month
```

#### Option B: Amadeus (Production ready)
```bash
AMADEUS_CLIENT_ID=xxxxxxxxxxxxx
AMADEUS_CLIENT_SECRET=xxxxxxxxxxxxx
# Test environment available
```

#### Option C: SerpAPI (Web scraping fallback)
```bash
SERPAPI_API_KEY=xxxxxxxxxxxxx
```

### Complete `.env` file:
```bash
# LiveKit (Required)
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxxxxxxxxx
LIVEKIT_API_SECRET=secretxxxxxxxxxxxxx

# OpenAI (Required)
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx

# Anthropic (Required)
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx

# Flight API (Choose one)
AVIATIONSTACK_API_KEY=xxxxxxxxxxxxx
# AMADEUS_CLIENT_ID=xxxxxxxxxxxxx
# AMADEUS_CLIENT_SECRET=xxxxxxxxxxxxx

# MCP Server
MCP_SERVER_PORT=8765

# Vector Database
FAISS_INDEX_PATH=./data/faiss_index
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1024

# Development
GRADIO_SHARE=true
GRADIO_SERVER_PORT=7860
EXPO_PUBLIC_API_URL=http://localhost:8000

# Redis Cache (optional)
REDIS_URL=redis://localhost:6379
```

## 🏗️ Architecture Overview

### Core Components

1. **Voice Pipeline (LiveKit + OpenAI)**
   - Silero VAD for voice activity detection
   - OpenAI Whisper for STT
   - OpenAI TTS for speech synthesis
   - LiveKit Cloud for WebRTC infrastructure

2. **RAG System (FAISS + OpenAI Embeddings)**
   - Document ingestion and chunking
   - Vector storage with FAISS
   - Hybrid search (semantic + keyword)
   - Context-aware retrieval

3. **Autonomous Agent (LangGraph)**
   - Intent detection and routing
   - Multi-step parameter extraction
   - External API orchestration
   - Fallback mechanisms

4. **Flight Search Integration**
   - Primary: Aviationstack/Amadeus
   - Fallback: Web scraping via SerpAPI
   - Caching layer for common queries

## 🧪 Testing Components

### 1. Test Voice Pipeline
```python
# test_voice.py
import asyncio
from backend.agent.voice_pipeline import VoiceRAGPipeline

async def test_voice():
    pipeline = VoiceRAGPipeline()
    
    # Test with sample audio
    with open("test_audio.mp3", "rb") as f:
        result = await pipeline.process_voice_input(f)
        print(f"Response: {result}")

asyncio.run(test_voice())
```

### 2. Test RAG System
```python
# test_rag.py
from backend.rag.vector_store import FAISSVectorStore
from backend.rag.retrieval import RAGPipeline

# Initialize
vector_store = FAISSVectorStore()
rag = RAGPipeline(vector_store)

# Test query
response = rag.query("Find flights from NYC to Paris")
print(response)
```

### 3. Test Flight Agent
```python
# test_agent.py
from backend.langgraph.flight_agent import FlightSearchAgent

agent = FlightSearchAgent()
result = agent.search({
    "query": "I need a flight from New York to London next week"
})
print(result)
```

## 🌐 Web Interface (Gradio)

The Gradio interface provides:
- Voice input/output
- Multilingual support
- Real-time streaming responses
- Flight search visualization
- Conversation history

Access at: `http://localhost:7860` or public URL when using `--share`

## 📱 Mobile App Deployment

### Quick Setup with Expo

```bash
cd mobile-app/react-native
npm install

# Configure backend URL in App.tsx
const BACKEND_URL = "http://YOUR_IP:8000"
const LIVEKIT_URL = "wss://your-project.livekit.cloud"

# Start development server
expo start --tunnel
```

### Testing on Device
- **iOS**: Scan QR code with Camera app
- **Android**: Use Expo Go app

## 🚀 Production Deployment

### Using Docker Compose

```bash
# Build and start all services
docker-compose up --build

# Scale backend services
docker-compose up --scale backend=3
```

### LiveKit Cloud Deployment

```bash
cd backend/agent

# Deploy agent to LiveKit Cloud
lk cloud agent deploy --project polyglot-rag

# Monitor logs
lk cloud logs -f --project polyglot-rag
```

### Kubernetes Deployment (Optional)

```bash
# Apply configurations
kubectl apply -f k8s/

# Check status
kubectl get pods -n polyglot-rag
```

## 🔧 Troubleshooting

### Common Issues

1. **LiveKit Connection Failed**
   ```bash
   # Verify credentials
   lk cloud project list
   
   # Test connection
   lk room create test-room
   ```

2. **API Rate Limits**
   - Add delays between API calls
   - Implement exponential backoff
   - Use Redis caching

3. **Voice Recognition Issues**
   - Check microphone permissions
   - Verify Whisper API access
   - Test with different audio formats

4. **Mobile App Can't Connect**
   ```bash
   # Find your local IP
   ifconfig | grep inet  # Mac/Linux
   ipconfig              # Windows
   
   # Update App.tsx with correct IP
   ```

## 📊 Performance Optimization

### Caching Strategy
- Redis for session state
- In-memory cache for embeddings
- API response caching (30min TTL)

### Latency Targets
- Voice recognition: <300ms
- LLM response: <500ms
- Total round-trip: <1s

### Scaling Considerations
- Use GPU instances for embeddings
- Implement connection pooling
- Consider edge deployment for voice

## 🎯 Demo Checklist

- [ ] All API keys configured
- [ ] LiveKit agent deployed
- [ ] Gradio interface accessible
- [ ] Mobile app tested
- [ ] Sample queries prepared
- [ ] Backup demo video ready
- [ ] Hotspot for backup internet

## 📚 Additional Resources

- [LiveKit Documentation](https://docs.livekit.io/)
- [LangGraph Tutorial](https://python.langchain.com/docs/langgraph)
- [OpenAI API Reference](https://platform.openai.com/docs)
- [FAISS Documentation](https://github.com/facebookresearch/faiss)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

---

**Remember**: Working demo > Perfect code! Focus on core functionality first, optimize later. 🚀