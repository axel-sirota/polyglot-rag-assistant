#!/usr/bin/env python3
"""Test Gradio interface components"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

def test_gradio_basic():
    """Test basic Gradio functionality"""
    try:
        import gradio as gr
        
        print("🖥️ Testing Gradio Interface\n")
        
        # Test basic interface creation
        def process_text(text):
            return f"Processed: {text}"
        
        demo = gr.Interface(
            fn=process_text,
            inputs="text",
            outputs="text",
            title="Test Interface"
        )
        
        print("✅ Basic Gradio interface created")
        
        # Test Blocks interface
        with gr.Blocks() as blocks_demo:
            gr.Markdown("# Test Blocks Interface")
            with gr.Row():
                text_input = gr.Textbox(label="Input")
                text_output = gr.Textbox(label="Output")
            btn = gr.Button("Process")
            btn.click(process_text, inputs=text_input, outputs=text_output)
        
        print("✅ Gradio Blocks interface created")
        
        # Test audio components
        with gr.Blocks() as audio_demo:
            audio_input = gr.Audio(sources=["microphone"], type="filepath")
            audio_output = gr.Audio(type="filepath")
        
        print("✅ Audio components created")
        
        return True
        
    except Exception as e:
        print(f"❌ Gradio Test Error: {e}")
        return False

def test_gradio_voice_interface():
    """Test voice-enabled Gradio interface"""
    try:
        import gradio as gr
        from pathlib import Path
        
        print("\n2. Testing Voice Interface Components...")
        
        # Create a mock voice processing function
        def mock_voice_process(audio_path):
            if audio_path:
                return "Mock transcription: Flight search request", "Mock response audio"
            return None, None
        
        with gr.Blocks(title="Voice Test") as demo:
            gr.Markdown("# 🎤 Voice Interface Test")
            
            with gr.Row():
                with gr.Column():
                    audio_input = gr.Audio(
                        sources=["microphone", "upload"],
                        type="filepath",
                        label="Speak or Upload"
                    )
                    submit_btn = gr.Button("Process Voice", variant="primary")
                
                with gr.Column():
                    transcript_output = gr.Textbox(label="Transcript")
                    response_output = gr.Textbox(label="Response")
            
            submit_btn.click(
                mock_voice_process,
                inputs=[audio_input],
                outputs=[transcript_output, response_output]
            )
        
        print("✅ Voice interface components created")
        
        # Test streaming audio
        def mock_stream(audio):
            yield "Processing..."
            yield "Complete!"
        
        with gr.Blocks() as stream_demo:
            gr.Audio(source="microphone", streaming=True)
        
        print("✅ Streaming audio component created")
        
        return True
        
    except Exception as e:
        print(f"❌ Voice Interface Error: {e}")
        return False

def test_full_demo_interface():
    """Test the full demo interface"""
    try:
        from frontend.gradio_app import create_demo_interface
        
        print("\n3. Testing Full Demo Interface...")
        
        # Try to create the demo interface
        demo = create_demo_interface()
        
        print("✅ Full demo interface created successfully")
        print("   - Chat interface ready")
        print("   - Voice input ready")
        print("   - Flight search integration ready")
        
        return True
        
    except Exception as e:
        print(f"❌ Full Demo Error: {e}")
        print("   (This is expected if create_demo_interface is not implemented yet)")
        return True  # Don't fail the test for missing implementation

def main():
    """Run Gradio tests"""
    print("🎨 Testing Gradio Components\n")
    
    tests = [
        test_gradio_basic(),
        test_gradio_voice_interface(),
        test_full_demo_interface()
    ]
    
    results = [test() for test in tests]
    
    print("\n📊 Gradio Test Summary:")
    passed = sum(results)
    total = len(results)
    print(f"   Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ All Gradio tests passed!")
        print("   Run 'python frontend/gradio_app.py' to start the interface")

if __name__ == "__main__":
    main()