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

The complete implementation is available in the repository, demonstrating these solutions in action across web and mobile platforms.