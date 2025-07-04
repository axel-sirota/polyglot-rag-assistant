#!/usr/bin/env python3
"""Test the voice processing pipeline"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_voice_pipeline():
    """Test complete voice pipeline: STT -> LLM -> TTS"""
    try:
        import openai
        from pathlib import Path
        
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        print("🎤 Testing Voice Pipeline\n")
        
        # Step 1: Generate test audio with TTS
        print("1. Generating test audio...")
        test_text = "Hello, I would like to find flights from New York to Paris."
        
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=test_text
        )
        
        audio_file = Path("tests/test_audio.mp3")
        audio_file.parent.mkdir(exist_ok=True)
        audio_file.write_bytes(response.content)
        print(f"   ✅ Audio generated: {audio_file}")
        
        # Step 2: Transcribe with Whisper
        print("\n2. Testing Speech-to-Text...")
        with open(audio_file, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="verbose_json"
            )
        
        print(f"   ✅ Transcribed: {transcript.text}")
        print(f"   Language detected: {transcript.language}")
        
        # Step 3: Process with LLM
        print("\n3. Processing with LLM...")
        llm_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a flight search assistant. Extract the origin and destination from the user's request."},
                {"role": "user", "content": transcript.text}
            ]
        )
        
        print(f"   ✅ LLM Response: {llm_response.choices[0].message.content}")
        
        # Step 4: Generate response audio
        print("\n4. Generating response audio...")
        response_audio = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=llm_response.choices[0].message.content
        )
        
        response_file = Path("tests/response_audio.mp3")
        response_file.write_bytes(response_audio.content)
        print(f"   ✅ Response audio saved: {response_file}")
        
        print("\n✅ Voice pipeline test completed successfully!")
        
        # Cleanup
        audio_file.unlink()
        response_file.unlink()
        
        return True
        
    except Exception as e:
        print(f"❌ Voice Pipeline Error: {e}")
        return False

async def test_multilingual():
    """Test multilingual capabilities"""
    try:
        import openai
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        print("\n🌍 Testing Multilingual Support\n")
        
        languages = {
            "Spanish": "Buscar vuelos de Madrid a Barcelona",
            "French": "Chercher des vols de Paris à Londres",
            "German": "Flüge von Berlin nach München finden"
        }
        
        for lang, text in languages.items():
            print(f"Testing {lang}: {text}")
            
            # Generate audio
            response = client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=text
            )
            
            # Save and transcribe
            audio_file = Path(f"tests/test_{lang.lower()}.mp3")
            audio_file.write_bytes(response.content)
            
            with open(audio_file, "rb") as f:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    response_format="verbose_json"
                )
            
            print(f"   ✅ Detected language: {transcript.language}")
            print(f"   Transcription: {transcript.text}")
            
            # Cleanup
            audio_file.unlink()
            
        return True
        
    except Exception as e:
        print(f"❌ Multilingual Test Error: {e}")
        return False

async def main():
    """Run voice tests"""
    print("🎙️ Testing Voice Components\n")
    
    await test_voice_pipeline()
    await test_multilingual()

if __name__ == "__main__":
    asyncio.run(main())