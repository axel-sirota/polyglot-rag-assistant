# Polyglot RAG Assistant - TODO Tracker

## Overview
Fixing the Polyglot RAG repository to use OpenAI Realtime API with fallback, removing MCP dependencies, and preparing for 2-day App Store deployment.

## Phase 1: Backend Cleanup (4 hours)
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
Starting Phase 1: Backend Cleanup