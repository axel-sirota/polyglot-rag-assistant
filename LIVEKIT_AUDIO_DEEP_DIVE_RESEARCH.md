# LiveKit Agent Audio Issue - Deep Research Request

## Executive Summary
We have a LiveKit voice agent that appears to be working perfectly EXCEPT no audio is heard. The browser shows the agent's audio track is subscribed, but the track appears to be silent/empty. This issue persists across both LiveKit Agents 1.1.5 and 1.0.23.

## Current Situation

### What We Know Works ✅
1. **Agent connects to LiveKit Cloud successfully**
   - Shows as `agent-AJ_aRe5R4iusCW5` in browser
   - WebSocket connection established
   - Room joined without errors

2. **Audio track IS published**
   - Browser console shows: `Track subscribed: audio agent-AJ_aRe5R4iusCW5`
   - This means LiveKit recognizes an audio track from the agent
   - The track exists but appears to contain no audio data

3. **All components initialize**
   - VAD (Silero) loads successfully
   - STT (Deepgram) connects 
   - LLM (GPT-4) responds
   - TTS (Cartesia/OpenAI) claims to generate audio
   - No errors in initialization

4. **State transitions work correctly**
   - Agent states: listening → thinking → speaking → listening
   - User speech detected and transcribed
   - LLM generates responses
   - TTS metrics show audio duration (e.g., 3.065s)

### What Doesn't Work ❌
- **No audible output** - Complete silence from agent
- **Audio track is empty** - Track exists but contains no audio data
- **Same issue in both 1.1.5 and 1.0.23** - Not version-specific

## Critical Evidence

### Browser Console Output
```javascript
publishing track {room: 'flight-demo', participant: 'user-1751763764067', ...}
silence detected on local audio track {room: 'flight-demo', participant: 'user-1751763764067', ...}
Participant connected: agent-AJ_aRe5R4iusCW5
Track subscribed: audio agent-AJ_aRe5R4iusCW5  // <-- Audio track EXISTS but is SILENT
```

### Agent Logs Pattern
```
✅ STT-LLM-TTS pipeline configured with Deepgram STT + GPT-4 + Cartesia TTS
✅ Agent session started successfully
🎵 Speech created - Audio channel active
📊 TTSMetrics: audio_duration=3.065s, cancelled=False
🤖 Agent state changed: speaking -> listening
```

Missing: Any logs about audio frames being sent to the track

## Technical Architecture

### Current Implementation
```python
# LiveKit Agents 1.0.23
session = AgentSession(
    vad=silero.VAD.load(force_cpu=True),
    stt=deepgram.STT(model="nova-3", language="en"),
    llm=openai.LLM(model="gpt-4o", temperature=0.7),
    tts=cartesia.TTS(),  # Also tried openai.TTS(model="tts-1")
    turn_detection="vad"
)
await session.start(agent=agent, room=ctx.room)
```

### Audio Flow (Theory)
1. TTS generates audio frames → ✅ (metrics show duration)
2. Frames sent to AudioSource → ❓ (no logs confirm this)
3. AudioSource publishes as LocalAudioTrack → ✅ (track exists)
4. Track contains audio data → ❌ (silent/empty)

## Research Questions

### 1. Audio Frame Delivery
- Are TTS audio frames actually being delivered to the AudioSource?
- Is there a buffer or queue that's not being flushed?
- Are the audio frames in the correct format (sample rate, channels)?

### 2. AudioSource Configuration
- Is the AudioSource properly configured with correct sample rate (24000 Hz)?
- Are frames being captured via `audio_source.capture_frame()`?
- Is there a timing issue with frame delivery?

### 3. Track Publishing
- Why does the track exist but contain no audio?
- Is the track being published before audio data is available?
- Is there a race condition between track creation and audio generation?

### 4. Session Output Configuration
- Is `session.output.audio` properly set?
- Does the session need explicit audio output configuration?
- Is RoomIO properly bridging the audio?

### 5. Framework Integration
- Is there a missing initialization step?
- Do we need to manually configure the audio pipeline?
- Are there undocumented requirements for audio output?

## Code Investigation Needed

### 1. Find Where Audio Frames Go
```python
# In TTS generation
# Where do frames go after being generated?
# Look for: audio_source.capture_frame() calls
```

### 2. Verify AudioSource Creation
```python
# How is AudioSource created and configured?
# Look for: rtc.AudioSource(sample_rate, num_channels)
```

### 3. Track Publishing Logic
```python
# When and how is the audio track published?
# Look for: room.local_participant.publish_track()
```

### 4. Debug Audio Pipeline
```python
# Add logging at each step:
# - TTS frame generation
# - Frame delivery to AudioSource  
# - AudioSource buffer state
# - Track publishing events
```

## Hypothesis

The audio track is being published BEFORE audio data is available, creating an empty track. OR the audio frames are being generated but not properly routed to the AudioSource that backs the published track.

## Required Investigation

1. **Trace audio frame path** - Follow frames from TTS to track
2. **Check timing** - When is track published vs when audio is ready?
3. **Verify format** - Are audio frames in correct format?
4. **Test manual publishing** - Can we manually create and publish audio?
5. **Compare working examples** - Find ANY working LiveKit agent with audio

## Test Scenarios

### Test 1: Manual Audio Publishing
```python
# Create AudioSource manually
audio_source = rtc.AudioSource(24000, 1)
track = rtc.LocalAudioTrack.create_audio_track("test", audio_source)
await room.local_participant.publish_track(track)

# Generate and send audio frames manually
# This will confirm if the issue is with AgentSession or deeper
```

### Test 2: Direct TTS to Track
```python
# Bypass AgentSession completely
# Generate TTS audio and publish directly
# This isolates the issue to AgentSession vs LiveKit SDK
```

### Test 3: Pre-recorded Audio
```python
# Play a pre-recorded audio file through the agent
# This eliminates TTS as a variable
# If this works, issue is with TTS integration
# If this fails, issue is with audio publishing
```

## Ultimate Questions

1. **Why is the audio track empty when it's successfully published?**
2. **Where exactly are the TTS audio frames going?**
3. **What is the EXACT code path from TTS generation to audible output?**
4. **Is there a working example ANYWHERE of LiveKit Agents producing audio?**

## Success Criteria

Find and implement a solution that results in:
- Audible agent speech in the browser
- Consistent audio output for all TTS responses
- Clear understanding of the audio pipeline
- Reproducible fix that works reliably

Please investigate this comprehensively. We need to understand WHY the audio track exists but is silent, and HOW to make it contain actual audio data. The agent is SO CLOSE to working - we just need sound!