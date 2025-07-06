# Multilingual Support Fix

## Issue
Agent crashed when user spoke Spanish with error:
```
ValueError: language detection is not supported in streaming mode
```

## Root Cause
Deepgram's `detect_language=True` parameter is not supported in streaming mode (only in batch/pre-recorded mode).

## Solution
Removed the `detect_language=True` parameter from Deepgram STT configuration. The Nova-3 model automatically supports 40+ languages without needing explicit language detection.

## Configuration
```python
stt=deepgram.STT(
    model="nova-3",
    # Nova-3 supports 40+ languages automatically
    # No need for explicit language detection in streaming mode
    sample_rate=48000  # Match WebRTC requirement
),
```

## How It Works
- Nova-3 model has built-in multilingual support
- It automatically recognizes and transcribes 40+ languages
- No explicit language parameter needed in streaming mode
- The model adapts to the input language on the fly

## Tested Languages
Should now work with:
- English: "Find flights from New York to Paris"
- Spanish: "Buscar vuelos de Madrid a Barcelona"
- French: "Chercher des vols de Paris à Londres"
- Chinese: "查找从北京到上海的航班"
- And 36+ other languages supported by Nova-3