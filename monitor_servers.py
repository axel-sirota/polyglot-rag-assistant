#!/usr/bin/env python3
"""
Monitor running servers and show logs
"""
import subprocess
import time
import os
import sys

def tail_logs():
    """Show logs from both servers"""
    print("📊 Monitoring server logs...")
    print("=" * 60)
    
    # Check if log files exist
    if not os.path.exists("api_server.log"):
        print("⚠️  No api_server.log found. Start servers first with: python3 start_servers.py")
        return
    
    if not os.path.exists("web_server.log"):
        print("⚠️  No web_server.log found. Start servers first with: python3 start_servers.py")
        return
    
    print("Press Ctrl+C to stop monitoring\n")
    
    # Use tail to follow both logs
    try:
        # Start tail processes
        api_tail = subprocess.Popen(
            ["tail", "-f", "api_server.log"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        web_tail = subprocess.Popen(
            ["tail", "-f", "web_server.log"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Monitor both logs
        import select
        
        while True:
            # Check API log
            if api_tail.stdout:
                ready, _, _ = select.select([api_tail.stdout], [], [], 0.1)
                if ready:
                    line = api_tail.stdout.readline()
                    if line:
                        print(f"[API] {line.strip()}")
            
            # Check Web log
            if web_tail.stdout:
                ready, _, _ = select.select([web_tail.stdout], [], [], 0.1)
                if ready:
                    line = web_tail.stdout.readline()
                    if line:
                        print(f"[WEB] {line.strip()}")
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\n✅ Stopped monitoring logs")
        api_tail.terminate()
        web_tail.terminate()

def check_status():
    """Check if servers are running"""
    print("\n🔍 Checking server status...")
    
    # Check for running processes
    try:
        # Check API server
        api_check = subprocess.run(
            ["lsof", "-i", ":8000"],
            capture_output=True,
            text=True
        )
        if "LISTEN" in api_check.stdout:
            print("✅ API server is running on port 8000")
        else:
            print("❌ API server is not running")
        
        # Check web server
        web_check = subprocess.run(
            ["lsof", "-i", ":3000"],
            capture_output=True,
            text=True
        )
        if "LISTEN" in web_check.stdout:
            print("✅ Web server is running on port 3000")
        else:
            print("❌ Web server is not running")
            
    except Exception as e:
        print(f"Error checking status: {e}")

if __name__ == "__main__":
    check_status()
    print()
    tail_logs()