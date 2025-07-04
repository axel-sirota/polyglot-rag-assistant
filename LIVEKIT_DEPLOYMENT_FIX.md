# LiveKit Deployment Fix

The "project does not match agent subdomain []" error indicates a configuration mismatch. Here are several solutions:

## Solution 1: Use Environment Variables

```bash
export LIVEKIT_URL=wss://polyglot-rag-assistant-3l6xagej.livekit.cloud
export LIVEKIT_API_KEY=***REMOVED***  
export LIVEKIT_API_SECRET=***REMOVED***

cd livekit-agent
lk agent create .
```

## Solution 2: Direct API Deployment

Since both your projects point to the same subdomain, you might need to:

1. Delete one of the duplicate projects:
```bash
lk project delete polyglot-rag-assistant
```

2. Then try creating the agent:
```bash
cd livekit-agent
lk agent create --project polyglot-rag-assistant-cloud .
```

## Solution 3: Use LiveKit Cloud Dashboard

1. Go to https://cloud.livekit.io
2. Navigate to your project
3. Go to "Agents" section
4. Click "Deploy Agent"
5. Upload your agent directory as a ZIP file

## Solution 4: Create New Project

If the subdomain conflict persists:

```bash
# Create a new project with unique subdomain
lk project create polyglot-flight-agent

# Then deploy to the new project
cd livekit-agent
lk agent create --project polyglot-flight-agent .
```

## Solution 5: Direct Python Deployment

You can also run the agent directly connected to LiveKit Cloud:

```bash
cd livekit-agent
python agent.py dev
```

This will connect to LiveKit Cloud using your credentials from the .env file.

## What's Happening

The error suggests that:
1. You have two projects with the same subdomain
2. The CLI can't determine which project to deploy to
3. The agent subdomain field is empty []

## Recommended Fix

1. First, clean up duplicate projects
2. Ensure you're using the correct project
3. Try deployment again

If all else fails, the LiveKit Cloud dashboard deployment is the most reliable method.