"""
Simplified API Server for Polyglot Flight Assistant
This is the main entry point - just run: python api_server.py
"""

import os
import sys
import logging
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point - starts the FastAPI server"""
    try:
        # Import and run the FastAPI app
        import uvicorn
        from api.main import app
        
        # Get port from environment or use default
        port = int(os.getenv("PORT", 8000))
        host = os.getenv("HOST", "0.0.0.0")
        
        logger.info(f"Starting Flight Voice Assistant API on {host}:{port}")
        logger.info("Documentation available at: http://localhost:8000/docs")
        logger.info("Web interface: Run 'cd web-app && python3 -m http.server 3000'")
        
        # Run the server
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Please install dependencies: .venv/bin/python3 -m pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()