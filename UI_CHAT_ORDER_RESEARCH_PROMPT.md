# Research Prompt: Fix UI Chat Display Order - Show Text Before Audio

## Problem Statement
Currently in the Polyglot RAG Assistant, when the assistant responds:
1. The TTS audio plays first
2. Then the text appears in the chat
3. We want to reverse this: show text in chat FIRST, then play audio

## Technical Context

### Current Architecture Overview
The system uses LiveKit for real-time communication with separate channels for text and audio:
- **Text Channel**: Uses LiveKit's data channel to send JSON messages with transcriptions
- **Audio Channel**: Uses LiveKit's audio track to stream TTS audio
- **These operate independently** - no built-in synchronization

### Key Components to Investigate

#### 1. Backend (LiveKit Agent - `agent.py`)
Current flow:
```python
# Lines around 300-400 in agent.py
async def handle_audio_response(self, text_response):
    # Currently:
    # 1. Sends text via data channel: agent.publish_data(...)
    # 2. TTS generates audio: tts.synthesize(...)
    # 3. Audio plays through LiveKit audio track automatically
```

Need to understand:
- How `assistant.voice_assistant.say()` works
- When exactly the data channel message is sent vs when TTS starts
- If we can delay audio playback until UI confirms text is displayed

#### 2. Web Frontend (`app.js` and `realtime-app.js`)
Current flow:
```javascript
// WebSocket message handler
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'transcript_delta') {
        // Updates chat immediately
        addMessage(data.text, 'assistant');
    } else if (data.type === 'audio_delta') {
        // Plays audio immediately
        playAudio(data.audio);
    }
};
```

Issues:
- Audio and text are processed independently
- No coordination between text display and audio playback
- Audio might arrive and play before text is fully displayed


### Potential Solutions to Research

#### Solution 1: Backend Coordination
Modify the agent to:
1. Send text message with a unique response ID
2. Wait for UI acknowledgment before starting TTS
3. Only then generate and send audio

#### Solution 2: Frontend Buffering
Modify the UI to:
1. Receive and display text immediately
2. Buffer incoming audio chunks
3. Play audio only after text is fully displayed (with small delay)

#### Solution 3: LiveKit Event Coordination
Use LiveKit's event system:
1. Agent publishes a "text_ready" event
2. UI displays text and publishes "text_displayed" event
3. Agent only then starts TTS generation

### Code Locations to Examine

1. **agent.py**:
   - `_create_and_run_assistant()` method
   - `handle_function_calls_and_respond()` method
   - Any calls to `assistant.say()` or TTS generation
   - Data channel publishing logic

2. **app.js / realtime-app.js**:
   - WebSocket message handlers
   - `playAudio()` function
   - `addMessage()` or chat update functions
   - Audio queue management

3. **conversation_manager.js**:
   - Message ordering logic
   - Queue processing
   - Timing controls


### Specific Questions to Answer

1. **Timing Analysis**:
   - When exactly does the agent send text vs start TTS?
   - Can we measure the delay between text send and audio start?
   - Is there existing delay/buffer logic we can leverage?

2. **LiveKit Capabilities**:
   - Can we pause/delay audio track playback?
   - Can we use custom events for coordination?
   - Is there a way to sync data channel with audio track?

3. **Frontend Control**:
   - Can we buffer audio on the client side?
   - How to ensure text is rendered before audio plays?
   - Should we add artificial delay or wait for render confirmation?

### Testing Approach
1. Add logging to trace exact timing of:
   - Text message sent from agent
   - Text displayed in UI
   - Audio generation started
   - Audio playback started

2. Test with various response lengths:
   - Short responses (might display instantly)
   - Long responses (might have progressive updates)
   - Multi-sentence responses

3. Test across web implementations:
   - LiveKit Voice Chat (primary)
   - WebSocket app
   - Different network conditions

### Implementation Priority
Given this is a demo project:
1. **Quick Fix**: Add a simple delay in frontend before playing audio
2. **Better Fix**: Buffer audio and play after text display confirmation
3. **Best Fix**: Proper event-based coordination between agent and UI

### Example Quick Fix Code
```javascript
// In app.js or realtime-app.js
let audioBuffer = [];
let textDisplayed = false;

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'transcript_delta' || data.type === 'response_complete') {
        addMessage(data.text, 'assistant');
        textDisplayed = true;
        
        // Play any buffered audio after a small delay
        setTimeout(() => {
            audioBuffer.forEach(audio => playAudio(audio));
            audioBuffer = [];
        }, 100); // 100ms delay to ensure text renders
    } 
    else if (data.type === 'audio_delta') {
        if (textDisplayed) {
            playAudio(data.audio);
        } else {
            audioBuffer.push(data.audio);
        }
    }
};
```

## Next Steps
1. Locate exact code sections where text is sent and audio is generated
2. Identify the best interception point for delaying audio
3. Implement minimal change that works across all platforms
4. Test thoroughly with different response types and lengths

## Actual Code Implementation Details

### 1. Backend - LiveKit Agent (agent.py)

#### Text Message Publishing via Data Channel
```python
# Lines 700-714: User transcription sent to UI
@session.on("user_input_transcribed")
def on_user_input_transcribed(event):
    if event.is_final:  # Only send final transcriptions
        logger.info(f"💬 USER SAID: '{event.transcript}'")
        # Send to data channel for chat UI
        try:
            data = json.dumps({
                "type": "transcription",
                "speaker": "user", 
                "text": event.transcript
            }).encode('utf-8')
            asyncio.create_task(ctx.room.local_participant.publish_data(data, reliable=True))
            logger.info(f"✅ Sent user transcription to data channel")
        except Exception as e:
            logger.error(f"Error sending user transcription: {e}")

# Lines 717-738: Assistant response sent to UI
@session.on("conversation_item_added") 
def on_conversation_item_added(event):
    if event.item.role == "assistant":
        logger.info(f"🗣️ Agent speaking: {event.item.text_content}")
        # Send to data channel for chat UI
        try:
            data = json.dumps({
                "type": "transcription", 
                "speaker": "assistant",
                "text": event.item.text_content
            }).encode('utf-8')
            asyncio.create_task(ctx.room.local_participant.publish_data(data, reliable=True))
            logger.info(f"✅ Sent agent transcription to data channel")
        except Exception as e:
            logger.error(f"Error sending agent transcription: {e}")
```

#### Audio Generation and TTS Events
```python
# Lines 754-760: TTS lifecycle events
@session.on("tts_started")
def on_tts_started(event):
    logger.info("🎵 TTS STARTED: Generating audio...")

@session.on("tts_stopped") 
def on_tts_stopped(event):
    logger.info("🎵 TTS STOPPED")

# Lines 275-342: Audio resampling and output
class ResamplingAudioOutput(io.AudioOutput):
    """Audio output that resamples TTS audio from 24kHz to 48kHz"""
    
    def capture_frame(self, frame: rtc.AudioFrame):
        """Capture audio frame, resampling if necessary"""
        if frame.sample_rate != 48000:
            # Resample to 48kHz
            resampled_data = resample_audio(
                frame.data, 
                original_rate=frame.sample_rate,
                target_rate=48000
            )
            # Audio is automatically sent through LiveKit audio track
```

### 2. Web Frontend - LiveKit Voice Chat (livekit-voice-chat.html)

#### Data Channel Message Handler
```javascript
// Lines 1373-1395: Data channel receives both text and audio
async function handleDataReceived(payload, participant, kind) {
    const data = new TextDecoder().decode(payload);
    
    try {
        const parsedData = JSON.parse(data);
        console.log('Data received:', parsedData);
        
        switch (parsedData.type) {
            case 'transcript':
            case 'transcription':
                if (parsedData.speaker === 'user') {
                    chatUI.addMessage(parsedData.text, 'user');
                } else if (parsedData.speaker === 'assistant' || parsedData.speaker === 'agent') {
                    chatUI.addMessage(parsedData.text, 'assistant');
                } else if (parsedData.speaker === 'system') {
                    chatUI.addMessage(parsedData.text, 'system');
                }
                break;
            // ... other cases
        }
    } catch (error) {
        console.error('Error parsing data:', error);
    }
}
```

**Note**: In LiveKit, audio comes through the audio track automatically, not through data channel!

### 3. Web App with WebSocket (app.js)

#### WebSocket Message Handler with Separate Audio
```javascript
// Lines 97-149: Handle different message types
async handleServerMessage(data) {
    switch (data.type) {
        case 'user_transcript':
            // Show what the user said
            this.addUserMessage(data.text);
            break;
            
        case 'transcript_delta':
            // Real-time assistant transcript update
            this.updateTranscript(data.text);
            break;
            
        case 'audio_delta':
            // Real-time audio response
            if (data.audio) {
                await this.playAudioChunk(data.audio);
            }
            break;
            
        case 'response_complete':
            // Complete response received
            if (data.text) {
                this.addAssistantMessage(data.text);
            }
            if (data.audio) {
                await this.playAudio(data.audio);
            }
            break;
    }
}

// Lines 367-398: Audio playback function
async playAudio(base64Audio) {
    try {
        // Decode base64 to blob
        const byteCharacters = atob(base64Audio);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        
        // Create blob with proper MIME type
        const blob = new Blob([byteArray], { type: 'audio/mpeg' });
        const audioUrl = URL.createObjectURL(blob);
        
        // Create and play audio
        const audio = new Audio(audioUrl);
        await audio.play();
    } catch (error) {
        console.error('Failed to play audio:', error);
    }
}
```

### 4. Realtime App with Audio Queue (realtime-app.js)

#### Advanced Audio Queue Management
```javascript
// Lines 244-295: Handle transcript and audio deltas separately
case 'transcript_delta':
    // Assistant's response transcription
    if (this.conversationManager) {
        await this.conversationManager.handleConversationUpdate({
            item: {
                id: data.item_id || data.response_id || `assistant-${Date.now()}`,
                type: 'message',
                role: 'assistant'
            },
            delta: { text: data.delta }
        });
    }
    break;
    
case 'audio_delta':
    // Check if this audio should be played
    const responseId = data.response_id || data.item_id;
    if (this.interruptionManager && !this.interruptionManager.shouldPlayAudioChunk(responseId)) {
        console.log(`Discarding audio from interrupted response: ${responseId}`);
        break;
    }
    
    // Queue audio for playback
    if (data.audio) {
        const audioData = this.base64ToArrayBuffer(data.audio);
        this.audioQueue.push({
            data: audioData,
            responseId: responseId
        });
        if (!this.isPlaying) {
            this.playAudioQueue();
        }
    }
    break;

// Lines 386-459: Audio queue playback
async playAudioQueue() {
    if (this.audioQueue.length === 0) {
        this.isPlaying = false;
        return;
    }
    
    this.isPlaying = true;
    const audioChunk = this.audioQueue.shift();
    
    // ... convert and play audio through Web Audio API
    const source = this.audioContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(this.gainNode);
    
    source.onended = () => {
        // Continue with next chunk
        this.playAudioQueue();
    };
    
    source.start(0);
}
```

### 5. Conversation Manager for Message Ordering (conversation_manager.js)

#### Message Queue and Ordering Logic
```javascript
// Lines 25-41: Queue message updates
async handleConversationUpdate(event) {
    const { item, delta } = event;
    
    // Queue the update
    this.messageQueue.push({ 
        type: 'update', 
        item, 
        delta, 
        timestamp: Date.now() 
    });
    
    // Process queue if not already processing
    if (!this.isProcessingQueue) {
        await this.processMessageQueue();
    }
}

// Lines 115-155: Ensure proper message ordering
async addToDisplayOrder(itemId, role) {
    const item = this.items.get(itemId);
    item.displayTimestamp = Date.now();
    
    if (role === 'user') {
        // User messages always go at the end
        this.displayOrder.push(itemId);
        this.createMessageElement(item);
    } else if (role === 'assistant') {
        // Find the correct position for assistant message
        let insertIndex = this.displayOrder.length;
        
        // Look for the most recent user message
        for (let i = this.displayOrder.length - 1; i >= 0; i--) {
            const displayItem = this.items.get(this.displayOrder[i]);
            if (displayItem && displayItem.role === 'user') {
                // Insert after this user message
                insertIndex = i + 1;
                break;
            }
        }
        
        // Add delay to ensure proper ordering
        await this.sleep(150);
    }
}
```

## Key Insights from Code Analysis

### Current Flow:
1. **Agent Side**:
   - Text is sent immediately when `conversation_item_added` event fires
   - TTS generates audio separately and streams it through LiveKit audio track
   - No coordination between text and audio sending

2. **Frontend Side**:
   - LiveKit app: Text comes via data channel, audio via audio track (separate)
   - WebSocket apps: Text and audio come as separate message types
   - Both are processed immediately upon receipt

### The Problem:
- Text and audio are sent through different channels
- Audio might start playing before text is displayed
- No synchronization mechanism exists

### Proposed Solution Points:
1. **Backend**: Delay TTS generation until text is confirmed displayed
2. **Frontend**: Buffer audio until text is rendered
3. **Hybrid**: Use response IDs to coordinate text/audio pairs

## Recommended Implementation for LiveKit Voice Chat

Since the main issue is that LiveKit audio track plays immediately while text comes via data channel, here's the simplest solution:

### Frontend-Only Solution (Quickest)

In the LiveKit agent, we need to add a delay before TTS starts. Since we can't easily control LiveKit's audio track playback from the frontend, we need to modify the agent:

```python
# In agent.py, modify the conversation_item_added handler:
@session.on("conversation_item_added") 
def on_conversation_item_added(event):
    if event.item.role == "assistant":
        logger.info(f"🗣️ Agent speaking: {event.item.text_content}")
        # Send to data channel for chat UI FIRST
        try:
            data = json.dumps({
                "type": "transcription", 
                "speaker": "assistant",
                "text": event.item.text_content
            }).encode('utf-8')
            asyncio.create_task(ctx.room.local_participant.publish_data(data, reliable=True))
            logger.info(f"✅ Sent agent transcription to data channel")
            
            # ADD DELAY HERE to ensure text displays first
            async def delayed_speech():
                await asyncio.sleep(0.5)  # 500ms delay for text to render
                # The TTS will start after this delay
            
            asyncio.create_task(delayed_speech())
            
        except Exception as e:
            logger.error(f"Error sending agent transcription: {e}")
```

### Better Solution: Control TTS Timing

Since LiveKit Agents v1.0.23 uses STT-LLM-TTS pipeline, we can potentially control when TTS starts:

```python
# Instead of automatic TTS, manually control it:
@session.on("agent_message_ready")
def on_agent_message_ready(event):
    # 1. Send text to UI first
    send_text_to_ui(event.text)
    
    # 2. Wait for confirmation or fixed delay
    await asyncio.sleep(0.3)
    
    # 3. Then trigger TTS
    session.say(event.text)
```

### Alternative: Frontend Audio Control

For WebSocket-based apps (app.js, realtime-app.js), the solution is already shown in the Example Quick Fix Code section - buffer audio until text is displayed.

## Critical Finding

The main challenge is that **LiveKit's audio track plays automatically** when TTS generates audio. Unlike WebSocket apps where we control playback, LiveKit handles audio streaming internally. This means the solution must be implemented in the agent to delay TTS generation, not just audio playback.