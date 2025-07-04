"""FastAPI backend with WebSocket support for voice assistant"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio
import json
import base64
import logging
from typing import Optional, Dict, Any, List
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.voice_processor import VoiceProcessor
from services.flight_search_service import FlightSearchServer
from utils.logging_config import setup_logging

# Set up logging
logger = setup_logging('api_server')

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
        self.active_connections.remove(websocket)
        if websocket in self.connection_data:
            del self.connection_data[websocket]
        logger.info(f"WebSocket disconnected: {websocket.client}")

    async def send_json(self, websocket: WebSocket, data: Dict[str, Any]):
        await websocket.send_json(data)

    async def broadcast(self, data: Dict[str, Any]):
        for connection in self.active_connections:
            await connection.send_json(data)

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
                "process_audio": "/process_audio"
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
                        
                        await manager.send_json(websocket, response)
                
                except Exception as e:
                    logger.error(f"Voice processing error: {e}")
                    await manager.send_json(websocket, {
                        "type": "error",
                        "error": str(e)
                    })
            
            elif message_type == "text":
                # Process text query
                text = data.get("text")
                language = data.get("language", "auto")
                
                if not text:
                    await manager.send_json(websocket, {
                        "type": "error",
                        "error": "No text provided"
                    })
                    continue
                
                # Create a mock audio request for the text
                # In real implementation, you might want a separate text processing path
                await manager.send_json(websocket, {
                    "type": "processing",
                    "message": "Processing text query..."
                })
                
                # For now, send to the standard pipeline
                # You could implement a text-only path here
                
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
        # For text queries, we'll use the standard pipeline
        # Convert text to a voice query by using TTS first, then process
        
        # This is a simplified version - in production, you might want
        # a dedicated text processing path
        
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
        responses = []
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
                "realtime_available": voice_processor.realtime_available,
                "supported_languages": voice_processor.supported_languages
            },
            "flight_service": {
                "initialized": flight_service is not None,
                "has_aviation_key": bool(flight_service.aviationstack_key),
                "has_serp_key": bool(flight_service.serpapi_key)
            }
        },
        "websocket_connections": len(manager.active_connections)
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

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)