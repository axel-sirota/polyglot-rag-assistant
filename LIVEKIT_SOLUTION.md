# LiveKit Deployment Solution

The "project does not match agent subdomain []" error appears to be a known issue when projects share the same subdomain. Here are the solutions:

## Option 1: Deploy Through LiveKit Cloud Dashboard (Recommended)

Since the CLI is having issues, use the web interface:

1. Go to https://cloud.livekit.io
2. Sign in and select your project: `polyglot-rag-assistant-cloud`
3. Navigate to **Agents** in the left sidebar
4. Click **Deploy New Agent**
5. Upload these files:
   - `agent.py`
   - `realtime_agent.py`
   - `requirements.txt`
   - `livekit.toml`
6. Set environment variables:
   - `OPENAI_API_KEY`
   - `AMADEUS_CLIENT_ID`
   - `AMADEUS_CLIENT_SECRET`
   - `API_SERVER_URL` (set to your deployed API server URL)
7. Click **Deploy**

## Option 2: Run Agent Locally with Cloud Connection

Instead of deploying to LiveKit Cloud, run the agent locally but connected to LiveKit Cloud:

```bash
cd livekit-agent

# Set environment variables
export LIVEKIT_URL=wss://polyglot-rag-assistant-3l6xagej.livekit.cloud
export LIVEKIT_API_KEY=***REMOVED***
export LIVEKIT_API_SECRET=***REMOVED***

# Run the agent
python agent.py start
```

This connects your local agent to LiveKit Cloud rooms.

## Option 3: Create Fresh Project

The issue might be due to conflicting projects. Create a completely new project:

```bash
# Create new project (will generate new subdomain)
lk project create polyglot-agent-prod

# This will give you a new subdomain like:
# wss://polyglot-agent-prod-xxxxxx.livekit.cloud

# Then deploy to this new project
cd livekit-agent
lk agent create --project polyglot-agent-prod .
```

## Option 4: Use Docker Deployment

Create a Dockerfile and deploy as a container:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "agent.py", "start"]
```

Then deploy this container to any cloud provider.

## Why This Is Happening

1. Both your projects (`polyglot-rag-assistant` and `polyglot-rag-assistant-cloud`) point to the same subdomain
2. The CLI can't determine which project owns the agent subdomain
3. The agent subdomain field appears to be empty `[]`

## Recommended Action

Use **Option 1** (LiveKit Dashboard) for the quickest deployment. The web interface handles the complexity and avoids CLI issues.

Once deployed, your agent will:
- Handle voice conversations with interruption support
- Process multiple languages
- Search flights through your API server
- Use LiveKit's infrastructure for scaling

Test with the web client at `web-app/livekit-client.html` after deployment!