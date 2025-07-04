# LiveKit Cloud Setup Guide

This guide will help you set up and deploy the Polyglot Flight Assistant to LiveKit Cloud for production-ready voice interactions with proper interruption handling.

## Why LiveKit?

After experiencing issues with voice interruptions in our custom WebSocket implementation, we're migrating to LiveKit because:

1. **Battle-tested interruption handling** - LiveKit handles voice interruptions natively
2. **WebRTC infrastructure** - Low latency, high quality audio
3. **Auto-scaling** - Handles load automatically
4. **Global edge network** - Low latency worldwide
5. **OpenAI Realtime API integration** - First-class support

## Quick Start

### 1. Get LiveKit Cloud Account

1. Go to [cloud.livekit.io](https://cloud.livekit.io)
2. Sign up for a free account
3. Create a new project
4. Copy your credentials

### 2. Update .env File

Add these to your `.env`:

```bash
# LiveKit Cloud
LIVEKIT_API_KEY=your_api_key_here
LIVEKIT_API_SECRET=your_api_secret_here
LIVEKIT_URL=wss://your-project.livekit.cloud

# Existing keys you should already have
OPENAI_API_KEY=your_openai_key
AMADEUS_CLIENT_ID=your_amadeus_id
AMADEUS_CLIENT_SECRET=your_amadeus_secret
```

### 3. Install LiveKit CLI

```bash
# macOS/Linux
curl -sSL https://get.livekit.io/cli | bash

# Or with Homebrew
brew install livekit
```

### 4. Deploy the Agent

```bash
cd livekit-agent
./deploy.sh
```

### 5. Test It Out

Open `web-app/livekit-client.html` in your browser and click "Connect"!

## Architecture Overview

### Before (Custom WebSocket)
```
Browser → WebSocket → Python Server → OpenAI Realtime API
         ↓
    Interruption Issues 😢
```

### After (LiveKit Cloud)
```
Browser → WebRTC → LiveKit Cloud → Agent → OpenAI Realtime API
         ↓
    Perfect Interruptions! 🎉
```

## Development Workflow

### Local Development

1. Start the API server (for flight search):
```bash
python api_server.py
```

2. Run the LiveKit agent locally:
```bash
cd livekit-agent
./run_local.sh
```

3. Open the web client and test

### Production Deployment

```bash
cd livekit-agent
./deploy.sh
```

## Key Features with LiveKit

### 1. Natural Interruptions
- User can interrupt at any time
- Assistant stops immediately
- No audio overlap or continuation
- No phantom messages

### 2. Voice Activity Detection
```python
vad=openai.VAD(
    min_speech_duration=0.2,    # 200ms minimum speech
    min_silence_duration=0.5,   # 500ms to end turn
    padding_duration=0.3,       # 300ms padding
)
```

### 3. Multilingual Support
- Automatic language detection
- Response in user's language
- 90+ languages supported

### 4. Flight Search Integration
```python
@llm.ai_callable()
async def search_flights(origin, destination, departure_date):
    # Calls our existing flight search API
    return formatted_results
```

## Testing Voice Interactions

### Test Interruptions
1. Start the assistant talking
2. Say "stop" or start speaking
3. Assistant should stop immediately

### Test Languages
- English: "Find flights from New York to London"
- Spanish: "Buscar vuelos de Madrid a Barcelona"
- French: "Chercher des vols de Paris à Rome"
- Chinese: "查找从北京到上海的航班"

### Test Flight Search
1. "I need a flight from New York to Paris"
2. "Show me flights for tomorrow"
3. "What about next week?"

## Configuration Options

### Agent Settings

```python
assistant = agents.VoiceAssistant(
    # Interruption settings
    interrupt_min_words=1,      # Interrupt after 1 word
    allow_interruptions=True,   # Enable interruptions
    
    # Synthesis settings
    preemptive_synthesis=False, # Don't synthesize ahead
    
    # Transcription
    transcription=agents.AssistantTranscriptionOptions(
        user_transcription=True,   # Transcribe user
        agent_transcription=True,  # Transcribe assistant
    ),
)
```

### Turn Detection

```python
turn_detection=openai.realtime.ServerVadOptions(
    threshold=0.5,              # VAD threshold
    prefix_padding_ms=300,      # Pre-speech padding
    silence_duration_ms=200,    # Silence to end turn
)
```

## Monitoring & Logs

### View Live Logs
```bash
lk cloud logs --project your-project --follow
```

### View Agent Status
```bash
lk cloud agent list --project your-project
```

### Debug Mode
```bash
python realtime_agent.py dev --log-level debug
```

## Cost Optimization

LiveKit Cloud pricing:
- **Participant minutes**: $0.001 per minute
- **Bandwidth**: Included
- **Auto-scaling**: Automatic

Tips to reduce costs:
1. Set idle timeout: `shutdown_process_after_idle_timeout=60.0`
2. Use `num_idle_processes=1` for low traffic
3. Monitor usage in LiveKit dashboard

## Troubleshooting

### Agent Won't Start
- Check LiveKit credentials in `.env`
- Verify API server is running
- Check logs: `lk cloud logs --project your-project`

### No Audio
- Check browser permissions
- Verify WebRTC connection
- Test with LiveKit playground first

### Interruptions Not Working
- Verify `allow_interruptions=True`
- Check `interrupt_min_words` setting
- Monitor VAD threshold

### Language Detection Issues
- Ensure `language=None` in STT config
- Check OpenAI Realtime API language support
- Verify instructions mention multilingual support

## Next Steps

1. **Custom Domain**: Set up custom domain for your LiveKit project
2. **Analytics**: Add usage tracking and analytics
3. **Error Handling**: Implement fallback responses
4. **Load Testing**: Test with multiple concurrent users
5. **CI/CD**: Automate deployments with GitHub Actions

## Resources

- [LiveKit Docs](https://docs.livekit.io)
- [LiveKit Agents Python](https://docs.livekit.io/agents/overview/)
- [OpenAI Realtime API](https://platform.openai.com/docs/guides/realtime)
- [WebRTC Info](https://webrtc.org/)

---

With LiveKit Cloud, we've solved the voice interruption issues and created a production-ready multilingual flight assistant that scales automatically and provides excellent user experience!