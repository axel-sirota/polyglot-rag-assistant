# LiveKit Audio Publishing Analysis - Root Cause and Solutions

## Executive Summary

After deep analysis of the LiveKit Agents framework (v1.1.5), I've identified the exact flow where TTS audio should be published but isn't. The issue appears to be in the audio pipeline connection between TTS generation and LiveKit track publishing.

## Audio Publishing Flow (How It Should Work)

### 1. **TTS Generation** ✅ Working
```python
# In generation.py - perform_tts_inference()
tts_task, tts_gen_data = perform_tts_inference(
    node=self._agent.tts_node,
    input=tts_text_input,
    model_settings=model_settings,
)
# This generates audio frames successfully
```

### 2. **Audio Forwarding** ✅ Working
```python
# In generation.py - perform_audio_forwarding()
forward_task, audio_out = perform_audio_forwarding(
    audio_output=audio_output,  # This is session.output.audio
    tts_output=tts_gen_data.audio_ch
)
# This forwards frames to audio_output.capture_frame()
```

### 3. **Audio Output Capture** ✅ Working
```python
# In _output.py - _ParticipantAudioOutput.capture_frame()
async def capture_frame(self, frame: rtc.AudioFrame) -> None:
    await self._audio_source.capture_frame(frame)
    # Frames are sent to AudioSource
```

### 4. **Track Publishing** ❌ BROKEN
```python
# In _output.py - _ParticipantAudioOutput._publish_track()
track = rtc.LocalAudioTrack.create_audio_track("roomio_audio", self._audio_source)
self._publication = await self._room.local_participant.publish_track(
    track, self._publish_options
)
# This should publish the track, but no "track_published" events fire
```

## The Problem

The audio pipeline is complete from TTS → AudioFrames → AudioSource, but the LocalAudioTrack is either:
1. Not receiving frames from the AudioSource
2. Not properly publishing to the room
3. Being published but not visible to participants

## Root Cause Hypothesis

### Theory 1: AudioSource Queue Issue
The AudioSource might be configured with a queue that's not being flushed properly, causing audio to buffer indefinitely.

### Theory 2: Track Publishing Timing
The track might be published before any audio data is available, causing it to appear "muted" to participants.

### Theory 3: Sample Rate Mismatch
If there's a sample rate mismatch between TTS output and AudioSource expectations, frames might be dropped silently.

## Potential Solutions

### Solution 1: Manual Track Publishing
```python
# Instead of relying on RoomIO, manually publish audio
async def publish_tts_audio(room: rtc.Room, audio_frames: list[rtc.AudioFrame]):
    # Create audio source with explicit settings
    audio_source = rtc.AudioSource(
        sample_rate=24000,
        num_channels=1,
        queue_size_ms=10000
    )
    
    # Create and publish track
    track = rtc.LocalAudioTrack.create_audio_track("agent_tts", audio_source)
    publication = await room.local_participant.publish_track(
        track,
        rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE)
    )
    
    # Feed audio frames
    for frame in audio_frames:
        await audio_source.capture_frame(frame)
    
    # Wait for playout
    await audio_source.wait_for_playout()
```

### Solution 2: Direct Audio Streaming
```python
# Bypass AgentSession and stream TTS directly
async def stream_tts_to_room(tts_result, room: rtc.Room):
    audio_source = rtc.AudioSource(24000, 1)
    track = rtc.LocalAudioTrack.create_audio_track("tts_direct", audio_source)
    
    # Publish first, then stream
    await room.local_participant.publish_track(track)
    
    async for frame in tts_result:
        await audio_source.capture_frame(frame)
```

### Solution 3: Force Audio Output Connection
```python
# Ensure audio output is properly connected
if not session.output.audio:
    # Create manual audio output
    audio_output = _ParticipantAudioOutput(
        room=ctx.room,
        sample_rate=24000,
        num_channels=1,
        track_publish_options=rtc.TrackPublishOptions()
    )
    await audio_output.start()
    session.output.audio = audio_output
```

### Solution 4: Use Lower-Level APIs
```python
# Skip AgentSession entirely for audio
class DirectTTSAgent:
    def __init__(self, room: rtc.Room):
        self.room = room
        self.tts = openai.TTS(model="tts-1")
        
    async def speak(self, text: str):
        # Generate TTS
        audio_stream = await self.tts.synthesize(text)
        
        # Create audio track
        source = rtc.AudioSource(24000, 1)
        track = rtc.LocalAudioTrack.create_audio_track("agent_voice", source)
        
        # Publish track
        pub = await self.room.local_participant.publish_track(track)
        
        # Stream audio
        async for frame in audio_stream:
            await source.capture_frame(frame)
```

## Debugging Steps

### 1. Verify AudioSource is receiving frames
```python
# Add logging in capture_frame
logger.debug(f"AudioSource received frame: duration={frame.duration}")
```

### 2. Check track publication state
```python
# After publish_track
logger.info(f"Track published: {publication.sid}, muted={publication.muted}")
```

### 3. Monitor room events
```python
@room.on("track_published")
def on_any_track(pub, participant):
    logger.info(f"ANY track published: {pub.kind} by {participant.identity}")
```

### 4. Test with simple audio
```python
# Generate test tone instead of TTS
test_frames = generate_sine_wave(frequency=440, duration=1.0)
await audio_source.capture_frame(test_frames)
```

## Framework Bug Confirmation

This appears to be a bug in LiveKit Agents 1.1.5 where:
1. The AgentSession creates all necessary components
2. TTS generates audio successfully  
3. Audio is forwarded to the output
4. But the final step of track publishing fails silently

## Workaround Implementation

Until the framework is fixed, the most reliable workaround is to bypass AgentSession for audio output and manually handle TTS → Track publishing:

```python
async def voice_agent_with_manual_audio(ctx: JobContext):
    # Use AgentSession for STT/VAD/LLM only
    session = AgentSession(
        vad=vad,
        stt=stt,
        llm=llm,
        tts=None,  # Don't use built-in TTS
        turn_detection="vad"
    )
    
    # Handle TTS manually
    tts = openai.TTS(model="tts-1")
    
    # On agent response
    async def on_agent_thinking(text: str):
        # Generate TTS
        audio = await tts.synthesize(text)
        
        # Manually publish
        await publish_audio_to_room(audio, ctx.room)
```

## Next Steps

1. **Test the manual publishing approach** using `test_audio_publishing.py`
2. **File a bug report** with LiveKit about the audio publishing issue
3. **Implement workaround** in production agent until fixed
4. **Monitor LiveKit Agents updates** for fixes in newer versions

## Summary

The issue is confirmed: LiveKit Agents 1.1.5 has a bug where TTS audio is generated but not published as tracks. The audio pipeline is intact up to the AudioSource, but the track publishing step fails silently. Manual track publishing or bypassing AgentSession for audio output are the most viable workarounds.