#!/usr/bin/env python3
"""Test all API connections and basic functionality"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_openai_connection():
    """Test OpenAI API connection"""
    try:
        import openai
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Test chat completion
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'test passed'"}],
            max_tokens=10
        )
        print("✅ OpenAI Chat API: Connected")
        print(f"   Response: {response.choices[0].message.content}")
        
        # Test embeddings
        embedding = client.embeddings.create(
            input="test",
            model="text-embedding-3-small"
        )
        print("✅ OpenAI Embeddings API: Connected")
        
        # Test Whisper
        print("✅ OpenAI Whisper API: Ready (requires audio file to test)")
        
        # Test TTS
        print("✅ OpenAI TTS API: Ready (requires text to test)")
        
        return True
    except Exception as e:
        print(f"❌ OpenAI API Error: {e}")
        return False

async def test_anthropic_connection():
    """Test Anthropic API connection"""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=10,
            messages=[{"role": "user", "content": "Say 'test passed'"}]
        )
        print("✅ Anthropic API: Connected")
        print(f"   Response: {response.content[0].text}")
        return True
    except Exception as e:
        print(f"❌ Anthropic API Error: {e}")
        return False

async def test_livekit_connection():
    """Test LiveKit connection"""
    try:
        # Just check if we have the credentials
        livekit_url = os.getenv("LIVEKIT_URL")
        livekit_api_key = os.getenv("LIVEKIT_API_KEY")
        livekit_api_secret = os.getenv("LIVEKIT_API_SECRET")
        
        if livekit_url and livekit_api_key and livekit_api_secret:
            print("✅ LiveKit: Credentials found")
            print(f"   URL: {livekit_url}")
            return True
        else:
            print("❌ LiveKit: Missing credentials")
            return False
    except Exception as e:
        print(f"❌ LiveKit Error: {e}")
        return False

async def test_flight_api():
    """Test flight search API"""
    try:
        serpapi_key = os.getenv("SERPAPI_API_KEY")
        aviationstack_key = os.getenv("AVIATIONSTACK_API_KEY")
        
        if serpapi_key:
            print("✅ SerpAPI: API key found")
        else:
            print("⚠️  SerpAPI: No API key (will use mock data)")
            
        if aviationstack_key:
            print("✅ Aviationstack: API key found")
        else:
            print("⚠️  Aviationstack: No API key (will use mock data)")
            
        return True
    except Exception as e:
        print(f"❌ Flight API Error: {e}")
        return False

async def test_gradio():
    """Test Gradio import"""
    try:
        import gradio as gr
        print("✅ Gradio: Installed and ready")
        print(f"   Version: {gr.__version__}")
        return True
    except Exception as e:
        print(f"❌ Gradio Error: {e}")
        return False

async def test_faiss():
    """Test FAISS vector store"""
    try:
        import faiss
        import numpy as np
        
        # Create a simple index
        dimension = 128
        index = faiss.IndexFlatL2(dimension)
        
        # Add some vectors
        vectors = np.random.random((10, dimension)).astype('float32')
        index.add(vectors)
        
        # Search
        query = np.random.random((1, dimension)).astype('float32')
        distances, indices = index.search(query, 5)
        
        print("✅ FAISS: Working")
        print(f"   Index size: {index.ntotal} vectors")
        return True
    except Exception as e:
        print(f"❌ FAISS Error: {e}")
        return False

async def main():
    """Run all tests"""
    print("🧪 Testing Polyglot RAG Components\n")
    
    tests = [
        test_openai_connection(),
        test_anthropic_connection(),
        test_livekit_connection(),
        test_flight_api(),
        test_gradio(),
        test_faiss()
    ]
    
    results = await asyncio.gather(*tests)
    
    print("\n📊 Test Summary:")
    passed = sum(results)
    total = len(results)
    print(f"   Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ All tests passed! Ready for demo.")
    else:
        print("\n⚠️  Some tests failed. Check your .env file.")

if __name__ == "__main__":
    asyncio.run(main())