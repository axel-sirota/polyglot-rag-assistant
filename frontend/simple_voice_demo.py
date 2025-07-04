"""Simple voice demo to test functionality"""
import gradio as gr
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

def process_voice(audio):
    if audio is None:
        return "No audio received", None
    
    try:
        # Simple transcription
        import io
        import soundfile as sf
        
        # audio is (sample_rate, data)
        sample_rate, audio_data = audio
        
        # Save to buffer
        buffer = io.BytesIO()
        sf.write(buffer, audio_data, sample_rate, format='WAV')
        buffer.seek(0)
        buffer.name = "audio.wav"
        
        # Transcribe
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=buffer
        )
        
        text = transcript.text
        
        # Simple response
        response = f"You said: {text}"
        
        # TTS
        tts_response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=response
        )
        
        # Return text and audio
        return response, tts_response.content
        
    except Exception as e:
        return f"Error: {str(e)}", None

# Create interface
demo = gr.Interface(
    fn=process_voice,
    inputs=gr.Audio(sources=["microphone"], type="numpy"),
    outputs=[
        gr.Textbox(label="Response"),
        gr.Audio(label="Audio Response", type="filepath")
    ],
    title="Simple Voice Test"
)

if __name__ == "__main__":
    print("Starting simple voice demo...")
    demo.launch(server_name="0.0.0.0", server_port=7861, share=True)