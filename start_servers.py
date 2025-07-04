#!/usr/bin/env python3
"""
Start both API and Web servers for Polyglot RAG Assistant
Run from project root directory
"""
import subprocess
import time
import sys
import os
import signal
import atexit

# Store process references for cleanup
processes = []

def cleanup():
    """Kill all started processes on exit"""
    print("\n🛑 Shutting down servers...")
    for p in processes:
        try:
            p.terminate()
            p.wait(timeout=5)
        except:
            p.kill()
    print("✅ Servers stopped")

# Register cleanup on exit
atexit.register(cleanup)

def start_servers():
    """Start API and Web servers"""
    print("🚀 Starting Polyglot RAG Voice Assistant...")
    print("=" * 60)
    
    # Start API server
    print("📡 Starting API server on port 8000...")
    api_process = subprocess.Popen(
        [".venv/bin/python3", "api_server.py"],
        stdout=open("api_server.log", "w"),
        stderr=subprocess.STDOUT
    )
    processes.append(api_process)
    
    # Wait a bit for API server to start
    time.sleep(3)
    
    # Start web server from root directory, serving web-app folder
    print("🌐 Starting web server on port 3000...")
    web_process = subprocess.Popen(
        ["python3", "-m", "http.server", "3000", "--directory", "web-app"],
        stdout=open("web_server.log", "w"),
        stderr=subprocess.STDOUT
    )
    processes.append(web_process)
    
    # Wait for servers to be ready
    time.sleep(2)
    
    # Check if servers are running
    import urllib.request
    import urllib.error
    
    try:
        # Check API server
        with urllib.request.urlopen("http://localhost:8000/health", timeout=2) as response:
            if response.status == 200:
                print("✅ API server is running at http://localhost:8000")
                print("   Documentation: http://localhost:8000/docs")
            else:
                print("❌ API server health check failed")
    except (urllib.error.URLError, urllib.error.HTTPError, OSError):
        print("⏳ API server is starting...")
    
    try:
        # Check web server
        with urllib.request.urlopen("http://localhost:3000", timeout=2) as response:
            if response.status == 200:
                print("✅ Web server is running at http://localhost:3000")
                print("   Voice Interface: http://localhost:3000/realtime.html")
            else:
                print("❌ Web server check failed")
    except (urllib.error.URLError, urllib.error.HTTPError, OSError):
        print("⏳ Web server is starting...")
    
    print("\n" + "=" * 60)
    print("🎤 Ready to use!")
    print("Open your browser to: http://localhost:3000/realtime.html")
    print("=" * 60)
    print("\nPress Ctrl+C to stop all servers\n")
    
    # Keep the script running
    try:
        # Monitor processes
        while True:
            # Check if processes are still running
            if api_process.poll() is not None:
                print("⚠️  API server stopped unexpectedly!")
                break
            if web_process.poll() is not None:
                print("⚠️  Web server stopped unexpectedly!")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n📍 Received shutdown signal...")

if __name__ == "__main__":
    # Handle Ctrl+C gracefully
    signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(0))
    
    # Make sure we're in the right directory
    if not os.path.exists("api_server.py"):
        print("❌ Error: This script must be run from the project root directory")
        print("   Current directory:", os.getcwd())
        sys.exit(1)
    
    # Check for virtual environment
    if not os.path.exists(".venv/bin/python3"):
        print("❌ Error: Virtual environment not found at .venv/")
        print("   Please create it with: python3 -m venv .venv")
        sys.exit(1)
    
    start_servers()