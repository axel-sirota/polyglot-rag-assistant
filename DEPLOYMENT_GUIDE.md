# 🚀 Polyglot RAG - Local Testing & Deployment Guide

## 📱 Testing on Phone & Web (Local Development)

### Current Setup
- **Gradio App**: Running on `localhost:7860`
- **Ngrok**: Already running (forwards to port 80)

### Quick Access URLs

1. **Local Computer**:
   ```
   http://localhost:7860
   ```

2. **Phone/Tablet (Same WiFi)**:
   ```bash
   # Find your local IP:
   # Mac: ifconfig | grep "inet " | grep -v 127.0.0.1
   # Then use: http://YOUR_LOCAL_IP:7860
   ```

3. **Public Access (Gradio Share)**:
   - When you run the Gradio app with `share=True`, it creates a public URL
   - Look for: `Running on public URL: https://xxxxx.gradio.live`
   - This URL works from anywhere!

4. **Ngrok (Custom)**:
   ```bash
   # Kill current ngrok (it's pointing to port 80)
   # Then restart pointing to Gradio:
   ngrok http 7860
   
   # Or update your ngrok.yml to use port 7860
   ```

## 🎯 Step-by-Step Testing Guide

### 1. Start Everything Locally

```bash
# Terminal 1: Start Gradio (creates public URL automatically)
.venv/bin/python3 frontend/gradio_app.py

# Terminal 2: Start the orchestrator (optional, Gradio includes it)
.venv/bin/python3 main.py

# Terminal 3: Monitor logs
tail -f logs/*.log
```

### 2. Access from Phone

**Option A: Gradio Share (Easiest)**
- Look for the public URL in terminal: `https://xxxxx.gradio.live`
- Open this URL on your phone
- Works through firewalls, no setup needed!

**Option B: Local Network**
```bash
# Get your computer's IP
ifconfig | grep "inet " | grep -v 127.0.0.1
# Example: 192.168.1.100

# On phone browser:
http://192.168.1.100:7860
```

**Option C: Ngrok**
```bash
# Stop current ngrok (Ctrl+C)
# Restart with correct port:
ngrok http 7860

# Use the ngrok URL on phone:
https://your-subdomain.ngrok-free.app
```

## 🌍 Full Deployment Architecture

### Components & Where They Run:

1. **LiveKit Agent** (Voice Processing)
   - **Where**: LiveKit Cloud
   - **Deploy**: `lk cloud agent deploy`
   - **Purpose**: Handles WebRTC, voice streaming

2. **Main Backend** (Orchestrator + APIs)
   - **Where**: Your server/cloud VM
   - **Options**:
     - Local machine (development)
     - AWS EC2 / Google Cloud VM
     - Docker container
     - Kubernetes cluster

3. **Web Interface**
   - **Gradio** (Development):
     - Auto-creates public URLs
     - Good for demos
   - **Static HTML** (Production):
     - Deploy to: Vercel, Netlify, AWS S3
     - Files in `web-app/`

4. **Mobile App**
   - **Development**: Expo (creates tunnel automatically)
   - **Production**: App stores

## 🔧 Quick Commands

### Start Everything for Demo
```bash
# Simple start (Gradio only)
.venv/bin/python3 frontend/gradio_app.py

# This gives you:
# - Local URL: http://localhost:7860
# - Public URL: https://xxxxx.gradio.live (auto-generated)
```

### Test Voice Features
1. Click microphone in Gradio interface
2. Speak in any language
3. Get response in same language

### Test Flight Search
Type or say:
- "Find flights from NYC to Paris"
- "Buscar vuelos de Madrid a Barcelona"
- "Trouvez des vols de Paris à Londres"

## 🚀 Production Deployment

### Option 1: Simple Cloud VM
```bash
# On AWS/GCP/Azure VM:
git clone <your-repo>
cd polyglot-rag-assistant
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run with systemd or supervisor
python3 frontend/gradio_app.py --server_name 0.0.0.0
```

### Option 2: Docker
```bash
# Build and run
docker build -t polyglot-rag .
docker run -p 7860:7860 --env-file .env polyglot-rag
```

### Option 3: Kubernetes
```bash
kubectl apply -f k8s/deployment.yaml
kubectl expose deployment polyglot-rag --type=LoadBalancer --port=80 --target-port=7860
```

## 📱 Mobile App Testing

### Using Expo (React Native)
```bash
cd mobile-app/react-native
npm install
expo start --tunnel

# This creates a URL like: exp://xxx.xxx.xxx.xxx:19000
# Scan QR code with Expo Go app
```

### Configure Backend URL in App
Edit `mobile-app/react-native/config.ts`:
```typescript
export const API_URL = "https://xxxxx.gradio.live"; // Your Gradio public URL
```

## 🔍 Troubleshooting

### Can't access from phone?
1. Check firewall: `sudo ufw allow 7860`
2. Check same WiFi network
3. Use Gradio share URL instead

### Voice not working?
1. Check microphone permissions in browser
2. Ensure HTTPS (required for mic access)
3. Use Gradio share URL (always HTTPS)

### Ngrok issues?
```bash
# Check ngrok status
curl http://localhost:4040/api/tunnels

# Restart with correct port
pkill ngrok
ngrok http 7860
```

## 🎮 Demo Mode Commands

### Quick Demo Start
```bash
# This starts everything needed for a demo:
./scripts/start-demo.sh
```

### Monitor Everything
```bash
# Terminal 1: Logs
tail -f logs/*.log

# Terminal 2: System status
watch -n 1 'ps aux | grep python'

# Terminal 3: Network connections
netstat -an | grep LISTEN
```

## 📝 Summary

For quick testing:
1. Run: `.venv/bin/python3 frontend/gradio_app.py`
2. Use the public URL it generates
3. Share that URL to test on any device!

For production:
1. Deploy LiveKit agent to cloud
2. Deploy backend to VM/container
3. Use proper domain with HTTPS