# Polyglot RAG - Setup & Deployment Guide

A multilingual voice-enabled flight search assistant powered by LiveKit, OpenAI, and Anthropic Claude.

## 🚀 Quick Start (You have 3 days!)

```bash
# Clone and setup
git clone <your-repo>
cd polyglot-rag
pip install -r requirements.txt
npm install -g expo-cli @livekit/cli

# Copy environment file
cp .env.example .env
# Add your keys (see below)

# Run everything
./demo.sh
```

## 🔑 Required Credentials

### 1. LiveKit Cloud (REQUIRED)
Sign up at https://cloud.livekit.io

```bash
# Get your credentials from LiveKit Cloud dashboard
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxxxxxxxxx
LIVEKIT_API_SECRET=secretxxxxxxxxxxxxx

# Install LiveKit CLI
curl -sSL https://get.livekit.io/cli | bash
lk cloud login
```

### 2. OpenAI (REQUIRED)
Get from https://platform.openai.com/api-keys

```bash
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx

# You'll need access to:
# - Whisper (speech-to-text)
# - TTS (text-to-speech)
# - GPT-4o-mini (for agents)
# - text-embedding-3-small
```

### 3. Anthropic Claude (REQUIRED)
Get from https://console.anthropic.com/

```bash
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx

# Make sure you have access to:
# - claude-3-5-sonnet-20241022
```

### 4. Flight Search API (CHOOSE ONE)

#### Option A: Aviationstack (Recommended - Free tier)
Sign up at https://aviationstack.com/signup/free

```bash
AVIATIONSTACK_API_KEY=xxxxxxxxxxxxx
# Free: 100 requests/month
```

#### Option B: SerpAPI
Sign up at https://serpapi.com/

```bash
SERPAPI_API_KEY=xxxxxxxxxxxxx
# Free trial available
```

#### Option C: RapidAPI (Multiple flight APIs)
Sign up at https://rapidapi.com/

```bash
RAPIDAPI_KEY=xxxxxxxxxxxxx
# Various free tiers
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
# OR
SERPAPI_API_KEY=xxxxxxxxxxxxx

# MCP Server
MCP_SERVER_PORT=8765

# Development
GRADIO_SHARE=true
EXPO_PUBLIC_API_URL=http://localhost:8000
```

## 🧪 Local Testing

### 1. Test LiveKit Connection
```bash
# Test LiveKit CLI is working
lk --version
lk cloud list-projects

# Create a test room
lk room create test-room

# Generate test tokens
lk token create --identity test-user --room test-room
```

### 2. Test Backend Components

```bash
# Test MCP Server
cd backend
python -m mcp_servers.flight_search_server

# In another terminal, test the MCP server
curl http://localhost:8765/health

# Test voice agent locally (without LiveKit Cloud)
python main.py --dev
```

### 3. Test API Connections
```python
# Create test_apis.py
import os
from dotenv import load_dotenv
import openai
import anthropic

load_dotenv()

# Test OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")
response = openai.audio.transcriptions.create(
    model="whisper-1",
    file=open("test_audio.mp3", "rb")
)
print(f"✅ OpenAI Whisper: {response.text}")

# Test Anthropic
client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=50,
    messages=[{"role": "user", "content": "Hello"}]
)
print(f"✅ Anthropic Claude: {response.content[0].text}")

# Test Flight API
# ... your chosen API test
```

## 🌐 Web App Deployment

### Option 1: Gradio (Quick Demo - Day 1-2)

```bash
cd web-app
python gradio_demo.py
```

This will output:
```
Running on local URL:  http://127.0.0.1:7860
Running on public URL: https://xxxxx.gradio.live
```

Share the public URL for instant demo access!

#### Gradio Tips:
- Use `share=True` for public URL
- Use `server_name="0.0.0.0"` for network access
- Add `auth=("demo", "password")` for basic auth

### Option 2: Production Web (Day 3 if time)

```bash
# Simple Python server for local testing
cd web-app
python -m http.server 8080

# For production, deploy to Vercel
npm i -g vercel
vercel --prod
```

### Option 3: Expose Local via Ngrok
```bash
# If Gradio share isn't working
ngrok http 7860
```

## 📱 Mobile App Deployment

### 1. Quick Setup with Expo

```bash
cd mobile-app/react-native

# Install dependencies
npm install

# Start Expo dev server
expo start --tunnel
```

This generates a QR code. On your phone:
- **iOS**: Scan with Camera app
- **Android**: Scan with Expo Go app

### 2. Configure Mobile Backend

```typescript
// In App.tsx, update the URL
const LIVEKIT_URL = "wss://your-project.livekit.cloud";

// For local testing
const LIVEKIT_URL = "ws://192.168.1.100:7880"; // Your computer's IP
```

### 3. Quick Mobile Deployment

#### For Demo (Recommended):
```bash
# Just use Expo Go - no build needed!
expo start --tunnel
# Share the exp://xxx.xxx.xxx URL
```

#### For TestFlight/Beta (If time):
```bash
# iOS
expo build:ios

# Android APK
expo build:android -t apk
```

## 🚀 LiveKit Cloud Deployment

### 1. Deploy the Agent

```bash
cd backend

# First time setup
lk cloud agent scaffold

# Deploy
lk cloud agent deploy --project polyglot-rag

# Check logs
lk cloud logs -f
```

### 2. Get Connection Details

```bash
# Get your WebSocket URL
lk cloud project info

# It will show:
# URL: wss://polyglot-rag.livekit.cloud
# API Key: APIxxxxx
# Secret: secretxxxxx
```

## 🎤 Testing Everything Together

### 1. Full System Test
```bash
# Terminal 1: MCP Server
cd backend && python -m mcp_servers.flight_search_server

# Terminal 2: Deploy Agent
cd backend && lk cloud agent deploy

# Terminal 3: Web App
cd web-app && python gradio_demo.py --share

# Terminal 4: Mobile
cd mobile-app/react-native && expo start --tunnel
```

### 2. Test Conversation Flow

Try these in order:
1. **English**: "Find flights from New York to Paris next week"
2. **Spanish**: "Buscar vuelos de Madrid a Barcelona"
3. **French**: "Chercher des vols Paris Londres"
4. **Switch Languages**: Start in English, continue in Spanish

### 3. Monitor Everything

```bash
# LiveKit logs
lk cloud logs -f --project polyglot-rag

# Local logs
tail -f backend/logs/*.log
```

## 🔧 Troubleshooting

### LiveKit Issues
```bash
# Can't connect?
lk cloud project list
lk room list

# Reset everything
lk room delete --all
lk cloud agent stop
```

### API Rate Limits
```python
# Add delays if hitting limits
import time
time.sleep(0.5)  # Between API calls
```

### Mobile Can't Connect
```bash
# Check your IP
ifconfig | grep inet

# Update mobile app config with your computer's IP
const LOCAL_IP = "192.168.1.XXX";
```

### Gradio Share Failed
```bash
# Use ngrok instead
pip install pyngrok
# Add to your gradio_demo.py:
from pyngrok import ngrok
public_url = ngrok.connect(7860)
print(f"Public URL: {public_url}")
```

## 📋 Demo Day Checklist

- [ ] All API keys in `.env`
- [ ] LiveKit agent deployed
- [ ] Gradio public URL working
- [ ] Mobile app on your phone
- [ ] Test audio file ready
- [ ] Backup responses prepared
- [ ] Phone hotspot ready (backup internet)
- [ ] Screen recording software ready

## 🎯 Quick Commands Reference

```bash
# Deploy everything
./demo.sh

# Just the web app
python web-app/gradio_demo.py --share

# Just the mobile app
cd mobile-app/react-native && expo start --tunnel

# Just the backend
lk cloud agent deploy

# Monitor logs
lk cloud logs -f

# Emergency restart
pkill -f python
lk cloud agent stop
./demo.sh
```

## 💡 Pro Tips

1. **Test with a friend**: Have someone else try the mobile app
2. **Record everything**: Use OBS to record working demos
3. **Prepare offline mode**: Have cached responses ready
4. **Multiple devices**: Test on iOS and Android
5. **Backup plan**: If LiveKit fails, show Gradio only

## 🆘 Emergency Contacts

- LiveKit Discord: https://livekit.io/discord
- OpenAI Status: https://status.openai.com
- Anthropic Status: https://status.anthropic.com

Good luck with your demo! Remember: Working > Perfect 🚀