# How to Trigger the LiveKit Agent

The LiveKit agent is running and registered but needs to be triggered to join a room. Here are the ways to do it:

## Method 1: Browser/Client Metadata (Recommended)

When connecting from your test client, include metadata to trigger the agent:

```javascript
// In your browser connection code
const room = new Room();
await room.connect(url, token, {
  // Add this metadata to trigger agent
  metadata: JSON.stringify({ 
    request_agent: true,
    agent_name: "polyglot-flight-agent"
  })
});
```

## Method 2: Room Name Pattern

Some agents are configured to auto-join rooms with specific name patterns:
- Try room names like: `agent-test`, `demo-agent`, `flight-agent`

## Method 3: Manual Agent Assignment

If you have access to LiveKit Cloud dashboard:
1. Go to your project dashboard
2. Navigate to Agents section
3. Manually assign the agent to your room

## Method 4: Check Agent Logs

The agent logs should show if it's receiving job requests:
- Look for: "Job received" or "Connecting to room"
- If no jobs are received, the trigger mechanism isn't working

## Debugging Tips

1. **Check agent registration**:
   - Agent logs should show: "registered worker"
   - Note the worker ID (e.g., "AW_NYjThAiDNfJN")

2. **Verify room exists**:
   - The room must exist before agent can join
   - Agent won't create rooms

3. **Check participant count**:
   - Agents typically join when human participants are present
   - Empty rooms might not trigger agents

## Current Status

- ✅ Agent is running and registered
- ✅ Connected to LiveKit Cloud
- ❓ Waiting for job trigger
- ❓ No agent in room yet

The most likely issue is that the agent needs specific metadata or room configuration to be triggered.