"""
FastAPI + WebSocket implementation for OpenAI Realtime Voice
More reliable than Gradio for audio streaming
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import json
import asyncio
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
import base64
import logging

load_dotenv()

app = FastAPI()
client = AsyncOpenAI()

# Simple HTML interface
html = """
<!DOCTYPE html>
<html>
<head>
    <title>Voice Assistant</title>
    <style>
        body { font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; }
        #status { margin: 20px 0; padding: 10px; background: #f0f0f0; }
        button { padding: 10px 20px; margin: 10px; font-size: 16px; }
        #messages { height: 300px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; margin: 20px 0; }
        .message { margin: 10px 0; }
        .user { color: blue; }
        .assistant { color: green; }
    </style>
</head>
<body>
    <h1>🎤 Voice Assistant (FastAPI)</h1>
    <div id="status">Ready</div>
    <button id="recordBtn">🔴 Start Recording</button>
    <div id="messages"></div>
    
    <script>
        let ws;
        let mediaRecorder;
        let audioChunks = [];
        const recordBtn = document.getElementById('recordBtn');
        const status = document.getElementById('status');
        const messages = document.getElementById('messages');
        
        // Connect WebSocket
        ws = new WebSocket('ws://localhost:8000/ws');
        
        ws.onopen = () => {
            status.textContent = 'Connected';
        };
        
        ws.onmessage = async (event) => {
            const data = JSON.parse(event.data);
            
            if (data.type === 'transcript') {
                addMessage('user', data.text);
            } else if (data.type === 'response') {
                addMessage('assistant', data.text);
                if (data.audio) {
                    playAudio(data.audio);
                }
            } else if (data.type === 'error') {
                status.textContent = 'Error: ' + data.message;
            }
        };
        
        ws.onclose = () => {
            status.textContent = 'Disconnected';
        };
        
        // Recording logic
        recordBtn.onclick = async () => {
            if (mediaRecorder && mediaRecorder.state === 'recording') {
                mediaRecorder.stop();
                recordBtn.textContent = '🔴 Start Recording';
            } else {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];
                
                mediaRecorder.ondataavailable = (event) => {
                    audioChunks.push(event.data);
                };
                
                mediaRecorder.onstop = async () => {
                    const audioBlob = new Blob(audioChunks);
                    const reader = new FileReader();
                    reader.readAsDataURL(audioBlob);
                    reader.onloadend = () => {
                        const base64Audio = reader.result.split(',')[1];
                        ws.send(JSON.stringify({
                            type: 'audio',
                            data: base64Audio
                        }));
                    };
                };
                
                mediaRecorder.start();
                recordBtn.textContent = '⏹️ Stop Recording';
                status.textContent = 'Recording...';
            }
        };
        
        function addMessage(role, text) {
            const div = document.createElement('div');
            div.className = 'message ' + role;
            div.textContent = role + ': ' + text;
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
        }
        
        function playAudio(base64Audio) {
            const audio = new Audio('data:audio/mp3;base64,' + base64Audio);
            audio.play();
        }
    </script>
</body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data['type'] == 'audio':
                # Decode base64 audio
                audio_data = base64.b64decode(data['data'])
                
                # Save to temp file (Whisper needs a file)
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as f:
                    f.write(audio_data)
                    temp_path = f.name
                
                # Transcribe
                with open(temp_path, 'rb') as audio_file:
                    transcript = await client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file
                    )
                
                # Send transcript
                await websocket.send_json({
                    'type': 'transcript',
                    'text': transcript.text
                })
                
                # Process with GPT-4
                response = await client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a helpful voice assistant."},
                        {"role": "user", "content": transcript.text}
                    ]
                )
                
                response_text = response.choices[0].message.content
                
                # Generate audio response
                tts_response = await client.audio.speech.create(
                    model="tts-1",
                    voice="alloy",
                    input=response_text
                )
                
                # Convert to base64
                audio_base64 = base64.b64encode(tts_response.content).decode()
                
                # Send response
                await websocket.send_json({
                    'type': 'response',
                    'text': response_text,
                    'audio': audio_base64
                })
                
                # Cleanup
                os.unlink(temp_path)
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({
            'type': 'error',
            'message': str(e)
        })

if __name__ == "__main__":
    import uvicorn
    print("Starting FastAPI voice app on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)