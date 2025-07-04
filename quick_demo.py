"""Simplest possible voice demo for MVP"""
import os
from openai import OpenAI
from dotenv import load_dotenv
import tempfile

load_dotenv()
client = OpenAI()

print("🎤 Simple Voice Demo")
print("=" * 40)

while True:
    input("\nPress Enter to start recording (or Ctrl+C to quit)...")
    
    # Simulate recording (in real app, would record from microphone)
    print("🔴 Recording... (using test audio for demo)")
    
    # For demo, use a test phrase
    test_text = "Find me flights from New York to Paris tomorrow"
    print(f"\n📝 Transcribed: {test_text}")
    
    # Process with GPT-4
    print("\n🤔 Processing...")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful flight search assistant."},
            {"role": "user", "content": test_text}
        ]
    )
    
    answer = response.choices[0].message.content
    print(f"\n🤖 Response: {answer}")
    
    # Generate audio
    print("\n🔊 Generating audio...")
    tts_response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=answer
    )
    
    # Save audio
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(tts_response.content)
        print(f"✅ Audio saved to: {f.name}")
        print("   (In real app, would play automatically)")