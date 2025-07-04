# Local Testing Instructions - Polyglot RAG Voice Assistant

## 🟢 Current Status
Both servers are running:
- API Server: http://localhost:8000 ✅
- Web Server: http://localhost:3000 ✅

## 🎤 Test the Voice Interface

1. **Open the Web Interface**
   ```
   http://localhost:3000/realtime.html
   ```

2. **Start Voice Interaction**
   - Click the green "Start Listening" button
   - Allow microphone access when prompted
   - You should see "Listening... (Speak naturally, no need to hold any button)"

3. **Test Voice Commands**
   Try these examples in any language:
   
   **English:**
   - "Find me flights from New York to Paris next Tuesday"
   - "I need to fly from Los Angeles to London in business class"
   - "Show me cheap flights from Chicago to Miami"
   
   **Spanish:**
   - "Buscar vuelos de Madrid a Barcelona"
   - "Necesito volar de México a Buenos Aires"
   
   **French:**
   - "Chercher des vols de Paris à Londres"
   - "Je veux aller de Lyon à Rome"
   
   **Other Languages:**
   - German, Italian, Portuguese, Chinese, Japanese, Korean, Arabic, Hindi, Russian, and 80+ more!

4. **What to Expect**
   - Your speech appears in real-time as you talk
   - The assistant responds in the same language you speak
   - Flight results are displayed in the chat
   - You can interrupt the assistant while it's speaking

## 🧪 API Testing

Test the APIs directly:

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test flight search API
curl -X POST http://localhost:8000/search_flights \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "JFK",
    "destination": "CDG",
    "departure_date": "2025-07-15",
    "passengers": 1,
    "cabin_class": "economy"
  }'

# View API documentation
open http://localhost:8000/docs
```

## 🔍 Monitor Logs

Watch the logs in real-time:

```bash
# API server logs
tail -f api_server.log

# Web server logs
tail -f web_server.log

# Application logs
tail -f logs/api_server/$(ls -t logs/api_server/ | head -1)
tail -f logs/voice_processor/$(ls -t logs/voice_processor/ | head -1)
```

## 🛑 Stop Servers

When done testing:

```bash
# Find and kill the processes
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill
lsof -i :3000 | grep LISTEN | awk '{print $2}' | xargs kill
```

## ✅ Verification Checklist

- [ ] Web interface loads at http://localhost:3000/realtime.html
- [ ] Microphone permission granted
- [ ] "Start Listening" button works
- [ ] Real-time transcription shows your speech
- [ ] Assistant responds in your language
- [ ] Flight search returns results (Amadeus API or mock data)
- [ ] You can interrupt the assistant while speaking
- [ ] Messages appear in correct order (user first, then assistant)

## 🚀 Next Steps

Once local testing is successful:
1. Deploy to LiveKit Cloud
2. Deploy to AWS ECS
3. Configure production environment

## 🐛 Troubleshooting

**Microphone not working:**
- Check browser permissions
- Try Chrome or Edge (better WebRTC support)
- Check system microphone settings

**No audio response:**
- Check browser console for errors
- Ensure speakers/headphones are connected
- Try refreshing the page

**API errors:**
- Check api_server.log for details
- Verify all API keys in .env file
- Ensure Amadeus credentials are valid

**WebSocket disconnects:**
- Check network stability
- Look for errors in browser console
- Restart both servers if needed