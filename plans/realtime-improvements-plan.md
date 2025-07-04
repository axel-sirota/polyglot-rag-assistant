# Realtime Voice Assistant Improvement Plan

## Issues Identified

### 1. **Voice Interruption Not Working Properly**
- Assistant continues speaking over user interruptions
- Only stops when audio chunk completes
- Creates audio feedback and confusion
- Chat displays assistant messages before user messages

### 2. **Flight Search Issues**
- **Critical Bug**: `coroutine 'FlightSearchServer._get_mock_flights' was never awaited`
- No real flight data (APIs returning 400/401 errors)
- High latency without user feedback
- Results never arrive due to async error

### 3. **Chat Display Issues**
- Messages appear out of order
- Assistant responses show before user messages
- Auto-scroll working but messages are confusing

### 4. **API Integration Issues**
- AviationStack returning 400 error
- SerpAPI key invalid (401 error)
- Need alternative flight data source

## Root Causes

### 1. Async/Await Error
```python
# Current error in logs:
RuntimeWarning: coroutine 'FlightSearchServer._get_mock_flights' was never awaited
```
The `_get_mock_flights` method was changed to async but is being called without await.

### 2. OpenAI Realtime API Limitations
- Interruption handling is chunk-based, not instant
- Need to implement client-side audio suppression

### 3. API Configuration
- AviationStack endpoint might be wrong
- Need to verify API keys and endpoints

## Implementation Plan

### Phase 1: Fix Critical Bugs (Immediate)

#### 1.1 Fix Async/Await Error
```python
# In flight_search_service.py search_flights method
# Change from:
flights = self._get_mock_flights(...)
# To:
flights = await self._get_mock_flights(...)
```

#### 1.2 Fix Message Ordering
- Add message queue to ensure proper ordering
- Buffer user messages until transcription is complete
- Show typing indicator during processing

### Phase 2: Improve Interruption Handling

#### 2.1 Client-Side Audio Management
```javascript
// Add audio ducking when user speaks
class RealtimeVoiceAssistant {
    constructor() {
        this.assistantAudioLevel = 1.0;
        this.gainNode = null;
        // ...
    }
    
    setupAudioDucking() {
        // Create gain node for assistant audio
        this.gainNode = this.audioContext.createGain();
        // Connect: source -> gainNode -> destination
    }
    
    onUserSpeaking() {
        // Duck assistant audio to 20%
        this.gainNode.gain.setTargetAtTime(0.2, this.audioContext.currentTime, 0.1);
    }
    
    onUserStoppedSpeaking() {
        // Restore assistant audio
        this.gainNode.gain.setTargetAtTime(1.0, this.audioContext.currentTime, 0.1);
    }
}
```

#### 2.2 Server-Side Improvements
- Send interrupt signal immediately when user starts speaking
- Clear audio queue on interruption
- Implement conversation.item.truncate for immediate stop

### Phase 3: Real Flight Data Integration

#### 3.1 Option A: Fix AviationStack Integration
```python
# Correct endpoint for AviationStack
# According to docs: /v1/flights for real-time data
params = {
    "access_key": self.aviationstack_key,
    "dep_iata": origin,
    "arr_iata": destination,
    "flight_date": departure_date,
    "limit": 10,
    "flight_status": "scheduled"  # Add this parameter
}
```

#### 3.2 Option B: Use Browserless.io for Web Scraping
```python
async def search_flights_browserless(self, origin, destination, date):
    """Use Browserless to scrape Google Flights"""
    url = f"https://www.google.com/travel/flights?q={origin}+to+{destination}+{date}"
    
    api_url = f"https://chrome.browserless.io/content?token={self.browserless_key}"
    payload = {
        "url": url,
        "waitForSelector": "[role='list'] [role='listitem']",
        "evaluate": """
        () => {
            const flights = [];
            document.querySelectorAll('[role="listitem"]').forEach(item => {
                const airline = item.querySelector('[dir="auto"]')?.textContent;
                const price = item.querySelector('[role="text"]')?.textContent;
                const time = item.querySelector('[aria-label*="Departure"]')?.textContent;
                if (airline && price) {
                    flights.push({ airline, price, time });
                }
            });
            return flights;
        }
        """
    }
```

### Phase 4: Improve User Experience

#### 4.1 Add Progress Indicators
```javascript
// Show searching status
async handleServerMessage(data) {
    switch (data.type) {
        case 'function_call_started':
            if (data.name === 'search_flights') {
                this.showSearchingIndicator();
            }
            break;
        case 'function_call_completed':
            this.hideSearchingIndicator();
            break;
    }
}
```

#### 4.2 Implement Streaming Results
- Return flights as they're found
- Show partial results immediately
- Update UI progressively

### Phase 5: Alternative Architecture (WebRTC)

Consider moving to WebRTC for better real-time performance:
- Lower latency
- Better interruption handling
- Native browser audio APIs

## Implementation Priority

1. **Immediate** (Fix breaking issues):
   - Fix async/await error in flight search
   - Fix message ordering in chat

2. **High Priority** (Core functionality):
   - Implement proper flight search with real data
   - Add progress indicators

3. **Medium Priority** (UX improvements):
   - Improve interruption handling
   - Add audio ducking

4. **Future** (Architecture):
   - Consider WebRTC migration
   - Implement streaming results

## Testing Plan

1. Test flight search with various routes
2. Test interruption at different points
3. Test with multiple languages
4. Performance testing for latency

## Alternative Solutions

### For Flight Data:
1. Use Amadeus API (free tier available)
2. Use Skyscanner API
3. Build database of common routes
4. Use Browserless for real-time scraping

### For Interruption:
1. Implement WebRTC instead of WebSocket
2. Use client-side VAD with manual control
3. Add push-to-talk mode as fallback

## Next Steps

1. Fix the critical async/await bug
2. Implement proper error handling for APIs
3. Add user feedback for long operations
4. Test with real flight data sources
5. Improve interruption handling progressively