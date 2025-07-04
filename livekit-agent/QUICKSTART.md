# LiveKit Agent Quick Start

## 1. First Time Setup

### Authenticate with LiveKit Cloud
```bash
lk cloud auth
```
This will open a browser to authenticate your LiveKit account.

### List your projects
```bash
lk project list
```

## 2. Deploy the Agent

### Option A: Using the directory (recommended)
```bash
cd livekit-agent

# Deploy from current directory
lk agent deploy --project your-project-name .
```

### Option B: Manual deployment
```bash
cd livekit-agent

# 1. Install dependencies
pip install -r requirements.txt

# 2. Run locally first to test
python realtime_agent.py dev

# 3. Deploy to cloud
lk agent deploy \
    --project your-project-name \
    --secrets-file ../.env \
    .
```

## 3. Common Issues

### "flag provided but not defined: -name"
The correct syntax is `lk agent deploy` not `lk cloud agent deploy`

### "project not found"
1. Run `lk cloud auth` first
2. Use `lk project list` to see available projects
3. Use `--project your-project-name` in deploy command

### Missing credentials
Add to your `.env`:
```
LIVEKIT_API_KEY=your_key
LIVEKIT_API_SECRET=your_secret
LIVEKIT_PROJECT=your-project-name
```

## 4. Testing

1. Check agent status:
```bash
lk agent list --project your-project-name
```

2. View logs:
```bash
lk logs --project your-project-name --follow
```

3. Open the web client and test!