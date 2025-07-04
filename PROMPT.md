Claude Prompt: Fix Polyglot RAG Repository for OpenAI Realtime Voice Assistant

# Context

Read the plan in context/new_plan.md and Claude.md and Claude.local.md and TODOS.md for context

Context & Current State
I have a multilingual voice assistant project called "polyglot-rag-assistant" that's partially working but needs major fixes. The goal is to create a slick voice interface that uses OpenAI's Realtime API (with fallback to standard STT→LLM→TTS) to search for flights in real-time using function calling. Users speak in any language, and the assistant responds in the same language with flight data.
Current Issues:
1. MCP (Model Context Protocol) imports are failing - package not available via pip
2. Complex LiveKit setup that's overengineered for our needs
3. Multiple disconnected frontends (Gradio, web-app, mobile-app)
4. Flight APIs not properly integrated with function calling
5. No OpenAI Realtime API implementation
6. Need to deploy to App Store in 2 days
Required Architecture Changes
1. Replace MCP with OpenAI Function Calling
Remove all MCP dependencies and replace with native OpenAI function calling:
* Delete mcp_servers/flight_search_server.py
* Keep mcp_servers/flight_search_api.py but rename to services/flight_search_service.py
* Update all imports from mcp to use direct function calling
2. Implement OpenAI Realtime API with Fallback
Create a new voice pipeline that prioritizes Realtime API but falls back to standard pipeline:
File: services/voice_pipeline.py
import os
import json
import asyncio
from typing import AsyncGenerator, Optional
import websockets
import openai
from openai import OpenAI

class VoicePipeline:
    def __init__(self):
        self.client = OpenAI()
        self.realtime_available = self._check_realtime_access()
        
    def _check_realtime_access(self) -> bool:
        """Check if account has Realtime API access"""
        try:
            # Try to establish connection to Realtime endpoint
            # This will fail if no access
            return True
        except:
            print("Realtime API not available, using standard pipeline")
            return False
    
    async def process_voice_realtime(self, audio_stream: bytes, language: str = 'en') -> AsyncGenerator[str, None]:
        """Process voice using Realtime API with function calling"""
        # Implementation from the research artifact
        
    async def process_voice_standard(self, audio_data: bytes, language: str = 'en') -> tuple[str, bytes]:
        """Fallback to standard STT→LLM→TTS pipeline"""
        # 1. Whisper transcription
        # 2. GPT-4 with function calling
        # 3. TTS generation
3. Simplify Flight Search Service
Consolidate flight search into a single service with AviationStack primary and SerpAPI fallback:
File: services/flight_service.py
from typing import List, Dict, Optional
import httpx
from datetime import datetime

class FlightService:
    def __init__(self, aviation_key: str, serp_key: str):
        self.aviation_key = aviation_key
        self.serp_key = serp_key
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        passengers: int = 1,
        cabin_class: str = 'economy'
    ) -> List[Dict]:
        """Search flights with automatic fallback"""
        # Try AviationStack first
        # Fall back to SerpAPI if failed
        # Return standardized format
4. Create Unified React Native App with Expo
Replace the current mobile app structure with a clean Expo setup:
File: mobile/App.tsx
import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, FlatList, StyleSheet } from 'react-native';
import { Audio } from 'expo-av';
import * as Speech from 'expo-speech';

export default function App() {
  // Clean implementation focused on voice interaction
  // Reuse web components where possible
}
5. Streamline Web Interface
Create a single, clean web interface that works on both desktop and mobile:
File: web/index.html
<!DOCTYPE html>
<html>
<head>
    <title>Flight Voice Assistant</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body>
    <!-- Clean, responsive design -->
    <!-- WebSocket connection for real-time voice -->
</body>
</html>
Step-by-Step Implementation Instructions
Phase 1: Backend Cleanup (4 hours)
1. Remove MCP and fix imports: # Delete MCP-related files
2. rm mcp_servers/flight_search_server.py
3. rm mcp_servers/mcp_config.json
4. 
5. # Update main.py to remove MCP references
6. # Replace with direct function calling
7. 
8. Create OpenAI function definitions: # In services/functions.py
9. FLIGHT_SEARCH_FUNCTION = {
10.     "type": "function",
11.     "function": {
12.         "name": "search_flights",
13.         "description": "Search for flights between airports",
14.         "parameters": {
15.             "type": "object",
16.             "properties": {
17.                 "origin": {"type": "string", "description": "Origin airport IATA code"},
18.                 "destination": {"type": "string", "description": "Destination airport IATA code"},
19.                 "departure_date": {"type": "string", "description": "YYYY-MM-DD format"},
20.                 "return_date": {"type": "string", "description": "Optional return date"},
21.                 "passengers": {"type": "integer", "minimum": 1, "maximum": 9},
22.                 "cabin_class": {"type": "string", "enum": ["economy", "premium", "business", "first"]}
23.             },
24.             "required": ["origin", "destination", "departure_date"]
25.         }
26.     }
27. }
28. 
29. Update environment variables: # In .env
30. OPENAI_API_KEY=your_key
31. AVIATION_STACK_KEY=your_key
32. SERP_API_KEY=your_key
33. # Remove MCP_SERVER_PORT and related configs
34. 
Phase 2: Voice Pipeline Implementation (4 hours)
1. Create Realtime API client: # In services/realtime_client.py
2. class RealtimeClient:
3.     def __init__(self, api_key: str):
4.         self.api_key = api_key
5.         self.ws_url = "wss://api.openai.com/v1/realtime"
6.         self.session_config = {
7.             "modalities": ["text", "audio"],
8.             "voice": "alloy",
9.             "turn_detection": {"type": "server_vad"},
10.             "tools": [FLIGHT_SEARCH_FUNCTION]
11.         }
12. 
13. Implement voice processing: # In services/voice_processor.py
14. async def process_voice_input(audio_data: bytes, language: str = 'auto'):
15.     if realtime_available:
16.         async for response in realtime_process(audio_data, language):
17.             yield response
18.     else:
19.         text, audio = await standard_process(audio_data, language)
20.         yield {"text": text, "audio": audio}
21. 
Phase 3: Simplified Frontend (4 hours)
1. Create single web interface: // In web/app.js
2. class VoiceAssistant {
3.     constructor() {
4.         this.mediaRecorder = null;
5.         this.socket = null;
6.         this.isRecording = false;
7.     }
8.     
9.     async init() {
10.         // Initialize WebSocket for real-time communication
11.         this.socket = new WebSocket('ws://localhost:8000/ws');
12.         // Setup UI handlers
13.     }
14.     
15.     async startRecording() {
16.         const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
17.         this.mediaRecorder = new MediaRecorder(stream);
18.         // Send audio chunks via WebSocket
19.     }
20. }
21. 
22. Remove Gradio dependency for production:
    * Keep gradio_demo.py for testing only
    * Create FastAPI WebSocket endpoint for production
Phase 4: Mobile App with Expo (8 hours)
1. Initialize Expo project: cd mobile
2. npx create-expo-app flight-assistant --template blank-typescript
3. cd flight-assistant
4. npx expo install expo-av expo-speech expo-haptics
5. 
6. Configure for App Store: // In app.json
7. {
8.   "expo": {
9.     "name": "Flight Voice Assistant",
10.     "slug": "flight-voice-assistant",
11.     "version": "1.0.0",
12.     "orientation": "portrait",
13.     "icon": "./assets/icon.png",
14.     "splash": {
15.       "image": "./assets/splash.png",
16.       "resizeMode": "contain",
17.       "backgroundColor": "#ffffff"
18.     },
19.     "ios": {
20.       "supportsTablet": true,
21.       "bundleIdentifier": "com.yourcompany.flightassistant",
22.       "infoPlist": {
23.         "NSMicrophoneUsageDescription": "This app needs access to microphone for voice commands"
24.       }
25.     },
26.     "plugins": [
27.       [
28.         "expo-av",
29.         {
30.           "microphonePermission": "Allow $(PRODUCT_NAME) to access your microphone for voice search."
31.         }
32.       ]
33.     ]
34.   }
35. }
36. 
37. Build and submit: # Install EAS CLI
38. npm install -g eas-cli
39. eas login
40. 
41. # Configure
42. eas build:configure
43. 
44. # Build for iOS
45. eas build --platform ios --auto-submit
46. 
Phase 5: Integration & Testing (4 hours)
1. Create unified API endpoint: # In api/main.py
2. from fastapi import FastAPI, WebSocket
3. from services.voice_pipeline import VoicePipeline
4. from services.flight_service import FlightService
5. 
6. app = FastAPI()
7. voice_pipeline = VoicePipeline()
8. flight_service = FlightService()
9. 
10. @app.websocket("/ws")
11. async def websocket_endpoint(websocket: WebSocket):
12.     await websocket.accept()
13.     # Handle real-time voice streaming
14. 
15. Test multilingual support: # In tests/test_languages.py
16. test_phrases = {
17.     "en": "Find flights from New York to London",
18.     "es": "Buscar vuelos de Madrid a Barcelona",
19.     "fr": "Trouver des vols de Paris à Tokyo",
20.     "de": "Flüge von Berlin nach München finden",
21.     "zh": "查找从北京到上海的航班"
22. }
23. 
File Structure After Refactoring
polyglot-rag-assistant/
├── services/
│   ├── __init__.py
│   ├── voice_pipeline.py      # OpenAI Realtime + fallback
│   ├── flight_service.py      # AviationStack + SerpAPI
│   ├── functions.py           # OpenAI function definitions
│   └── realtime_client.py     # WebSocket client for Realtime API
├── api/
│   ├── __init__.py
│   └── main.py               # FastAPI with WebSocket support
├── web/
│   ├── index.html           # Single page app
│   ├── app.js              # Voice interaction logic
│   └── styles.css          # Tailwind or minimal CSS
├── mobile/
│   ├── App.tsx             # Main React Native component
│   ├── app.json           # Expo configuration
│   └── eas.json           # EAS Build configuration
├── tests/
│   ├── test_voice.py
│   ├── test_flights.py
│   └── test_languages.py
├── scripts/
│   ├── build_mobile.sh    # EAS build script
│   └── deploy.sh         # Deployment script
├── .env.example
├── requirements.txt      # Simplified dependencies
└── README.md            # Updated documentation
Critical Implementation Details
1. Remove these files entirely:
    * All MCP-related files
    * Complex LiveKit agent files (keep only if specifically needed)
    * Multiple frontend implementations (consolidate to one)
2. Simplify dependencies in requirements.txt: openai>=1.0.0
3. fastapi>=0.104.0
4. websockets>=12.0
5. httpx>=0.25.0
6. python-dotenv>=1.0.0
7. uvicorn>=0.24.0
8. # Remove: mcp, livekit (unless needed), gradio (dev only)
9. 
10. Environment variables needed: OPENAI_API_KEY=sk-...
11. AVIATION_STACK_KEY=...
12. SERP_API_KEY=...
13. 
14. Test commands sequence: # Backend
15. uvicorn api.main:app --reload --port 8000
16. 
17. # Web
18. python -m http.server 3000 --directory web
19. 
20. # Mobile
21. cd mobile && npx expo start
22. 
Expected Outcome
After implementing these changes:
1. Clean, working voice assistant using OpenAI Realtime API (with fallback)
2. Proper flight search with function calling (no MCP)
3. Single web interface that works everywhere
4. React Native app ready for App Store submission
5. All code simplified and focused on core functionality
The entire refactoring should take approximately 16-20 hours, fitting within your 2-day timeline.
