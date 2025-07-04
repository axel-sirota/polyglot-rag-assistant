"""
Simplified API Server for Polyglot Flight Assistant
This is the main entry point - just run: python api_server.py
"""

import os
import sys
import json
import base64
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
from utils.session_logging import setup_session_logging
logger = setup_session_logging('api_server')

# FastAPI imports
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# Import our services
from services.voice_processor import VoiceProcessor
from services.flight_search_service import FlightSearchServer

# Request models
class TextQueryRequest(BaseModel):
    text: str
    language: str = "auto"

class AudioQueryRequest(BaseModel):
    audio: str  # Base64 encoded audio
    language: str = "auto"

class FlightSearchRequest(BaseModel):
    origin: str
    destination: str
    departure_date: str
    return_date: Optional[str] = None
    passengers: int = 1
    cabin_class: str = "economy"
    currency: str = "USD"

# Create FastAPI app
app = FastAPI(
    title="Polyglot Flight Assistant API",
    version="2.0.0",
    description="Multilingual voice-enabled flight search with OpenAI Realtime API"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
voice_processor = VoiceProcessor()
flight_service = FlightSearchServer()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_data: Dict[WebSocket, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_data[websocket] = {
            "language": "auto",
            "session_id": None
        }
        logger.info(f"WebSocket connected: {websocket.client}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.connection_data:
            del self.connection_data[websocket]
        logger.info(f"WebSocket disconnected: {websocket.client}")

    async def send_json(self, websocket: WebSocket, data: Dict[str, Any]):
        await websocket.send_json(data)

manager = ConnectionManager()

# Initialize voice processor on startup
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    await voice_processor.initialize()
    logger.info("Voice processor initialized")

# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "Polyglot Flight Assistant API",
        "version": "2.0.0",
        "status": "running",
        "features": {
            "realtime_api": voice_processor.realtime_available,
            "languages": list(voice_processor.supported_languages.keys()),
            "websocket": "/ws",
            "endpoints": {
                "search_flights": "/search_flights",
                "process_text": "/process_text",
                "process_audio": "/process_audio",
                "docs": "/docs"
            }
        }
    }

# WebSocket endpoint for real-time voice interaction
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "audio":
                # Process audio data
                audio_base64 = data.get("audio")
                language = data.get("language", "auto")
                
                if not audio_base64:
                    await manager.send_json(websocket, {
                        "type": "error",
                        "error": "No audio data provided"
                    })
                    continue
                
                # Decode audio
                try:
                    audio_data = base64.b64decode(audio_base64)
                except Exception as e:
                    await manager.send_json(websocket, {
                        "type": "error",
                        "error": f"Invalid audio data: {str(e)}"
                    })
                    continue
                
                # Process voice input
                try:
                    async for response in voice_processor.process_voice_input(
                        audio_data,
                        language=language,
                        stream=True
                    ):
                        # Send response back to client
                        if response["type"] == "audio_delta" and response.get("audio"):
                            # Encode audio chunks
                            response["audio"] = base64.b64encode(response["audio"]).decode('utf-8')
                        elif response["type"] == "response_complete":
                            # Include the user's transcribed text
                            if "input_text" in response:
                                # First send the user's transcript
                                await manager.send_json(websocket, {
                                    "type": "user_transcript",
                                    "text": response["input_text"],
                                    "language": response.get("language", "en")
                                })
                            # Encode audio if present
                            if response.get("audio") and isinstance(response["audio"], bytes):
                                response["audio"] = base64.b64encode(response["audio"]).decode('utf-8')
                        
                        await manager.send_json(websocket, response)
                
                except Exception as e:
                    logger.error(f"Voice processing error: {e}")
                    await manager.send_json(websocket, {
                        "type": "error",
                        "error": str(e)
                    })
            
            elif message_type == "config":
                # Update connection configuration
                if "language" in data:
                    manager.connection_data[websocket]["language"] = data["language"]
                
                await manager.send_json(websocket, {
                    "type": "config_updated",
                    "config": manager.connection_data[websocket]
                })
            
            elif message_type == "ping":
                # Heartbeat
                await manager.send_json(websocket, {"type": "pong"})
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# REST API endpoints
@app.post("/search_flights")
async def search_flights(request: FlightSearchRequest):
    """Search for flights using the flight service"""
    try:
        flights = await flight_service.search_flights(
            origin=request.origin,
            destination=request.destination,
            departure_date=request.departure_date,
            return_date=request.return_date,
            passengers=request.passengers,
            cabin_class=request.cabin_class,
            currency=request.currency
        )
        return {
            "success": True,
            "flights": flights,
            "count": len(flights)
        }
    except Exception as e:
        logger.error(f"Flight search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process_text")
async def process_text(request: TextQueryRequest):
    """Process a text query"""
    try:
        return {
            "success": True,
            "message": "Text processing endpoint - implement based on your needs",
            "text": request.text,
            "language": request.language
        }
    except Exception as e:
        logger.error(f"Text processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process_audio")
async def process_audio(request: AudioQueryRequest):
    """Process an audio query"""
    try:
        # Decode audio
        audio_data = base64.b64decode(request.audio)
        
        # Process voice input (non-streaming for REST API)
        async for response in voice_processor.process_voice_input(
            audio_data,
            language=request.language,
            stream=False
        ):
            if response["type"] == "response_complete":
                return {
                    "success": True,
                    "text": response.get("text"),
                    "audio": base64.b64encode(response.get("audio", b"")).decode('utf-8') if response.get("audio") else None,
                    "language": response.get("language"),
                    "input_text": response.get("input_text")
                }
        
        return {
            "success": False,
            "error": "No response generated"
        }
        
    except Exception as e:
        logger.error(f"Audio processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    """Get API status and configuration"""
    return {
        "status": "operational",
        "services": {
            "voice_processor": {
                "initialized": voice_processor is not None,
                "realtime_available": voice_processor.realtime_available if voice_processor else False,
                "supported_languages": voice_processor.supported_languages if voice_processor else {}
            },
            "flight_service": {
                "initialized": flight_service is not None,
                "has_aviation_key": bool(flight_service.aviationstack_key) if flight_service else False,
                "has_serp_key": bool(flight_service.serpapi_key) if flight_service else False
            }
        },
        "websocket_connections": len(manager.active_connections)
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Not found", "path": str(request.url)}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

def main():
    """Main entry point"""
    # Get port from environment or use default
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"Starting Flight Voice Assistant API on {host}:{port}")
    logger.info(f"Documentation available at: http://localhost:{port}/docs")
    logger.info("Web interface: Run 'cd web-app && python3 -m http.server 3000'")
    
    # Run the server
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()