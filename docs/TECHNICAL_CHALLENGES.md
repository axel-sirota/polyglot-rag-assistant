# Technical Challenges and Solutions: Building a Production-Ready Polyglot Voice Assistant

## Overview

This document outlines the major technical challenges encountered while building a multilingual voice-enabled flight search assistant using LiveKit Cloud, and the solutions implemented to overcome them. These insights are designed to help conference attendees avoid common pitfalls when implementing their own voice assistants.

## Challenge 1: Audio Resampling and Sample Rate Mismatch

### Problem
The TTS (Text-to-Speech) services output audio at 24kHz, but WebRTC and LiveKit require 48kHz for proper playback. This mismatch caused:
- Silent audio tracks
- Distorted playback
- Browser compatibility issues

### Solution
Implemented real-time audio resampling using scipy:

```python
# audio_utils.py
def resample_audio(audio_data: bytes, original_rate: int = 24000, target_rate: int = 48000) -> bytes:
    """Resample audio from original_rate to target_rate"""
    # Convert bytes to numpy array
    audio_array = np.frombuffer(audio_data, dtype=np.int16)
    
    # Convert to float for resampling
    audio_float = audio_array.astype(np.float32) / 32768.0
    
    # Calculate new length and resample
    new_length = int(len(audio_float) * target_rate / original_rate)
    resampled = signal.resample(audio_float, new_length)
    
    # Convert back to int16
    resampled_int16 = (resampled * 32767).astype(np.int16)
    return resampled_int16.tobytes()
```

### Key Learnings
- Always check the sample rate of your audio sources
- WebRTC standardizes on 48kHz for compatibility
- Real-time resampling adds ~5ms latency but ensures compatibility

## Challenge 2: Voice Activity Detection (VAD) Speech Fragmentation

### Problem
Natural speech pauses were causing the VAD to fragment user input:
- "Hi. I would like" + "to find a flight" (two separate transcriptions)
- Poor user experience with interrupted thoughts
- Difficulty understanding complete user intent

### Solution
Implemented adaptive VAD configuration based on environment noise levels:

```python
# VAD configurations for different environments
VAD_CONFIGS = {
    "quiet": {
        "min_silence_duration": 0.6,    # 600ms for quiet environments
        "min_speaking_duration": 0.1,
        "threshold": 0.25,               # More sensitive
        "prefix_padding_duration": 0.1,
        "max_buffered_speech": 60.0
    },
    "medium": {
        "min_silence_duration": 0.8,    # 800ms default
        "threshold": 0.3,
    },
    "noisy": {
        "min_silence_duration": 1.0,    # 1000ms for noisy environments
        "threshold": 0.4,                # Less sensitive
    }
}

# Dynamic VAD reconfiguration
async def handle_data_received(data_packet):
    if message.get("type") == "environment_changed":
        new_env = message.get("environment", "medium")
        vad_config = VAD_CONFIGS.get(new_env, VAD_CONFIGS["medium"])
        
        # Update VAD without reconnecting
        session._vad = silero.VAD.load(**vad_config)
```

### Key Learnings
- Default VAD settings (550ms) are too aggressive for natural speech
- Environment-aware configuration dramatically improves UX
- Allow users to adjust settings for their environment

## Challenge 3: Text-Audio Synchronization

### Problem
Chat messages appeared AFTER the voice audio played, creating a jarring experience:
- Users heard the response before seeing it
- Opposite of expected ChatGPT-like behavior
- LiveKit v1.0.23 doesn't support native text streaming in STT-LLM-TTS pipeline

### Solution
Implemented a pre-speech text system with message sequencing:

```python
class SynchronizedSpeechController:
    async def synchronized_say(self, text: str) -> Any:
        """Send text first, then play audio with proper synchronization"""
        self.message_sequence += 1
        speech_id = f"speech_{self.message_sequence}_{time.time()}"
        
        # Send text to data channel immediately
        data = json.dumps({
            "type": "pre_speech_text",
            "speaker": "assistant",
            "text": text,
            "speech_id": speech_id,
            "sequence": self.message_sequence
        }).encode('utf-8')
        
        await self.room.local_participant.publish_data(data, reliable=True)
        
        # Small delay for text to render
        await asyncio.sleep(self.min_text_render_delay)
        
        # Then generate and play audio
        return await self.session.say(text, allow_interruptions=self.interruptions_enabled)
```

### Key Learnings
- Can't achieve true streaming with LiveKit v1.0.23 STT-LLM-TTS pipeline
- Data channels are perfect for metadata and synchronization
- Sequence numbers prevent message ordering issues

## Challenge 4: Multi-Language Support and Model Selection

### Problem
Supporting 40+ languages with optimal quality required:
- Different STT models for different languages
- Handling unsupported languages gracefully
- Preventing mid-conversation language switching

### Solution
Created comprehensive language configuration system:

```python
DEEPGRAM_LANGUAGE_MAP = {
    # Nova-3 for English (best quality)
    "en": {"model": "nova-3", "language": "en"},
    "en-US": {"model": "nova-3", "language": "en"},
    
    # Nova-2 for other languages (better single-language accuracy)
    "es": {"model": "nova-2", "language": "es"},
    "fr": {"model": "nova-2", "language": "fr"},
    "zh": {"model": "nova-2", "language": "zh"},
    # ... 40+ more languages
}

def get_deepgram_config(language_code: str) -> Dict[str, Any]:
    """Get optimal Deepgram configuration for a language"""
    lang_config = DEEPGRAM_LANGUAGE_MAP.get(
        language_code, 
        {"model": "nova-3", "language": "multi"}  # Fallback to multi
    )
    
    return {
        "model": lang_config["model"],
        "language": lang_config["language"],
        "punctuate": True,
        "interim_results": True,
        "endpointing": 300,
        "utterance_end_ms": 1000
    }
```

### Key Learnings
- Nova-3 is best for English, Nova-2 for other single languages
- Language locking prevents confusing mid-conversation switches
- Always have a multilingual fallback for unsupported languages

## Challenge 5: Agent Room Joining and Environment Routing

### Problem
Agents failed to join rooms in development environment:
- Production used language-suffixed room names (e.g., "room-en")
- Development needed simple room names
- URL mismatch between environments

### Solution
Environment-aware room naming and configuration:

```python
# Agent room joining logic
if IS_PRODUCTION:
    # Production: Join language-specific room
    room_name = f"{base_room_name}-{language}"
else:
    # Development: Join base room name only
    room_name = base_room_name

# Client-side configuration
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        const config = await response.json();
        LIVEKIT_URL = config.livekitUrl;
    } catch (e) {
        // Fallback to hostname detection
        LIVEKIT_URL = window.location.hostname.includes('localhost') 
            ? 'ws://localhost:7880'
            : 'wss://your-app.livekit.cloud';
    }
}
```

### Key Learnings
- Environment variables are crucial for multi-environment support
- Don't hardcode URLs - use configuration endpoints
- Room naming conventions must match between client and agent

## Challenge 6: STT-LLM-TTS Pipeline vs Realtime API

### Problem
Had to choose between OpenAI's Realtime API and LiveKit's STT-LLM-TTS pipeline:
- Realtime API promises lower latency but limited language support
- STT-LLM-TTS provides flexibility but higher latency
- LiveKit 1.1.x introduced breaking changes mid-project

### Solution
Chose STT-LLM-TTS pipeline with LiveKit 1.0.23:

```python
# Flexible pipeline allows mixing best-in-class services
session = AgentSession(
    vad=silero.VAD.load(**vad_config),      # Best open-source VAD
    stt=deepgram.STT(**stt_config),         # 40+ language support
    llm=openai.LLM(model="gpt-4"),          # Could swap for Claude/Gemini
    tts=cartesia.TTS(voice="janet")         # High-quality voice synthesis
)
```

### Key Learnings
- STT-LLM-TTS provides more control and flexibility
- Can optimize each component independently
- Easier to debug and add custom logic between stages
- Stability (1.0.23) more important than latest features for demos

## Challenge 7: Function Calling with Resilience

### Problem
Flight search APIs are unreliable and have varying response times:
- Primary API (Amadeus) has strict rate limits
- Need fallback options for demo reliability
- Must handle timeouts gracefully

### Solution
Implemented multi-tier fallback system with parallel execution:

```python
@function_tool(
    description="Search for flights between airports",
    parameters_schema=SearchFlightsArgs
)
async def search_flights(args: SearchFlightsArgs) -> AsyncGenerator[str, None]:
    yield "Searching for flights..."
    
    # Try primary API with timeout
    try:
        async with asyncio.timeout(5.0):
            results = await search_amadeus_flights(args)
            if results:
                yield format_flight_results(results)
                return
    except asyncio.TimeoutError:
        logger.warning("Amadeus API timeout")
    
    # Fallback to secondary API
    try:
        results = await search_rapidapi_flights(args)
        if results:
            yield format_flight_results(results)
            return
    except Exception as e:
        logger.error(f"RapidAPI failed: {e}")
    
    # Ultimate fallback - mock data for demos
    yield "I found several flights for your route:\n" + get_demo_flights(args)
```

### Key Learnings
- Always have fallback data for live demos
- Use asyncio.timeout for reliable timeout handling
- Parallel API calls can reduce perceived latency

## Challenge 8: Interruption Handling and Turn Detection

### Problem
Noisy environments and sensitive VAD caused issues:
- Background noise triggered interruptions
- Users couldn't complete thoughts
- Agent responses were cut off

### Solution
User-controlled interruption toggle with visual feedback:

```python
# Agent-side interruption handling
class SynchronizedSpeechController:
    def __init__(self):
        self.interruptions_enabled = True
        
    async def handle_interruption_toggle(self, enabled: bool):
        self.interruptions_enabled = enabled
        mode = "enabled" if enabled else "disabled"
        await self.synchronized_say(f"Interruptions are now {mode}")

# Client-side UI control
<button id="interruptBtn" title="Toggle interruptions">
    <span class="interrupt-icon">✋</span>
    <span class="status-text">ON</span>
</button>
```

### Key Learnings
- Let users control interruption behavior
- Visual feedback is crucial for state changes
- Consider environment when setting defaults

## Challenge 9: Message Deduplication and Sequencing

### Problem
Messages appeared multiple times or out of order:
- Race conditions between transcription events
- Multiple "thinking" indicators
- WebSocket message ordering not guaranteed

### Solution
Implemented message tracking and sequencing:

```python
# Track sent messages to prevent duplicates
sent_messages = set()

@session.on("conversation_item_added")
def on_conversation_item_added(event):
    message_id = f"{event.item.role}_{event.item.id}"
    
    # Skip if already sent via synchronized_say
    if message_id in sent_messages:
        return
        
    # Skip if this was our synchronized message
    if event.item.text_content == controller.last_synchronized_text:
        return
    
    sent_messages.add(message_id)
    # Send message with sequence number
```

### Key Learnings
- Always use message IDs for deduplication
- Sequence numbers ensure correct ordering
- Track what's been sent to prevent duplicates

## Challenge 10: Cross-Platform State Management

### Problem
Supporting web, mobile, and multiple environments with shared state:
- User preferences should persist
- Audio state must sync across platforms
- Development and production have different requirements

### Solution
Centralized state management with data channels:

```python
# Agent maintains authoritative state
participant_state = {
    "environment": "medium",
    "interruptions_enabled": True,
    "language": "en",
    "conversation_history": []
}

# Broadcast state changes to all clients
async def broadcast_state_update(state_type: str, value: Any):
    data = json.dumps({
        "type": "state_update",
        "state_type": state_type,
        "value": value,
        "timestamp": time.time()
    }).encode('utf-8')
    
    await room.local_participant.publish_data(data, reliable=True)

# Clients sync on connection
room.on('data_received', (data) => {
    const message = JSON.parse(decoder.decode(data));
    if (message.type === 'state_update') {
        updateLocalState(message.state_type, message.value);
    }
});
```

### Key Learnings
- Agent should be source of truth for state
- Data channels enable real-time state sync
- Design for platform differences from the start

## Challenge 11: Session Persistence Across Reconnections

### Problem
When users disconnected and reconnected, the agent would:
- Greet them again as if they were new
- Lose all conversation context
- Reset language preferences
- Duplicate welcome messages

### Solution
Implemented global session tracking outside of AgentSession lifecycle:

```python
# Global dictionary to store session state
PARTICIPANT_SESSIONS: Dict[str, Dict] = {}

@session.on("participant_joined")
def on_participant_joined(event):
    participant_id = event.participant.identity
    
    if participant_id in PARTICIPANT_SESSIONS:
        # Returning user - restore their session
        session_data = PARTICIPANT_SESSIONS[participant_id]
        await controller.synchronized_say(
            get_welcome_back_message(session_data["language"])
        )
    else:
        # New user - create session
        PARTICIPANT_SESSIONS[participant_id] = {
            "language": language,
            "conversation_history": [],
            "joined_at": time.time()
        }
```

### Key Learnings
- LiveKit AgentSession is ephemeral - design around it
- Use participant identity for persistent tracking
- Global state survives connection drops

## Challenge 12: OpenAI Realtime API Incompatibility

### Problem
LiveKit 1.1.5 promised OpenAI Realtime API support but had a critical gap:
- WebSocket audio stream received successfully
- AudioSource and LocalAudioTrack created
- But audio never reached track publishing pipeline

### Solution
Discovered the architectural mismatch and reverted to proven pipeline:

```python
# The broken flow in LiveKit 1.1.5:
# OpenAI Realtime → WebSocket → LiveKit Agent → [GAP] → AudioSource → Track

# Our workaround attempts:
# 1. Manual audio bridging (too complex)
# 2. Force STT-LLM-TTS fallback (worked!)
# 3. Downgrade to LiveKit 1.0.23 (final solution)
```

### Key Learnings
- New features != production ready
- Community validation is crucial
- Have a rollback plan

## Challenge 13: Spanish Language Crash Bug

### Problem
Deepgram Nova-3 multilingual model would crash specifically on Spanish:
- English worked perfectly
- Spanish caused immediate STT failure
- No clear error messages
- Random behavior across sessions

### Solution
Language-specific model routing:

```python
# Spanish MUST use Nova-2
if language_code.startswith("es"):
    return {
        "model": "nova-2",  # NOT nova-3!
        "language": "es",
        "punctuate": True
    }
```

### Key Learnings
- Test every language individually
- Model capabilities vary by language
- Document language-specific quirks

## Challenge 14: Test Tone Annoyance

### Problem
Agent played loud 1kHz test tone on every connection:
- Users getting startled
- Unprofessional for demos
- No way to disable via configuration

### Solution
Complete removal of test tone generation:

```python
# Before: generate_test_tone() was called on init
# After: Removed entirely

# If you need connection testing, use silent frames:
silent_frame = rtc.AudioFrame(
    data=bytes(960),  # Silent PCM data
    sample_rate=48000,
    num_channels=1,
    samples_per_channel=480
)
```

### Key Learnings
- Question every default behavior
- User experience > developer convenience
- Test with real users early

## Challenge 15: Docker Development Environment Complexity

### Problem
Multiple docker-compose files created confusion:
- docker-compose.yml
- docker-compose.dev.yml
- docker-compose.prod.yml
- docker-compose.override.yml
- Conflicting configurations

### Solution
Simplified to single development file:

```yaml
# docker-compose.dev.yml only
services:
  api:
    environment:
      - ENVIRONMENT=dev
      - LIVEKIT_URL=ws://host.docker.internal:7880
    ports:
      - "8000:8000"
```

### Key Learnings
- Start simple, add complexity only when needed
- One source of truth per environment
- Clear naming prevents confusion

## Challenge 16: Frontend State Synchronization

### Problem
Mobile and desktop views had state mismatches:
- Microphone button states inverted
- Environment selector out of sync
- Interruption toggle not updating
- Different users seeing different states

### Solution
Centralized state management with event broadcasting:

```javascript
// Single source of truth
const appState = {
    micEnabled: true,
    speakerEnabled: true,
    environment: 'medium',
    interruptions: true
};

// Broadcast all changes
function updateState(key, value) {
    appState[key] = value;
    
    // Update all UI elements
    document.querySelectorAll(`[data-state="${key}"]`).forEach(el => {
        updateElement(el, value);
    });
    
    // Notify agent
    publishData({
        type: 'state_update',
        key: key,
        value: value
    });
}
```

### Key Learnings
- Single source of truth prevents drift
- Data attributes enable easy binding
- Broadcast pattern ensures consistency

## Challenge 17: Audio Device Management

### Problem
Users couldn't:
- Select specific microphones
- See audio levels
- Adjust input gain
- Diagnose audio issues

### Solution
Comprehensive audio control panel:

```javascript
// Live audio level monitoring
const audioContext = new AudioContext();
const analyser = audioContext.createAnalyser();
const source = audioContext.createMediaStreamSource(stream);
source.connect(analyser);

// Gain control
const gainNode = audioContext.createGain();
gainNode.gain.value = 2.0; // 2x amplification
source.connect(gainNode);
gainNode.connect(audioContext.destination);

// Device enumeration
const devices = await navigator.mediaDevices.enumerateDevices();
const audioInputs = devices.filter(d => d.kind === 'audioinput');
```

### Key Learnings
- Web Audio API is powerful but complex
- Visual feedback builds user confidence
- Always provide manual controls

## Challenge 18: Production vs Development URL Routing

### Problem
Hardcoded URLs caused 401 errors:
- Production UI connecting to dev LiveKit
- Dev UI connecting to production API
- Invalid API keys for wrong domains

### Solution
Dynamic configuration endpoint:

```javascript
// /api/config.js
export default function handler(req, res) {
    const isDev = process.env.ENVIRONMENT === 'dev';
    
    res.json({
        livekitUrl: isDev 
            ? 'ws://localhost:7880' 
            : process.env.LIVEKIT_URL,
        apiUrl: isDev
            ? 'http://localhost:8000'
            : process.env.API_URL
    });
}
```

### Key Learnings
- Never hardcode environment-specific values
- Configuration APIs provide flexibility
- Environment variables are your friend

## Challenge 19: TTS vs Chat Formatting Dichotomy

### Problem
Same content needed different formatting:
- Chat: Markdown, bullets, line breaks
- TTS: Natural speech, no special characters
- Mixed formatting broke both

### Solution
Dual formatting system:

```python
def format_for_chat(flights):
    # Visual formatting with markdown
    return "\n".join([
        f"- **{f['airline']}** - ${f['price']}"
        for f in flights
    ])

def format_for_tts(flights):
    # Natural speech formatting
    return " ".join([
        f"{f['airline']} for {f['price']} dollars,"
        for f in flights
    ])

# Use both
chat_text = format_for_chat(results)
speech_text = format_for_tts(results)
await send_to_chat(chat_text)
await speak(speech_text)
```

### Key Learnings
- Different mediums need different formatting
- Don't compromise either experience
- Separation of concerns improves quality

## Challenge 20: WebSocket Message Reliability

### Problem
Messages arrived out of order or got lost:
- Race conditions between channels
- No delivery guarantees
- Buffering issues
- Network packet reordering

### Solution
Reliable messaging with acknowledgments:

```python
# Agent side - track sent messages
pending_acks = {}

async def send_reliable_message(data):
    msg_id = str(uuid.uuid4())
    data["msg_id"] = msg_id
    data["timestamp"] = time.time()
    
    pending_acks[msg_id] = data
    
    # Send with retry logic
    for attempt in range(3):
        await publish_data(data, reliable=True)
        
        # Wait for ack
        if await wait_for_ack(msg_id, timeout=1.0):
            del pending_acks[msg_id]
            return True
            
    logger.error(f"Message {msg_id} failed after 3 attempts")
```

### Key Learnings
- TCP-like guarantees over UDP need work
- Implement application-level acknowledgments
- Always handle the failure case

## Challenge 21: No-Microphone Testing

### Problem
Needed to test voice interactions without microphone:
- Demo machines without audio input
- Testing specific phrases
- Debugging production issues

### Solution
Text injection via data channels:

```javascript
// Test UI with text input
function injectText(text) {
    const audioData = new Float32Array(16000); // Fake audio
    
    room.localParticipant.publishData(JSON.stringify({
        type: 'injected_transcription',
        text: text,
        is_final: true,
        language: 'en'
    }));
}

// Agent handles both real and injected
@session.on("data_received")
async def handle_injection(data):
    if data["type"] == "injected_transcription":
        # Process as if from STT
        await process_user_speech(data["text"])
```

### Key Learnings
- Build testability from the start
- Data channels enable powerful debugging
- Separate concerns (audio vs text processing)

## Challenge 22: Airline Filtering Logic

### Problem
Users searching for specific airlines got no results:
- Only US airlines were mapped
- "Iberia flights" returned empty
- International carriers ignored

### Solution
Comprehensive airline mapping:

```python
AIRLINE_ALIASES = {
    # US Airlines
    "American": ["AA", "American Airlines", "American"],
    "United": ["UA", "United Airlines", "United"],
    
    # European Airlines  
    "Iberia": ["IB", "Iberia", "Iberia Airlines"],
    "British Airways": ["BA", "British Airways", "British"],
    
    # ... 50+ more airlines
}

def normalize_airline(name):
    name_upper = name.upper()
    for canonical, aliases in AIRLINE_ALIASES.items():
        if any(alias.upper() in name_upper for alias in aliases):
            return canonical
    return name
```

### Key Learnings
- Think globally from the start
- Aliases and normalization are crucial
- Test with real-world data

## Challenge 23: Thinking Indicator Timing

### Problem
"Thinking" indicator issues:
- Appeared after response started
- Multiple indicators stacking
- Never disappeared
- Confused users about state

### Solution
State-based indicator management:

```python
thinking_message_id = None

@session.on("user_speech_committed")
async def on_speech_end(text):
    global thinking_message_id
    
    # Show thinking immediately
    thinking_message_id = str(uuid.uuid4())
    await publish_data({
        "type": "thinking",
        "id": thinking_message_id,
        "text": "Let me help you with that..."
    })

@session.on("agent_response_started")  
async def on_response_start():
    global thinking_message_id
    
    # Hide thinking indicator
    if thinking_message_id:
        await publish_data({
            "type": "hide_thinking",
            "id": thinking_message_id
        })
        thinking_message_id = None
```

### Key Learnings
- Track UI state explicitly
- Clean up temporary indicators
- Immediate feedback improves perception

## Challenge 24: Audio Track Auto-Play Restrictions

### Problem
Browsers block auto-play:
- Silent failures
- User confusion
- Inconsistent across browsers
- Mobile particularly strict

### Solution
User interaction detection and fallback:

```javascript
async function playAudioTrack(track) {
    const audio = new Audio();
    audio.srcObject = new MediaStream([track]);
    
    try {
        await audio.play();
    } catch (e) {
        if (e.name === 'NotAllowedError') {
            // Show play button
            showManualPlayButton(audio);
            
            // Try on next user interaction
            document.addEventListener('click', async () => {
                await audio.play();
                hideManualPlayButton();
            }, { once: true });
        }
    }
}
```

### Key Learnings
- Browser policies change frequently
- Always handle play() promise rejection
- Provide manual fallbacks

## Challenge 25: Multi-Platform Build Complexity

### Problem
Three platforms with different requirements:
- Web: Gradio + production HTML
- Mobile: React Native + Expo
- Backend: Python + Docker
- Shared LiveKit infrastructure

### Solution
Unified build and deployment strategy:

```bash
# Single entry point for all platforms
./deploy-prod.sh

# Platform-specific builds
make build-web    # Bundles HTML/JS
make build-mobile # Expo build
make build-agent  # Docker image

# Shared configuration
cat > platforms.env <<EOF
LIVEKIT_URL=${LIVEKIT_URL}
API_URL=${API_URL}
EOF
```

### Key Learnings
- Automate everything
- Share configuration across platforms
- Single command deploys reduce errors

## Conclusion

Building a production-ready voice assistant involves solving numerous technical challenges beyond the basic happy path. The key lessons learned:

1. **Audio is hard** - Always verify sample rates, formats, and compatibility
2. **VAD needs tuning** - Default settings rarely work for production
3. **Synchronization matters** - Users expect text before audio
4. **Plan for failure** - APIs fail, networks drop, browsers misbehave
5. **Let users control** - Interruptions, environment, language preferences
6. **Test across platforms** - What works on desktop might fail on mobile
7. **Have fallbacks** - Especially critical for live demos
8. **Use data channels** - Perfect for metadata and state synchronization
9. **Track everything** - Message IDs, sequences, and state prevent bugs
10. **Choose stability** - For demos, stable versions beat cutting edge

Each challenge taught us something valuable about building real-time voice applications. The complete implementation is available in the repository, demonstrating these solutions in action across web and mobile platforms.