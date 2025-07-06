# Next Steps to Debug LiveKit Agent Audio Issue

## Quick Summary
Agent publishes an audio track (browser subscribes to it) but the track is SILENT. We need to find out why.

## Immediate Action Items

### 1. Add Extensive Logging to Audio Pipeline
```python
# Add these debug points to agent.py:

# Log when TTS starts generating
@session.on("tts_started") 
def on_tts_started(event):
    logger.info(f"🎵 TTS STARTED: Generating audio...")

# Log audio frame events
@session.on("audio_frame_generated")
def on_audio_frame(event):
    logger.info(f"🔊 Audio frame: {event.frame.duration}ms")

# Log when audio is sent to output
@session.on("audio_output_started")
def on_audio_output(event):
    logger.info(f"📤 Audio being sent to output...")

# Monitor the actual audio source
# Check if session.output.audio exists and has data
```

### 2. Test Pre-recorded Audio
Create a simple test to play a known-good audio file:
```python
# This eliminates TTS as a variable
import wave
audio_file = wave.open("test_audio.wav", 'rb')
# Send frames directly to session output
# If this works → TTS integration issue
# If this fails → Audio publishing issue
```

### 3. Inspect Audio Track State
```python
# After agent connects, check:
# - Is audio track actually publishing data?
# - What's the track's state?
# - Are there any audio levels?

# Add to room event handlers:
@ctx.room.on("track_published")
def on_track_published(publication, participant):
    if publication.kind == rtc.TrackKind.KIND_AUDIO:
        logger.info(f"📡 Audio track state: {publication}")
        # Check if track has actual audio data
```

### 4. Test Manual Audio Publishing
```python
# Bypass AgentSession - create our own audio track
async def test_manual_audio():
    # Create audio source
    audio_source = rtc.AudioSource(24000, 1)
    
    # Create and publish track
    track = rtc.LocalAudioTrack.create_audio_track("agent_audio", audio_source)
    publication = await room.local_participant.publish_track(track)
    
    # Generate simple sine wave
    import numpy as np
    sample_rate = 24000
    duration = 1.0
    frequency = 440  # A4 note
    
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = np.sin(2 * np.pi * frequency * t)
    
    # Convert to int16
    audio_data = (audio_data * 32767).astype(np.int16)
    
    # Send frames
    frame = rtc.AudioFrame(
        sample_rate=sample_rate,
        num_channels=1,
        samples_per_channel=len(audio_data),
        data=audio_data.tobytes()
    )
    audio_source.capture_frame(frame)
    
    logger.info("✅ Manual audio sent - check if you hear a beep!")
```

### 5. Check Audio Output Configuration
```python
# Verify session has audio output configured
logger.info(f"Session audio output: {session.output.audio}")
logger.info(f"Session has room IO: {session._room_io}")

# Check if audio output is properly connected
if session.output.audio:
    logger.info("Audio output is configured")
else:
    logger.error("NO AUDIO OUTPUT CONFIGURED!")
```

### 6. Compare with Working Example
Find ANY working LiveKit Python agent example:
- Check LiveKit examples repository
- Look for playground or demo agents
- Compare initialization code line-by-line
- Find what we're missing

### 7. Test Different Configurations
```python
# Try different session configurations:

# Option 1: Explicit output configuration
from livekit.agents.voice import room_io
room_output_options = room_io.RoomOutputOptions(
    audio_enabled=True,
    transcription_enabled=True,
    audio_track_name="agent_audio"
)

# Option 2: Different TTS settings
tts=openai.TTS(
    model="tts-1",
    voice="nova",
    speed=1.0,
    sample_rate=24000  # Explicitly set sample rate
)

# Option 3: No turn detection
session = AgentSession(
    stt=deepgram.STT(),
    llm=openai.LLM(),
    tts=openai.TTS(),
    # No VAD, no turn_detection
)
```

### 8. Monitor WebRTC Stats
In browser console:
```javascript
// Get peer connection stats
pc = room.engine.subscriber.pc
stats = await pc.getStats()
stats.forEach(stat => {
    if (stat.type === 'inbound-rtp' && stat.kind === 'audio') {
        console.log('Audio stats:', stat)
        // Check: bytesReceived, packetsReceived, audioLevel
    }
})
```

## Priority Order

1. **Test manual audio publishing** (Test #4) - This will tell us if the issue is with AgentSession or deeper
2. **Add extensive logging** - We need to see exactly where audio stops flowing
3. **Check audio output configuration** - Ensure session.output.audio exists
4. **Test pre-recorded audio** - Eliminate TTS as a variable
5. **Monitor WebRTC stats** - Confirm if ANY audio data is being sent

## Key Questions to Answer

1. Is `session.output.audio` properly configured?
2. Are TTS frames reaching the AudioSource?
3. Can we publish ANY audio (even manually)?
4. What's different between our setup and working examples?

## Success Metrics

- [ ] Identify exactly where audio stops flowing
- [ ] Successfully play ANY sound through the agent
- [ ] Understand the difference between our setup and working agents
- [ ] Implement a fix that produces audible agent speech

The browser IS subscribing to an audio track, so we're 90% there. We just need to figure out why that track is empty!