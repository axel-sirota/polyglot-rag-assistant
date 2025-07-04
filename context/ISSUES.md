# Current Issues - Polyglot RAG Assistant

## Last Updated: July 4, 2025

## 1. Voice Interruption Limitations ⚠️

### Issue
When user interrupts the assistant while speaking, the OpenAI Realtime API continues sending audio chunks from the previous response. Even though we clear the audio queue and stop playback, the API keeps streaming the remaining audio.

### Current Mitigations
- Client-side audio ducking (reduces volume to 20% when user speaks)
- Audio queue clearing on interruption
- Response ID tracking to discard interrupted audio
- Skip playback of audio from interrupted responses
- Send interrupt signal to server (though API doesn't immediately stop)

### Root Cause
OpenAI Realtime API limitation - can only stop at audio chunk boundaries, not instantly. The `conversation.item.truncate` API returns "item_id not found" errors.

### Potential Solutions
1. Implement WebRTC connection instead of WebSocket for better control
2. Use client-side VAD with manual audio control
3. Add push-to-talk mode as fallback option

## 2. API Key Issues 🔑

### Issue
Both flight search APIs return authentication errors despite user providing keys:
- AviationStack: 403 Forbidden errors
- SerpAPI: 401 Invalid API key errors

### Current State
System falls back to mock flight data with realistic routes and prices.

### Potential Issues
1. API keys might be expired or have wrong permissions
2. AviationStack endpoint might be incorrect (tried /flights, /flightsFuture, /routes)
3. SerpAPI key format might be wrong

### Alternative Solutions
- Use Browserless.io for web scraping (key provided: `***REMOVED***`)
- Try Amadeus API (has free tier)
- Use Skyscanner API

## 3. Message Ordering in Chat 💬

### Issue
Sometimes assistant messages appear before user messages in the chat display, creating confusion about the conversation flow.

### Root Cause
Asynchronous message handling - assistant starts responding before user transcript is finalized.

### Proposed Solution
Implement message queue with proper ordering:
1. Buffer user messages until transcription is complete
2. Show typing indicator during processing
3. Ensure user message appears before assistant response

## 4. High Latency Without Feedback ⏱️

### Issue
During flight searches, there's no user feedback while the API is being called, creating perception of unresponsiveness.

### Proposed Solutions
1. Add "Searching for flights..." message immediately
2. Show progress indicator
3. Stream partial results as they arrive
4. Add timeout with graceful fallback

## 5. Audio Worklet Deprecation Warning ⚠️

### Issue
Browser console shows: "The ScriptProcessorNode is deprecated. Use AudioWorkletNode instead."

### Impact
Currently works fine but may break in future browser versions.

### Solution
Migrate audio processing to use AudioWorkletNode API for better performance and future compatibility.

## 6. Language Detection Locale Issue 🌍

### Issue
System sometimes defaults to Spanish, possibly due to browser locale or cache.

### Current State
Fixed by removing `"language": null` from configuration and using Whisper auto-detection.

### Status
✅ Resolved - but monitor for regression

## 7. Incomplete Error Handling 🚨

### Issue
Some API errors cause silent failures without user feedback.

### Examples
- Flight search API failures show in logs but not to user
- WebSocket disconnections don't always show clear error messages

### Solution
Add comprehensive error handling with user-friendly messages for all failure modes.

## Known Working Features ✅

1. **Multi-language support** - Auto-detects and responds in 12 languages
2. **Voice streaming** - Continuous bidirectional audio works well
3. **Real-time transcription** - Shows user speech as they talk
4. **Audio playback** - Assistant voice responses work correctly
5. **UI layout** - Responsive design with chat on right, controls on left
6. **Mock flight data** - Realistic fallback data for common routes

## Testing Scenarios That Fail ❌

1. **Rapid interruptions** - Multiple interruptions in quick succession
2. **Mid-word interruption** - Interrupting in the middle of a word
3. **Long responses** - Assistant continues for many chunks after interruption
4. **Real flight data** - API authentication issues

## Recommended Testing Flow 🧪

1. Start with simple query: "Find flights from New York to Paris"
2. Let assistant complete response
3. Try interrupting with "Actually, I want business class"
4. Test language: "Buscar vuelos de Madrid a Barcelona"
5. Test interruption during Spanish response
6. Check if audio stops properly after interruption