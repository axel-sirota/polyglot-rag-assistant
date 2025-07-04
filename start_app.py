#!/usr/bin/env python3
"""Start the Gradio app with error handling"""
import sys
import traceback

try:
    print("Starting Polyglot RAG app...")
    sys.path.append('.')
    
    print("Importing gradio_app...")
    from frontend.gradio_app import main
    
    print("Starting main...")
    main()
    
except Exception as e:
    print(f"Error starting app: {e}")
    traceback.print_exc()
    sys.exit(1)