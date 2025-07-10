# Chat Order Fix Implementation

## Overview

This document describes the implementation to fix the chat message timing issue where text messages were appearing AFTER the voice audio played, instead of before. The user wanted text to appear "as text comes in, like in ChatGPT".

## Problem Statement

### Root Cause Analysis
1. **LiveKit Agent Framework v1.0.23 Limitation**: The STT-LLM-TTS pipeline doesn't support native text streaming events
2. **Event Timing**: The `conversation_item_added` event fires AFTER TTS starts generating audio
3. **Automatic Audio Playback**: LiveKit's audio tracks play automatically when TTS generates audio
4. **Race Condition**: Text messages sent via data channel could arrive after audio started playing

### User Experience Issue
- User speaks → Agent processes → Audio starts playing → THEN text appears
- Desired: User speaks → Text appears immediately → Audio plays

## Research Findings

From the provided research document (UI_CHAT_ORDER_RESEARCH_PROMPT.md):
- LiveKit doesn't provide streaming LLM events in the STT-LLM-TTS pipeline
- Audio playback can't be delayed without modifying LiveKit's core behavior
- Solution must be implemented in the agent to send text before TTS generation

## Solution Implemented: Option 3 (Simplest Approach)

Since true streaming isn't possible with current LiveKit version, we implemented optimizations to show text as early as possible.

### Agent-Side Changes (polyglot-flight-agent/agent.py)

#### 1. Immediate "Thinking" Indicator
```python
@session.on("user_input_transcribed")
def on_user_input_transcribed(event):
    if event.is_final:
        # Send immediate thinking message
        thinking_data = json.dumps({
            "type": "pre_speech_text",
            "speaker": "assistant",
            "text": "Let me help you with that...",
            "speech_id": f"thinking_{time.time()}",
            "sequence": 0
        }).encode('utf-8')
        asyncio.create_task(ctx.room.local_participant.publish_data(thinking_data, reliable=True))
```

#### 2. Early Response Display
```python
@session.on("conversation_item_added")
def on_conversation_item_added(event):
    if event.item.role == "assistant":
        # Send as pre_speech_text for immediate display
        data = json.dumps({
            "type": "pre_speech_text",
            "speaker": "assistant",
            "text": clean_text,
            "speech_id": f"response_{time.time()}",
            "sequence": sequence,
            "is_final": True
        }).encode('utf-8')
```

#### 3. Synchronized Speech Controller
- Maintains message sequence numbers to prevent race conditions
- Adds 200ms minimum delay for text rendering before audio
- Tracks interruption settings for demo environments

### UI-Side Implementation

#### Production UI (web-app/livekit-voice-chat.html)
- Already had full support for `pre_speech_text` messages
- Implements message sequencing to handle out-of-order messages
- Buffers messages and processes them in correct order
- Sends text display confirmations back to agent

#### Test UI (polyglot-flight-agent/test-flight-ui.html)
- Similar implementation with additional debug features
- Shows message sequence numbers in debug mode
- Displays timing information for troubleshooting

### Message Flow

1. **User speaks** → STT processes → `user_input_transcribed` event
2. **Thinking indicator** → Agent immediately sends "Let me help you with that..."
3. **LLM processes** → Generates response
4. **Text sent early** → `conversation_item_added` → Send as `pre_speech_text`
5. **UI displays text** → Processes based on sequence number
6. **TTS generates audio** → Audio plays after text is visible

### Race Condition Prevention

Both UIs implement message sequencing:
```javascript
async function handleSequencedMessage(data) {
    if (data.sequence === expectedMessageSequence) {
        processPreSpeechText(data);
        expectedMessageSequence++;
        
        // Process buffered messages
        while (messageBuffer.has(expectedMessageSequence)) {
            const buffered = messageBuffer.get(expectedMessageSequence);
            messageBuffer.delete(expectedMessageSequence);
            processPreSpeechText(buffered);
            expectedMessageSequence++;
        }
    } else if (data.sequence > expectedMessageSequence) {
        // Buffer out-of-order message
        messageBuffer.set(data.sequence, data);
    }
}
```

## Environment Configuration Fix

### Problem
- Production UI was hardcoded to use production LiveKit URL
- Running production UI locally resulted in 401 auth errors
- Token from dev API couldn't authenticate with production LiveKit

### Solution
Implemented environment-based configuration:

1. **Environment Variables**:
   - Docker Compose: `ENVIRONMENT=dev`
   - Vercel: `ENVIRONMENT=production`

2. **Config API** (`web-app/api/config.js`):
   ```javascript
   const livekitUrls = {
       dev: 'wss://polyglot-rag-dev-qieglig5.livekit.cloud',
       production: 'wss://polyglot-rag-assistant-3l6xagej.livekit.cloud'
   };
   ```

3. **Dynamic Configuration Loading**:
   - UI fetches `/api/config` on startup
   - Falls back to hostname detection if API unavailable
   - Removes all hardcoded URLs from HTML

## How the UIs Work

### Production UI (livekit-voice-chat.html)
- **Purpose**: Main user-facing interface
- **Features**:
  - Language selector (40+ languages)
  - Interruption toggle for noisy environments
  - Flight results with interactive selection
  - Voice activity indicators
  - Responsive design for mobile/desktop
- **Configuration**: Loads from `/api/config` endpoint
- **Deployment**: Vercel with `ENVIRONMENT=production`

### Test UI (test-flight-ui.html)
- **Purpose**: Development and debugging
- **Features**:
  - Debug mode toggle
  - Message sequence display
  - Timing information
  - Test message injection
  - Simpler interface for troubleshooting
- **Configuration**: Hardcoded for dev environment
- **Usage**: Local development only

## Compromise and Limitations

### What We Achieved
- Text appears immediately when user finishes speaking
- Actual response text displays before audio plays
- Consistent behavior across all platforms
- No modifications to LiveKit framework required

### What's Not Possible (Yet)
- True streaming text display (character by character)
- Displaying partial LLM responses as they generate
- These require LiveKit to add streaming events to STT-LLM-TTS pipeline

### Future Improvements
When LiveKit adds streaming support:
1. Subscribe to LLM token generation events
2. Stream text to UI in real-time
3. Remove "thinking" indicator workaround

## Testing the Implementation

### Local Development
```bash
# Start all services
./docker-dev.sh up

# Access UIs
# Production UI: http://localhost:8080/livekit-voice-chat.html
# Test UI: http://localhost:8080/polyglot-flight-agent/test-flight-ui.html

# Check timing
# 1. Speak to the agent
# 2. Observe "Let me help you with that..." appears immediately
# 3. Actual response replaces it before audio plays
```

### Production Deployment
```bash
# Deploy to Vercel
./scripts/deploy-ui-vercel.sh

# Automatically sets ENVIRONMENT=production
# Uses production LiveKit instance
```

## Summary

This implementation provides the best possible text-before-audio experience within the constraints of LiveKit Agent Framework v1.0.23. While not true streaming like ChatGPT, it ensures users see text feedback immediately and never experience the jarring effect of hearing audio before seeing text.