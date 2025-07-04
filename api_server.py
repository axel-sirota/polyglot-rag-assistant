from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from livekit import api
import os
from dotenv import load_dotenv
import logging

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Polyglot RAG API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

# Request models
class TokenRequest(BaseModel):
    identity: str
    room: str

class ChatRequest(BaseModel):
    message: str
    language: str = "en"

# Endpoints
@app.get("/")
async def root():
    return {"message": "Polyglot RAG API is running"}

@app.post("/api/token")
async def generate_token(request: TokenRequest):
    """Generate LiveKit access token"""
    try:
        if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
            raise HTTPException(status_code=500, detail="LiveKit credentials not configured")
        
        # Create access token
        token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        token.with_identity(request.identity)
        token.with_name(request.identity)
        token.with_grants(api.VideoGrants(
            room_join=True,
            room=request.room,
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True
        ))
        
        jwt_token = token.to_jwt()
        
        return {"token": jwt_token}
        
    except Exception as e:
        logger.error(f"Token generation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate token")

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Handle chat messages (placeholder for direct API calls)"""
    # This is a placeholder endpoint for the web/mobile apps
    # In production, this would connect to your orchestrator
    return {
        "response": f"I received your message in {request.language}: {request.message}",
        "language": request.language,
        "flightResults": []
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)