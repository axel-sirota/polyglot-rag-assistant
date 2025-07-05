# LiveKit Audio Output Issue - Comprehensive Research Request V3

## Executive Summary
LiveKit agent successfully generates audio through TTS (both OpenAI and Cartesia) but NO AUDIO is heard by participants. The audio is created internally but never published as LiveKit tracks. This is a critical architectural issue preventing any voice output.

## Current State - Everything Works Except Audio Output

### What's Working ✅
1. **Agent Connection & State Management**
   - Agent connects to LiveKit Cloud successfully
   - Proper state transitions: `listening -> thinking -> speaking -> listening`
   - Room connection established with participants
   - WebRTC peer connection active

2. **Speech Recognition (STT)**
   - Deepgram STT working perfectly
   - User speech transcribed correctly: "Hello hello"
   - Language detection working (English detected)

3. **Language Model (LLM)**
   - GPT-4 processes requests successfully
   - Generates appropriate responses
   - Function calling available for flight search

4. **Text-to-Speech (TTS) Generation**
   - Both OpenAI TTS and Cartesia TTS generate audio successfully
   - Metrics show audio duration generated (3.274s, 3.065s)
   - TTS requests complete with 200 OK status

### What's NOT Working ❌
1. **No Audio Track Publishing**
   - ZERO "Track published" or "📡" events in logs
   - No LocalTrackPublication events
   - No audio tracks visible to participants
   - WebRTC shows no incoming audio from agent

2. **Missing Audio Pipeline**
   - Audio generated but not routed to LiveKit room
   - No track publishing despite successful TTS
   - RoomIO appears to not be publishing audio tracks

## Detailed Log Analysis

### Successful TTS Generation (OpenAI)
```
2025-07-05 14:57:37,230 - 🎵 Speech created - Audio channel active: source='say'
HTTP Request: POST https://api.openai.com/v1/audio/speech "HTTP/1.1 200 OK"
TTSMetrics: audio_duration=3.274s, cancelled=False, characters_count=53
```

### Successful TTS Generation (Cartesia)
```
2025-07-05 14:57:43,260 - TTSMetrics: 
  - request_id='1053c6ede91f'
  - ttfb=0.537s
  - duration=1.675s
  - audio_duration=3.065s
  - cancelled=False
  - streamed=True
```

### Missing Track Publishing
```
# Expected but NEVER seen:
📡 Track published: audio by agent-XXX
on_track_published fired
LocalTrackPublication created
```

## Code Implementation Details

### Current Configuration
```python
# Using STT-LLM-TTS pipeline (OpenAI Realtime disabled due to bug)
session = AgentSession(
    vad=vad,
    stt=deepgram.STT(model="nova-3", language="en"),
    llm=openai.LLM(model="gpt-4o", temperature=0.7),
    tts=cartesia.TTS(),  # Also tried openai.TTS(model="tts-1")
    turn_detection="vad"
)

# Initial greeting sent successfully
await session.say(
    "Hello! I'm your multilingual flight search assistant.",
    allow_interruptions=True
)
```

### Event Handlers Configured
```python
@session.on("speech_created")  # ✅ Fires
@session.on("agent_state_changed")  # ✅ Fires
@session.on("metrics_collected")  # ✅ Fires
@ctx.room.on("track_published")  # ❌ NEVER fires for agent audio
```

## Environment & Versions
- LiveKit Agents: 1.1.5
- LiveKit SDK: 1.0.11
- LiveKit Plugins:
  - livekit-plugins-openai: 1.1.5
  - livekit-plugins-deepgram: 1.1.5
  - livekit-plugins-cartesia: 1.1.5
  - livekit-plugins-silero: 1.1.5
- Python: 3.11
- Platform: macOS Darwin 22.6.0

## Critical Discovery from Testing

### OpenAI TTS Issue
- Model name was wrong initially (fixed to "tts-1")
- TTS now generates audio successfully
- But still no track publishing

### Cartesia TTS Test
- Switched to Cartesia as alternative
- Audio generates successfully with streaming
- But still no track publishing

### Pattern Observed
1. TTS generates audio → Success ✅
2. Audio data exists in memory → Success ✅
3. Audio should publish to room → FAILS ❌
4. Participants hear nothing → Problem persists

## Previous Research Findings

### From V1 Research
- Removing `session.say()` broke audio channel initialization
- Added `generate_reply()` to initialize audio channel
- This didn't fix the issue

### From V2 Research
- Discovered audio is generated but not published as tracks
- OpenAI Realtime has architectural gap with LiveKit 1.1.5
- Recommended STT-LLM-TTS fallback (currently implemented)

## New Questions for Research

### 1. Track Publishing Architecture
- **How does AgentSession publish audio tracks in LiveKit 1.1.5?**
- Is there a manual step required to publish TTS audio as tracks?
- Does RoomIO need explicit configuration for audio output?
- Are there any additional initialization steps for track publishing?

### 2. Audio Pipeline Investigation
- **What's the exact flow from TTS audio generation to track publishing?**
- Where in the pipeline is the audio getting stuck?
- Is there a buffer or queue that's not being flushed?
- Are there any callbacks or promises not being resolved?

### 3. Room Configuration
- Does the room need specific configuration for agent audio?
- Are there permissions or capabilities missing?
- Is AutoSubscribe.AUDIO_ONLY affecting output as well as input?

### 4. Known Issues & Workarounds
- **Is this a known bug in LiveKit Agents 1.1.5?**
- Are there any patches or workarounds available?
- Do other users report similar issues with STT-LLM-TTS pipeline?
- Is there a specific version that fixes this?

### 5. Alternative Approaches
- Can we manually create and publish audio tracks?
- Is there a lower-level API to bypass AgentSession?
- Can we use RoomIO directly to publish audio?
- Are there working examples that actually produce audio?

## Debugging Attempts Made

### 1. TTS Provider Switch
- ❌ OpenAI TTS (with correct model) - Audio generated, not published
- ❌ Cartesia TTS - Audio generated, not published

### 2. Configuration Changes
- ✅ Fixed OpenAI TTS model name to "tts-1"
- ✅ Added all event handlers for debugging
- ✅ Verified API keys and permissions
- ❌ Still no audio output

### 3. Code Patterns Tried
- ✅ Using `session.say()` for initial greeting
- ✅ Agent responds to user input
- ✅ State transitions work correctly
- ❌ No audio track publishing occurs

## WebRTC Analysis
From browser WebRTC internals:
- User microphone track subscribed by agent ✅
- Agent participant visible in room ✅
- No audio tracks from agent participant ❌
- getUserMedia successful for user ✅

## Hypothesis

The issue appears to be in the LiveKit Agents framework itself, specifically:

1. **Missing Track Publishing Step**: The AgentSession is generating audio but not automatically publishing it as a LiveKit track
2. **RoomIO Integration Issue**: The bridge between TTS output and room track publishing is broken
3. **Framework Bug**: This might be a known issue in LiveKit Agents 1.1.5 with the STT-LLM-TTS pipeline

## Request for Expert Analysis

Please help identify:

1. **Root Cause**: Why is TTS audio not being published as LiveKit tracks?
2. **Solution**: How to make the audio audible to participants?
3. **Workaround**: Any immediate fixes or alternative approaches?
4. **Code Example**: A working example of STT-LLM-TTS with actual audio output

## Additional Context

### Working Example Needed
We need a minimal working example that:
- Uses LiveKit Agents 1.1.5
- Implements STT-LLM-TTS pipeline
- Actually produces audible output
- Shows track publishing events

### Specific Questions
1. Is `session.say()` the right method for TTS output?
2. Do we need to manually publish tracks after TTS?
3. Is there a missing initialization step?
4. Are there any debug flags to see the audio pipeline?

## Test Scenarios

### Scenario 1: Initial Greeting
```
Expected: Agent says "Hello! I'm your multilingual flight search assistant."
Actual: Silence (but speech_created event fires)
```

### Scenario 2: User Interaction
```
User: "Hello hello"
Expected: Agent responds with greeting
Actual: Agent state changes to speaking, but no audio heard
```

## Log Patterns

### Successful Pattern (What we see)
```
1. 🎤 Audio track subscribed from user
2. 🤖 Agent state: listening
3. User speaks
4. STT transcribes successfully
5. LLM generates response
6. TTS creates audio
7. 🤖 Agent state: speaking
8. TTSMetrics show audio generated
9. 🤖 Agent state: listening
```

### Missing Pattern (What we need)
```
10. 📡 Track published: audio
11. Audio track active in WebRTC
12. Participants hear agent speech
```

## Summary

This is a critical issue where the entire voice pipeline works except for the final step - making the audio audible. The agent is effectively mute despite successfully generating speech. We need expert guidance on how to bridge the gap between TTS audio generation and LiveKit track publishing in the current framework version.

Please provide specific code examples or patches that will make the audio output work. The entire system is ready except for this final audio publishing step.