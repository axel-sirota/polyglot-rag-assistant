# Polyglot RAG Assistant - TODO Tracker

## Overview
Fixing the LiveKit Agent audio issue and preparing for production deployment.

## CRITICAL - Audio Fix Implementation (Sample Rate Mismatch)

### Root Cause Identified
- TTS outputs at 24kHz, WebRTC requires 48kHz
- LiveKit Cloud enforces strict sample rate requirements
- See `AUDIO_FIX_IMPLEMENTATION_PLAN.md` for full details

### Audio Fix Tasks
- [ ] Install scipy for audio resampling: `pip install scipy`
- [ ] Create `polyglot-flight-agent/audio_utils.py` with resampling functions
- [ ] Update VAD configuration to 48kHz (currently 16kHz)
- [ ] Create ResamplingAudioOutput class
- [ ] Update AudioSource to 48kHz: `rtc.AudioSource(48000, 1)`
- [ ] Add proper TrackPublishOptions with SOURCE_MICROPHONE
- [ ] Implement test tone generator for verification
- [ ] Add comprehensive audio pipeline logging
- [ ] Test with both test tone and actual TTS
- [ ] Verify audio is audible in browser

### Testing Sequence
1. [ ] Test manual 440Hz tone at 48kHz
2. [ ] Verify tone is audible
3. [ ] Test TTS with resampling
4. [ ] Monitor WebRTC stats for audio levels
5. [ ] Confirm consistent audio output

## Previous Work Completed

### Phase 1: Backend Cleanup (4 hours)
- [x] Remove MCP dependencies and fix imports
  - [x] Delete mcp_servers/flight_search_server.py
  - [x] Delete mcp_servers/mcp_config.json
  - [x] Move mcp_servers/flight_search_api.py to services/flight_search_service.py
  - [x] Update all imports from mcp to use direct function calling
- [x] Create OpenAI function definitions
  - [x] Create services/functions.py with flight search function schema
- [x] Update environment variables
  - [x] Remove MCP_SERVER_PORT and related configs from .env

## Phase 2: Voice Pipeline Implementation (4 hours)
- [x] Create Realtime API client
  - [x] Create services/realtime_client.py
  - [x] Implement WebSocket connection to OpenAI Realtime API
- [x] Implement voice processing with fallback
  - [x] Create services/voice_processor.py
  - [x] Add Realtime API processing
  - [x] Add fallback to standard STT→LLM→TTS pipeline

## Phase 3: Simplified Frontend (4 hours)
- [x] Create single web interface
  - [x] Update web-app/index.html
  - [x] Update web-app/app.js with WebSocket support
  - [x] Create FastAPI backend with WebSocket support in api/main.py
  - [ ] Remove Gradio dependency for production

## Phase 4: Mobile App with Expo (8 hours)
- [ ] Initialize Expo project
  - [ ] Create new Expo app with TypeScript template
  - [ ] Configure audio permissions
- [ ] Configure for App Store
  - [ ] Update app.json with proper metadata
  - [ ] Configure EAS build settings
- [ ] Build and submit
  - [ ] Install EAS CLI
  - [ ] Build for iOS
  - [ ] Submit to App Store

## Phase 5: Integration & Testing (4 hours)
- [ ] Create unified API endpoint
  - [ ] Create FastAPI app with WebSocket support
  - [ ] Integrate voice pipeline and flight service
- [ ] Test multilingual support
  - [ ] Test with multiple languages
  - [ ] Verify function calling works correctly

## Current Status
Completed Phases 1-3, simplified dependencies. Ready for mobile app development and production deployment.

## LiveKit Agent Work

### Completed
- ✅ Implemented LiveKit Agent with STT-LLM-TTS pipeline
- ✅ Integrated flight search API functionality
- ✅ Added multilingual support
- ✅ Downgraded to LiveKit 1.0.23 (didn't fix audio)
- ✅ Identified root cause: Sample rate mismatch (24kHz vs 48kHz)
- ✅ Created comprehensive debugging documentation

### Audio Issues Discovered
- ❌ No audio output despite successful track publishing
- ❌ Audio track exists but is silent/empty
- ❌ Issue persists in both LiveKit 1.1.5 and 1.0.23
- ✅ Root cause: TTS outputs 24kHz, WebRTC requires 48kHz
- ✅ Solution ready: Audio resampling implementation

## Summary of Current State
- LiveKit agent connects and publishes audio track
- Browser subscribes to audio track successfully
- But audio is silent due to sample rate mismatch
- Implementation plan ready in `AUDIO_FIX_IMPLEMENTATION_PLAN.md`
- Once audio fix is applied, agent will be fully functional

## Next Steps Priority
1. **Fix audio output** - Implement resampling solution
2. **Test thoroughly** - Verify audio works consistently
3. **Deploy to production** - LiveKit Cloud deployment
4. **Mobile app** - If needed for demo