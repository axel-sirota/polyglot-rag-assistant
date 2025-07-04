# Research Verification Prompt for Claude Desktop

## Context and Background

We've been building a **Polyglot Flight Search Assistant** that uses:
1. **OpenAI Realtime API** for voice processing
2. **Amadeus API** for flight searches
3. **LiveKit Cloud** for WebRTC infrastructure and voice interruption handling

The system was working with a custom WebSocket implementation but had critical voice interruption issues. We migrated to LiveKit Cloud to solve these issues.

## Architecture Overview

```
User Browser → WebRTC → LiveKit Cloud → LiveKit Agent → API Server → Amadeus API
```

### Key Components:

1. **API Server** (`api_server.py`):
   - FastAPI server running on port 8000
   - Provides `/api/flights` endpoint for flight searches
   - Uses `FlightSearchService` which integrates with Amadeus SDK
   - Also provides `/api/livekit/token` for LiveKit authentication

2. **Amadeus Integration** (`services/amadeus_sdk_flight_search.py`):
   - Uses official Amadeus Python SDK (v12.0.0)
   - Authenticates with production credentials
   - Searches real flights with pricing
   - Falls back to other APIs if needed

3. **LiveKit Agent** (`livekit-agent/realtime_agent.py`):
   - Uses LiveKit Agents SDK with OpenAI Realtime API
   - Handles voice in 90+ languages
   - Calls our API server for flight searches
   - Implements proper voice interruption handling

4. **Web Client** (`web-app/livekit-client.html`):
   - Connects to LiveKit Cloud via WebRTC
   - Uses LiveKit JavaScript SDK
   - Handles audio capture and playback

## What We Built vs What Got Lost

### What We Built (Critical Components):

1. **Amadeus Flight Search Service**:
   ```python
   # services/amadeus_sdk_flight_search.py
   class AmadeusSDKFlightSearch:
       def __init__(self):
           self.amadeus = Client(
               client_id=AMADEUS_CLIENT_ID,
               client_secret=AMADEUS_CLIENT_SECRET,
               hostname='production'  # Using production API
           )
   ```

2. **API Endpoint for LiveKit Agent**:
   ```python
   # api_server.py
   @app.get("/api/flights")
   async def api_search_flights(
       origin: str,
       destination: str,
       departure_date: str,
       ...
   ):
       flights = await flight_service.search_flights(...)
       return {"flights": flights}
   ```

3. **LiveKit Agent Flight Search Integration**:
   ```python
   # livekit-agent/realtime_agent.py
   async def search_flights(self, origin, destination, departure_date):
       async with aiohttp.ClientSession() as session:
           async with session.get(f"{self.base_url}/api/flights", params=params) as response:
               # Returns real Amadeus flight data
   ```

### What Got Simplified/Lost in Migration:

1. **Direct Amadeus calls in agent** - The agent now calls our API server instead
2. **Complex WebSocket handling** - LiveKit handles this now
3. **Custom interruption logic** - LiveKit provides native interruption support

## Critical Questions to Research

### 1. LiveKit Deployment Issues

**Research**: Why is `lk agent create` failing with "project does not match agent subdomain []"?

**Specific Error**:
```bash
➜ lk agent create .
Using project [polyglot-rag-assistant-cloud]
project does not match agent subdomain []
```

**What to investigate**:
- Is this a known LiveKit CLI issue?
- Does LiveKit require unique subdomains per project?
- What's the correct way to deploy agents in 2024/2025?
- Are there breaking changes in LiveKit CLI v2.4.12?

### 2. Architecture Validation

**Verify this architecture is correct**:
```
Browser → LiveKit Room SDK → LiveKit Cloud → Agent → FastAPI → Amadeus
```

**Questions**:
- Does LiveKit Agent properly support calling external HTTP APIs?
- Is the token generation endpoint correctly implemented?
- Should the agent include Amadeus SDK directly or use our API?

### 3. Code Accuracy Check

**Verify these implementations**:

a) **Token Generation** (`api_server.py`):
```python
@app.post("/api/livekit/token")
async def get_livekit_token(request: Request):
    token = jwt.encode(token_data, api_secret, algorithm="HS256")
```
Is this the correct way to generate LiveKit tokens?

b) **Agent Entry Point** (`livekit-agent/agent.py`):
```python
if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
```
Is this the correct way to start a LiveKit agent?

c) **Realtime Model Configuration**:
```python
llm=openai.LLM.with_realtime(
    model="gpt-4o-realtime-preview-2024-12-17",
    turn_detection=openai.realtime.ServerVadOptions(...)
)
```
Is this the correct API for OpenAI Realtime in LiveKit?

### 4. Deployment Methods

**Research all possible deployment methods**:
1. CLI deployment (`lk agent create/deploy`)
2. Dashboard deployment
3. Docker deployment
4. Direct Python execution

**Which method actually works in 2025?**

### 5. Missing Components

**Check if we need**:
- A specific `package.json` for LiveKit agents?
- A `Procfile` or similar?
- Specific directory structure?
- Agent manifest file?

## Specific Files to Examine

1. **`/livekit-agent/realtime_agent.py`** - Main agent logic
2. **`/livekit-agent/requirements.txt`** - Dependencies (includes Amadeus!)
3. **`/livekit-agent/livekit.toml`** - Configuration
4. **`/api_server.py`** - API server with flight endpoint
5. **`/services/amadeus_sdk_flight_search.py`** - Amadeus integration
6. **`/.env`** - All credentials

## Key Integration Points to Verify

1. **Amadeus is still used**:
   - Agent calls → API Server → FlightSearchService → AmadeusSDKFlightSearch
   - The agent doesn't bypass Amadeus, it uses it through our API

2. **Voice processing flow**:
   - User speaks → LiveKit → Agent → OpenAI Realtime API → Response
   - Interruptions handled by LiveKit natively

3. **Credentials flow**:
   - LiveKit credentials for room/agent
   - OpenAI API key for Realtime API
   - Amadeus credentials for flight search

## Testing Checklist

1. **Does the API server start?**
   ```bash
   python api_server.py
   ```

2. **Can you search flights directly?**
   ```bash
   curl http://localhost:8000/api/flights?origin=JFK&destination=LAX&departure_date=2025-07-10
   ```

3. **Does the agent run locally?**
   ```bash
   cd livekit-agent
   python agent.py dev
   ```

4. **Can you generate LiveKit tokens?**
   ```bash
   curl -X POST http://localhost:8000/api/livekit/token -d '{"identity":"test-user"}'
   ```

## Summary of What to Research

1. **LiveKit CLI deployment issues** - Why the subdomain error?
2. **Correct LiveKit Agents setup** for 2024/2025
3. **Verify all integration points** work as designed
4. **Confirm Amadeus is properly integrated** (not bypassed)
5. **Find the actual working deployment method**

The core question: **Is this architecture correct and why won't it deploy to LiveKit Cloud?**

All the code is in the repo - the Amadeus integration is intact, just accessed through our API server rather than directly from the agent.