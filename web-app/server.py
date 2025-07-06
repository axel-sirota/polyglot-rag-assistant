#!/usr/bin/env python3
"""
Simple HTTP server for the Polyglot RAG web app
Serves static files and proxies LiveKit token requests
"""
import os
import json
import logging
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.request
import urllib.parse
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API URL for token generation
API_URL = os.getenv('API_URL', 'http://localhost:8000')

class RequestHandler(SimpleHTTPRequestHandler):
    """Custom request handler with API proxy support"""
    
    def do_POST(self):
        """Handle POST requests for LiveKit tokens"""
        if self.path == '/api/livekit-token':
            self.handle_token_request()
        else:
            self.send_error(404, "Not Found")
    
    def handle_token_request(self):
        """Proxy token request to backend API"""
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            # Add room metadata to trigger agent
            request_data['roomMetadata'] = json.dumps({
                'require_agent': True,
                'agent_name': 'polyglot-flight-agent'
            })
            
            # Make request to backend
            url = f"{API_URL}/api/livekit/token"
            req = urllib.request.Request(
                url,
                data=json.dumps(request_data).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req) as response:
                response_data = response.read()
                
                # Send response
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(response_data)
                
        except Exception as e:
            logger.error(f"Token request error: {e}")
            self.send_error(500, f"Token request failed: {str(e)}")
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def end_headers(self):
        """Add CORS headers to all responses"""
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

def run_server(port=8080):
    """Run the HTTP server"""
    server_address = ('', port)
    
    # Change to web-app directory to serve files
    web_app_dir = Path(__file__).parent
    os.chdir(web_app_dir)
    
    httpd = HTTPServer(server_address, RequestHandler)
    logger.info(f"Server running on http://localhost:{port}")
    logger.info(f"Serving files from: {web_app_dir}")
    logger.info(f"API backend: {API_URL}")
    logger.info("Available pages:")
    logger.info(f"  - http://localhost:{port}/livekit-client.html (Original)")
    logger.info(f"  - http://localhost:{port}/livekit-voice-chat.html (Voice + Chat)")
    logger.info(f"  - http://localhost:{port}/realtime.html (Realtime API)")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("\nShutting down server...")
        httpd.shutdown()

if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port)