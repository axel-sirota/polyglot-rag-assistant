# LiveKit Agent Dispatch and Job Acceptance Guide

## Overview

This guide documents the findings and solutions for LiveKit agent dispatch issues, specifically for LiveKit Python SDK v1.0.23.

## The Dispatch Problem

When a LiveKit agent registers but never receives job assignments, showing logs like:
```
INFO livekit.agents - registered worker
INFO livekit.agents - received job request
WARNING livekit.agents - no answer was given inside the job_request_fnc, automatically rejecting the job
```

## Root Causes and Solutions

### 1. Room Metadata with agent_name

**Problem**: Setting `agent_name` in room metadata prevents automatic dispatch.

```javascript
// BAD - Prevents automatic dispatch
roomMetadata: JSON.stringify({
  require_agent: true,
  agent_name: 'polyglot-flight-agent'  // This breaks automatic dispatch!
})

// GOOD - Enables automatic dispatch
roomMetadata: JSON.stringify({
  require_agent: true
  // No agent_name specified
})
```

### 2. WorkerOptions Configuration

**Problem**: Setting `agent_name` in WorkerOptions disables automatic dispatch.

```python
# BAD - Requires explicit dispatch API calls
WorkerOptions(
    entrypoint_fnc=entrypoint,
    agent_name="my-agent"  # This disables automatic dispatch
)

# GOOD - Enables automatic dispatch
WorkerOptions(
    entrypoint_fnc=entrypoint
    # No agent_name specified
)
```

### 3. Custom Job Request Handler Issues

**Problem**: Custom `request_fnc` implementations often fail to properly accept jobs.

```python
# PROBLEMATIC - Custom handlers are tricky to implement correctly
async def handle_job_request(request):
    # Various attempts that didn't work:
    return True  # Doesn't work in v1.0.23
    await request.accept()  # May not work as expected
    
WorkerOptions(
    request_fnc=handle_job_request  # Often causes issues
)

# SOLUTION - Remove custom handler entirely
WorkerOptions(
    entrypoint_fnc=entrypoint,
    # No request_fnc - let LiveKit handle it automatically
)
```

## Correct Configuration for Automatic Dispatch

### Agent Configuration (agent.py)

```python
if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            # NO agent_name specified
            # NO request_fnc specified
            port=8082,
            host="0.0.0.0",
            ws_url=os.getenv("LIVEKIT_URL"),
            api_key=os.getenv("LIVEKIT_API_KEY"),
            api_secret=os.getenv("LIVEKIT_API_SECRET"),
            num_idle_processes=1,
            shutdown_process_timeout=30
        )
    )
```

### Token Generation (Backend)

When generating tokens, ensure room metadata doesn't include agent_name:

```python
# Example token generation
token = AccessToken(api_key, api_secret)
token.add_grant(VideoGrant(
    room_join=True,
    room=room_name
))

# Room creation/metadata should NOT include agent_name
room_metadata = {
    "require_agent": True,
    # "agent_name": "xxx"  # DON'T include this!
}
```

## Debugging Tips

### 1. Enable Debug Logging

```bash
python agent.py dev --log-level DEBUG
```

### 2. Check for agent_name in Logs

Look for warnings about agent_name:
```
⚠️  agent_name is set to: 'some-name'
⚠️  This will PREVENT automatic dispatch!
```

Note: `agent_name: ""` (empty string) in job request logs is normal and doesn't prevent dispatch.

### 3. Monitor Job Requests

If you see job requests being received but rejected:
```
INFO livekit.agents - received job request
WARNING livekit.agents - no answer was given inside the job_request_fnc
```

This usually means:
- Your custom `request_fnc` isn't accepting jobs correctly
- Solution: Remove the custom handler

## Common Misconceptions

1. **`close_on_disconnect` parameter**: This doesn't exist in RoomInputOptions for v1.0.23
2. **`namespace` parameter**: Not available in WorkerOptions for v1.0.23
3. **Return True in request_fnc**: Doesn't work reliably in v1.0.23
4. **Empty string agent_name**: The log entry `"agent_name": ""` is normal and doesn't prevent dispatch

## Best Practices

1. **Use automatic dispatch**: Don't set agent_name unless you need explicit dispatch control
2. **Avoid custom request handlers**: Let LiveKit handle job acceptance automatically
3. **Test with minimal configuration**: Start simple and add complexity only when needed
4. **Monitor logs carefully**: Job request logs will show if dispatch is working

## Version-Specific Notes

This guide is specifically for LiveKit Python SDK v1.0.23. Different versions may have different behaviors:
- Later versions might support different parameters
- Job acceptance mechanisms may vary between versions
- Always check the documentation for your specific version

## Summary

For automatic agent dispatch in LiveKit v1.0.23:
1. Don't set `agent_name` anywhere (room metadata or WorkerOptions)
2. Don't use custom `request_fnc` unless absolutely necessary
3. Let LiveKit's default behavior handle job acceptance
4. Monitor logs to ensure jobs are being received and accepted