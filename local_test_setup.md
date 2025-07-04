# Local Testing & Deployment Guide - Simplified

## 🎯 Quick Start (2 Commands)

```bash
# 1. Install dependencies
.venv/bin/python3 -m pip install -r requirements.txt

# 2. Start the application
.venv/bin/python3 api_server.py
```

That's it! Open http://localhost:8000 in your browser.

## 📁 Project Structure (Simplified)

```
polyglot-rag-assistant/
├── api_server.py           # Main FastAPI backend (START HERE)
├── main.py                 # Alternative entry point
├── requirements.txt        # Only 7 dependencies now!
├── services/              
│   ├── flight_search_service.py  # Flight API integration
│   ├── voice_processor.py        # Voice with Realtime API
│   ├── realtime_client.py        # OpenAI WebSocket client
│   └── functions.py              # OpenAI function definitions
├── web-app/               
│   ├── index.html               # Web interface
│   └── app.js                   # WebSocket voice client
└── mobile-app/            
    └── react-native/            # Mobile app (for later)
```

## 🚀 Step-by-Step Deployment

### Option 1: Web Interface (Recommended)

```bash
# Terminal 1: Start backend
.venv/bin/python3 api_server.py

# Terminal 2: Start web server
cd web-app
python3 -m http.server 3000

# Open browser
# Backend API: http://localhost:8000
# Web Interface: http://localhost:3000
```

### Option 2: API Only (for testing)

```bash
# Start FastAPI with auto-reload
.venv/bin/python3 -m uvicorn api.main:app --reload --port 8000

# Test endpoints:
curl http://localhost:8000/status
curl http://localhost:8000/search_flights -X POST \
  -H "Content-Type: application/json" \
  -d '{"origin": "JFK", "destination": "LAX", "departure_date": "2024-12-25"}'
```

### Option 3: Docker (Production-like)

```bash
# Create simple Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "api_server.py"]
EOF

# Build and run
docker build -t flight-assistant .
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e SERPAPI_API_KEY=$SERPAPI_API_KEY \
  -e AVIATIONSTACK_API_KEY=$AVIATIONSTACK_API_KEY \
  flight-assistant
```

## 🎤 Testing Voice Features

### Browser Requirements
- Chrome/Edge recommended (better WebRTC support)
- Allow microphone permissions when prompted

### Test Flow
1. Open http://localhost:3000
2. Click "Allow" for microphone access
3. Hold "Hold to Talk" button and speak
4. Release to send audio
5. Wait for voice response

### Example Queries
- English: "Find flights from New York to London next week"
- Spanish: "Busca vuelos de Madrid a Barcelona"
- French: "Trouve des vols de Paris à Tokyo"
- Chinese: "查找从北京到上海的航班"

## 🔧 Configuration

### Required API Keys (.env file)
```env
# OpenAI - Required for voice and chat
OPENAI_API_KEY=sk-...

# Flight Search - At least one required
AVIATIONSTACK_API_KEY=...
SERPAPI_API_KEY=...

# Optional
GRADIO_SHARE=false  # Set true for public URL
```

### Voice Settings
Edit `services/voice_processor.py` to change:
- Supported languages (line 35-47)
- Voice models (line 275-290)
- Realtime API settings (line 127-140)

## 📱 Mobile App Deployment (When Ready)

```bash
# Navigate to mobile app
cd mobile-app/react-native

# Install Expo CLI
npm install -g expo-cli

# Install dependencies
npm install

# Start development
expo start

# For iOS App Store
eas build --platform ios --auto-submit
```

## 🐛 Troubleshooting

### "Cannot connect to WebSocket"
- Check backend is running: `curl http://localhost:8000/status`
- Check browser console for errors
- Try different browser (Chrome/Edge)

### "No audio response"
- Check OpenAI API key is valid
- Check browser allowed microphone
- Look at backend logs for errors

### "Flight search returns no results"
- Verify at least one flight API key is set
- Check date format is YYYY-MM-DD
- Try common routes like JFK-LAX

### "Module not found" errors
```bash
# Reinstall dependencies
.venv/bin/python3 -m pip install -r requirements.txt --force-reinstall
```

## 🚢 Production Deployment

### Option 1: Single Server (Simplest)
```bash
# On Ubuntu/Debian server
sudo apt update
sudo apt install python3.11 python3-pip nginx

# Clone and setup
git clone <your-repo>
cd polyglot-rag-assistant
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Run with systemd
sudo nano /etc/systemd/system/flight-assistant.service
# Add service configuration (see below)

# Start service
sudo systemctl enable flight-assistant
sudo systemctl start flight-assistant
```

### Systemd Service File
```ini
[Unit]
Description=Flight Voice Assistant
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/polyglot-rag-assistant
Environment="PATH=/home/ubuntu/polyglot-rag-assistant/.venv/bin"
ExecStart=/home/ubuntu/polyglot-rag-assistant/.venv/bin/python api_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Option 2: Cloud Platform (AWS/GCP/Azure)
1. Use Docker image from Option 3 above
2. Deploy to:
   - AWS: ECS Fargate or App Runner
   - GCP: Cloud Run
   - Azure: Container Instances
3. Set environment variables in platform
4. Use platform's SSL/domain features

### Option 3: Vercel/Railway (Easiest)
```bash
# Install Railway CLI
npm install -g @railway/cli

# Deploy
railway login
railway init
railway up

# Set environment variables in Railway dashboard
```

## 📊 Monitoring

### Basic Health Check
```python
# Add to api_server.py
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }
```

### Logging
- All logs go to stdout by default
- In production, pipe to file: `python api_server.py >> app.log 2>&1`
- Or use logging service (CloudWatch, Stackdriver, etc.)

## 🎯 Performance Tips

1. **Enable caching** in flight service (already implemented)
2. **Use CDN** for web-app files in production
3. **Set up Redis** for session management (optional)
4. **Use nginx** as reverse proxy for better performance

## 💡 Next Steps

1. **Test locally** with the 2-command quick start
2. **Deploy to cloud** when ready for production
3. **Add monitoring** for production use
4. **Build mobile app** for App Store submission

## 🆘 Need Help?

1. Check the logs: Backend prints detailed errors
2. Test API directly: Use `/docs` endpoint for Swagger UI
3. Verify environment: All API keys must be valid
4. Simple is better: Start with basic deployment first

Remember: This is built for a demo, so focus on getting it working rather than perfect production setup!