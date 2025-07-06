# LiveKit Agent Audio Fix Implementation Plan

## Root Cause Identified
The agent's audio is silent because of a **sample rate mismatch** between TTS output (24kHz) and WebRTC requirements (48kHz), combined with incorrect AudioSource configuration for cloud mode.

## Implementation Steps

### Step 1: Install Required Dependencies
```bash
/Users/axelsirota/repos/polyglot-rag-assistant/.venv/bin/python3 -m pip install scipy
```

### Step 2: Create Audio Resampling Utility
Create file `polyglot-flight-agent/audio_utils.py`:
```python
import numpy as np
from scipy import signal
from livekit import rtc
import logging

logger = logging.getLogger(__name__)

def resample_audio(audio_data: bytes, original_rate: int = 24000, target_rate: int = 48000) -> bytes:
    """Resample audio from original_rate to target_rate"""
    # Convert bytes to numpy array
    audio_array = np.frombuffer(audio_data, dtype=np.int16)
    
    # Convert to float for resampling
    audio_float = audio_array.astype(np.float32) / 32768.0
    
    # Calculate new length
    new_length = int(len(audio_float) * target_rate / original_rate)
    
    # Resample
    resampled = signal.resample(audio_float, new_length)
    
    # Convert back to int16
    resampled_int16 = (resampled * 32767).astype(np.int16)
    
    logger.debug(f"Resampled audio from {original_rate}Hz to {target_rate}Hz, {len(audio_array)} -> {len(resampled_int16)} samples")
    
    return resampled_int16.tobytes()

def create_audio_frame_48khz(audio_data: bytes, duration_ms: int = 10) -> rtc.AudioFrame:
    """Create a properly formatted audio frame at 48kHz"""
    samples_per_channel = int(48000 * duration_ms / 1000)  # 480 for 10ms
    
    return rtc.AudioFrame(
        data=audio_data,
        sample_rate=48000,
        num_channels=1,
        samples_per_channel=samples_per_channel
    )
```

### Step 3: Update Agent Audio Configuration
Modify `polyglot-flight-agent/agent.py`:

#### 3.1: Import audio utilities
```python
from audio_utils import resample_audio, create_audio_frame_48khz
```

#### 3.2: Update VAD configuration for 48kHz
```python
# In prewarm function
proc.userdata["vad"] = silero.VAD.load(
    min_speech_duration=0.05,
    min_silence_duration=0.55,
    prefix_padding_duration=0.5,
    activation_threshold=0.5,
    sample_rate=48000,  # Changed from 16000 to 48000
    force_cpu=True
)
```

#### 3.3: Create custom audio output handler
Add this class before the entrypoint function:
```python
class ResamplingAudioOutput:
    """Audio output that resamples TTS audio from 24kHz to 48kHz"""
    
    def __init__(self, room: rtc.Room):
        self.room = room
        self.audio_source = rtc.AudioSource(sample_rate=48000, num_channels=1)
        self.track_published = False
        
    async def publish_track(self):
        """Publish the audio track with proper options"""
        if not self.track_published:
            track = rtc.LocalAudioTrack.create_audio_track(
                "agent_tts_audio", 
                self.audio_source
            )
            
            options = rtc.TrackPublishOptions(
                source=rtc.TrackSource.SOURCE_MICROPHONE,
                dtx=False,  # Disable DTX for TTS
                red=True,   # Enable redundancy
                audio_bitrate=64000
            )
            
            publication = await self.room.local_participant.publish_track(track, options)
            logger.info(f"✅ Published audio track: {publication}")
            self.track_published = True
    
    def capture_frame(self, frame: rtc.AudioFrame):
        """Capture audio frame, resampling if necessary"""
        if frame.sample_rate != 48000:
            # Resample to 48kHz
            resampled_data = resample_audio(
                frame.data, 
                original_rate=frame.sample_rate,
                target_rate=48000
            )
            
            # Create new frame at 48kHz
            new_frame = create_audio_frame_48khz(resampled_data)
            self.audio_source.capture_frame(new_frame)
            
            logger.debug(f"Resampled and captured frame: {frame.sample_rate}Hz -> 48000Hz")
        else:
            # Already at 48kHz
            self.audio_source.capture_frame(frame)
```

#### 3.4: Configure AgentSession with custom output
```python
# In entrypoint function, before creating AgentSession:

# Create custom audio output
custom_audio_output = ResamplingAudioOutput(ctx.room)
await custom_audio_output.publish_track()

# Configure session to use our custom output
session = AgentSession(
    vad=vad,
    stt=deepgram.STT(
        model="nova-3",
        language="en",
        sample_rate=48000  # Ensure STT expects 48kHz
    ),
    llm=openai.LLM(
        model="gpt-4o",
        temperature=0.7
    ),
    tts=cartesia.TTS(),
    turn_detection="vad"
)

# Override the audio output
session.output._audio = custom_audio_output
```

### Step 4: Add Comprehensive Logging
Add these event handlers after creating the session:
```python
# Monitor audio pipeline
@session.on("tts_started")
def on_tts_started(event):
    logger.info("🎵 TTS STARTED: Generating audio...")

@session.on("tts_audio_chunk")
def on_tts_chunk(event):
    logger.debug(f"🔊 TTS chunk: {len(event.audio)} bytes")

@session.on("agent_speech_committed")
def on_speech_committed(event):
    logger.info(f"💬 Agent speech: {event.text}")

# Log audio metrics
@session.on("metrics_collected")
def on_metrics(event):
    if hasattr(event.metrics, 'audio_duration'):
        logger.info(f"📊 Audio metrics: duration={event.metrics.audio_duration}s")
```

### Step 5: Create Test Function
Add this test function to verify audio publishing:
```python
async def test_audio_tone(room: rtc.Room, duration: float = 1.0):
    """Generate and publish a test tone at 48kHz"""
    logger.info("🔊 Generating test tone at 440Hz...")
    
    # Create audio source at 48kHz
    audio_source = rtc.AudioSource(sample_rate=48000, num_channels=1)
    
    # Create and publish track
    track = rtc.LocalAudioTrack.create_audio_track("test_tone", audio_source)
    options = rtc.TrackPublishOptions(
        source=rtc.TrackSource.SOURCE_MICROPHONE,
        dtx=False
    )
    await room.local_participant.publish_track(track, options)
    
    # Generate 440Hz tone
    sample_rate = 48000
    frequency = 440
    samples = int(sample_rate * duration)
    
    t = np.linspace(0, duration, samples)
    audio_data = np.sin(2 * np.pi * frequency * t)
    audio_data = (audio_data * 32767).astype(np.int16)
    
    # Send in 10ms chunks
    chunk_size = 480  # 10ms at 48kHz
    for i in range(0, len(audio_data), chunk_size):
        chunk = audio_data[i:i+chunk_size]
        if len(chunk) == chunk_size:
            frame = rtc.AudioFrame(
                data=chunk.tobytes(),
                sample_rate=48000,
                num_channels=1,
                samples_per_channel=chunk_size
            )
            audio_source.capture_frame(frame)
            await asyncio.sleep(0.01)  # 10ms
    
    logger.info("✅ Test tone complete - you should have heard a beep!")
```

### Step 6: Testing Sequence
1. First test the manual tone generation
2. Then test with actual TTS
3. Monitor logs for resampling events
4. Check WebRTC stats for audio levels

## Alternative Approaches

### If Resampling Doesn't Work
1. **Configure TTS for 48kHz output** (if supported):
   ```python
   tts=cartesia.TTS(
       sample_rate=48000  # If Cartesia supports this
   )
   ```

2. **Use OpenAI TTS with explicit format**:
   ```python
   tts=openai.TTS(
       model="tts-1",
       voice="nova",
       response_format="pcm",  # Raw PCM
       speed=1.0
   )
   ```

3. **Force Opus codec negotiation**:
   ```python
   options = rtc.TrackPublishOptions(
       audio_codec="opus",
       audio_bitrate=64000
   )
   ```

## Verification Steps
1. Check logs for "Resampled audio from 24000Hz to 48000Hz"
2. Monitor WebRTC stats for non-zero audio levels
3. Verify track publication with correct options
4. Test with both test tone and actual TTS

## Success Criteria
- [ ] Test tone is audible in browser
- [ ] TTS audio is resampled to 48kHz
- [ ] Agent speech is audible
- [ ] No audio dropouts or quality issues
- [ ] Consistent audio across all responses

## Notes
- The key insight is that LiveKit Cloud enforces strict WebRTC standards
- Local mode was more forgiving with sample rates
- 48kHz is the standard WebRTC sample rate
- Proper AudioSource configuration is critical
- TrackSource.SOURCE_MICROPHONE is required for cloud mode