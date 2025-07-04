# OpenAI Realtime API Refactoring Plan

## Current Issues to Fix

1. **No VAD (Voice Activity Detection)** - Currently using hold-to-talk instead of automatic detection
2. **No real-time transcription** - UI shows "[Voice message]" instead of actual transcript
3. **Language detection errors** - Sending "english" instead of ISO-639-1 "en"
4. **Text chat not working** - Text input sends to wrong endpoint
5. **No audio playback** - Response audio not playing in browser

## Architecture Problems

Our current implementation has fundamental misunderstandings:
- We're treating it like a traditional STT→LLM→TTS pipeline
- Not using WebSocket events properly
- Missing real-time transcription events
- No proper VAD implementation
- Not leveraging LiveKit's OpenAI integration

## Proposed Architecture

### Option 1: Pure OpenAI Realtime (Direct WebSocket)
```
Browser ←→ WebSocket ←→ OpenAI Realtime API
   ↓                         ↓
Web Audio API          Function Calling
   ↓                         ↓
MediaRecorder          Flight Search
```

### Option 2: LiveKit + OpenAI Realtime (Recommended)
```
Browser ←→ WebRTC ←→ LiveKit ←→ OpenAI Realtime
   ↓                    ↓              ↓
Native Audio       Automatic VAD   Function Calling
                   Transcription    Flight Search
```

## Implementation Plan

### Phase 1: Fix Immediate Issues (2 hours)

1. **Fix Language Detection**
   - ✅ Already fixed - Whisper returns ISO-639-1 codes

2. **Implement Real-time Transcription Display**
   ```javascript
   // In app.js handleServerMessage()
   case 'transcript_delta':
       this.updateUserTranscript(data.text);
       break;
   
   case 'response_complete':
       if (data.input_text) {
           this.addUserMessage(data.input_text);
       }
       this.addAssistantMessage(data.text);
       break;
   ```

3. **Fix Text Chat**
   ```javascript
   // Process text through voice pipeline
   async processTextQuery(text) {
       // Convert text to speech first
       const tts = await this.textToSpeech(text);
       // Send as audio
       await this.sendAudioData(tts);
   }
   ```

4. **Enable Audio Playback**
   - Fix audio format (base64 → audio buffer)
   - Use Web Audio API for streaming playback

### Phase 2: Implement Proper VAD (4 hours)

1. **Update Backend to Support VAD**
   ```python
   # In realtime_client.py
   self.session_config = {
       "model": "gpt-4o-realtime-preview",
       "modalities": ["text", "audio"],
       "voice": "alloy",
       "turn_detection": {
           "type": "server_vad",  # Enable automatic detection
           "threshold": 0.5,
           "prefix_padding_ms": 300,
           "silence_duration_ms": 500,
           "create_response": True
       },
       "input_audio_transcription": {
           "model": "whisper-1"  # Enable transcription
       }
   }
   ```

2. **Update Frontend for Continuous Streaming**
   ```javascript
   class VoiceAssistant {
       async startContinuousRecording() {
           // Request microphone once
           const stream = await navigator.mediaDevices.getUserMedia({ 
               audio: {
                   echoCancellation: true,
                   noiseSuppression: true,
                   autoGainControl: true,
                   sampleRate: 24000  // Match API requirement
               }
           });
           
           // Create audio worklet for real-time processing
           const audioContext = new AudioContext({ sampleRate: 24000 });
           const source = audioContext.createMediaStreamSource(stream);
           
           // Stream audio continuously
           await audioContext.audioWorklet.addModule('audio-processor.js');
           const processor = new AudioWorkletNode(audioContext, 'audio-processor');
           
           source.connect(processor);
           processor.port.onmessage = (e) => {
               // Send PCM16 audio chunks to server
               this.sendAudioChunk(e.data);
           };
       }
   }
   ```

3. **Handle Transcription Events**
   ```python
   # In realtime_client.py process_events()
   elif event_type == "conversation.item.input_audio_transcription.completed":
       yield {
           "type": "user_transcript",
           "text": event["transcript"],
           "item_id": event["item_id"]
       }
   ```

### Phase 3: Refactor to LiveKit Architecture (8 hours)

1. **Create New LiveKit Agent**
   ```python
   # agents/openai_realtime_agent.py
   from livekit import agents, rtc
   from livekit.agents import openai
   
   class FlightSearchAssistant:
       def __init__(self):
           self.assistant = openai.RealtimeAssistant(
               instructions="""You are a multilingual flight search assistant.
               Help users find flights in any language they speak.
               Always respond in the same language as the user.""",
               voice="alloy",
               temperature=0.8,
               turn_detection=openai.ServerVAD(
                   threshold=0.5,
                   silence_duration_ms=500
               ),
               tools=[self.search_flights_tool()]
           )
       
       def search_flights_tool(self):
           return openai.AssistantTool(
               name="search_flights",
               description="Search for flights",
               parameters={...},
               handler=self.handle_flight_search
           )
       
       async def handle_flight_search(self, **kwargs):
           # Call our flight service
           return await flight_service.search_flights(**kwargs)
   ```

2. **Update Web Client to Use WebRTC**
   ```javascript
   // Use LiveKit SDK instead of raw WebSocket
   import { Room, RoomEvent, RemoteTrack } from 'livekit-client';
   
   class LiveKitVoiceAssistant {
       async connect() {
           this.room = new Room();
           
           // Handle events
           this.room.on(RoomEvent.TrackSubscribed, this.handleTrackSubscribed);
           this.room.on(RoomEvent.DataReceived, this.handleDataReceived);
           
           // Connect to LiveKit
           await this.room.connect(LIVEKIT_URL, token);
           
           // Publish microphone
           await this.room.localParticipant.setMicrophoneEnabled(true);
       }
   }
   ```

### Phase 4: Production Optimizations (4 hours)

1. **Implement Audio Worklet for Low Latency**
   ```javascript
   // audio-processor.js
   class AudioProcessor extends AudioWorkletProcessor {
       process(inputs, outputs, parameters) {
           const input = inputs[0];
           if (input.length > 0) {
               // Convert to PCM16
               const pcm16 = this.convertToPCM16(input[0]);
               this.port.postMessage(pcm16);
           }
           return true;
       }
   }
   ```

2. **Add Conversation Context Management**
   ```python
   # Track conversation items
   self.conversation_items = []
   
   # Allow manual context addition
   async def add_context(self, text: str):
       message = {
           "type": "conversation.item.create",
           "item": {
               "type": "message",
               "role": "system",
               "content": [{"type": "text", "text": text}]
           }
       }
       await self._send_message(message)
   ```

3. **Implement Interruption Handling**
   ```python
   async def handle_interruption(self):
       # Truncate current response
       message = {
           "type": "conversation.item.truncate",
           "item_id": self.current_item_id,
           "content_index": 0,
           "audio_end_ms": 0
       }
       await self._send_message(message)
   ```

## Migration Strategy

### Step 1: Quick Fixes (Today)
1. Fix transcription display in UI
2. Enable basic audio playback
3. Fix text chat to work with voice pipeline

### Step 2: VAD Implementation (Tomorrow)
1. Update backend for server_vad
2. Implement continuous audio streaming
3. Add real-time transcription display

### Step 3: LiveKit Migration (Day 3)
1. Deploy LiveKit agent with OpenAI Realtime
2. Update web client to use WebRTC
3. Test all languages and features

## Expected Outcomes

1. **Seamless Conversations**: No more holding button, natural speech detection
2. **Real-time Feedback**: See transcription as you speak
3. **Lower Latency**: <300ms response time with WebRTC
4. **Better UX**: Interruption handling, natural conversation flow
5. **Cost Effective**: Only process audio when user is speaking

## Demo Day Advantages

1. **"Wow" Factor**: Real-time transcription looks impressive
2. **Natural Feel**: Like talking to a real assistant
3. **Multilingual Magic**: Seamless language switching
4. **Professional**: No awkward button holding

## Code Examples

### Minimal Working VAD Setup
```python
# Backend
async def setup_realtime_vad():
    config = {
        "turn_detection": {
            "type": "server_vad",
            "create_response": True
        },
        "input_audio_transcription": {
            "model": "whisper-1"
        }
    }
    await realtime_client.update_session(config)

# Frontend
async function startListening() {
    // Just start streaming, VAD handles everything
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    // ... stream to server
}
```

### Event Flow for Demo
```
User speaks → VAD detects → Transcription streams → 
User stops → VAD triggers → Function call → 
Flight search → Response generates → Audio streams back
```

This refactoring will transform the experience from a clunky hold-to-talk interface to a smooth, natural conversation system perfect for the conference demo.