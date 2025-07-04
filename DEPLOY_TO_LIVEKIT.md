# Deploy to LiveKit Cloud - Manual Steps

Since the automated deployment is having issues, here are the manual steps to deploy your agent to LiveKit Cloud:

## 1. First, authenticate with LiveKit Cloud

Open a terminal and run:
```bash
lk cloud auth
```

This will open a browser window for authentication.

## 2. Create the agent

Navigate to the agent directory and create the agent:
```bash
cd livekit-agent
lk agent create .
```

When prompted:
- Agent name: `polyglot-flight-assistant`
- Confirm creation: yes

## 3. Deploy the agent

Once created, deploy it:
```bash
lk agent deploy .
```

## 4. Set up secrets

Update the agent secrets with your API keys:
```bash
lk agent update-secrets \
  OPENAI_API_KEY=your_openai_key \
  AMADEUS_CLIENT_ID=your_amadeus_id \
  AMADEUS_CLIENT_SECRET=your_amadeus_secret \
  API_SERVER_URL=https://your-api-server-url.com
```

## 5. Check deployment status

```bash
lk agent status
lk agent logs --follow
```

## Alternative: Deploy via LiveKit Cloud Dashboard

1. Go to https://cloud.livekit.io
2. Navigate to "Agents" section
3. Click "Create Agent"
4. Upload the agent files
5. Set environment variables
6. Deploy

## Files needed for deployment:

- `agent.py` - Entry point
- `realtime_agent.py` - Main logic
- `requirements.txt` - Dependencies
- `livekit.toml` - Configuration

## Testing

Once deployed, use the web client at `web-app/livekit-client.html` to test the agent.

## Troubleshooting

If you see "project does not match agent subdomain" errors:
1. Make sure you're using the correct project from `lk project list`
2. Try using `--subdomain` flag instead of `--project`
3. Ensure your LIVEKIT_URL matches the project URL