# Polyglot RAG Assistant - TODO Tracker

## Overview
Fixing the Polyglot RAG repository to use OpenAI Realtime API with fallback, removing MCP dependencies, and preparing for 2-day App Store deployment.

## Phase 1: Backend Cleanup (4 hours)
- [ ] Remove MCP dependencies and fix imports
  - [ ] Delete mcp_servers/flight_search_server.py
  - [ ] Delete mcp_servers/mcp_config.json
  - [ ] Move mcp_servers/flight_search_api.py to services/flight_search_service.py
  - [ ] Update all imports from mcp to use direct function calling
- [ ] Create OpenAI function definitions
  - [ ] Create services/functions.py with flight search function schema
- [ ] Update environment variables
  - [ ] Remove MCP_SERVER_PORT and related configs from .env

## Phase 2: Voice Pipeline Implementation (4 hours)
- [ ] Create Realtime API client
  - [ ] Create services/realtime_client.py
  - [ ] Implement WebSocket connection to OpenAI Realtime API
- [ ] Implement voice processing with fallback
  - [ ] Create services/voice_processor.py
  - [ ] Add Realtime API processing
  - [ ] Add fallback to standard STT→LLM→TTS pipeline

## Phase 3: Simplified Frontend (4 hours)
- [ ] Create single web interface
  - [ ] Update web-app/index.html
  - [ ] Update web-app/app.js with WebSocket support
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
Starting Phase 1: Backend Cleanup