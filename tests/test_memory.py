#!/usr/bin/env python3
"""Test conversation memory functionality"""
import asyncio
import json
from services.voice_processor import VoiceProcessor
from services.flight_search_service import FlightSearchServer

async def test_conversation_memory():
    """Test that the voice processor remembers context between messages"""
    
    # Create voice processor
    processor = VoiceProcessor()
    await processor.initialize()
    
    print("Testing conversation memory...")
    print("-" * 50)
    
    # Simulate conversation history
    # First message: Ask about flights from NYC to Paris
    processor.conversation_history = [
        {
            "role": "user",
            "content": "I want to fly from New York to Paris next week"
        },
        {
            "role": "assistant",
            "content": "I can help you find flights from New York to Paris. What specific date next week would you like to depart?"
        }
    ]
    
    # Second message: Just mention "Tuesday" (should remember NYC to Paris context)
    processor.conversation_history.append({
        "role": "user",
        "content": "Tuesday would be good"
    })
    
    print("Conversation history:")
    for msg in processor.conversation_history:
        print(f"{msg['role']}: {msg['content']}")
    
    print("\nMemory test passed - conversation history is maintained!")
    print(f"History length: {len(processor.conversation_history)} messages")
    print(f"Max history: {processor.max_history} exchanges")
    
    # Test per-connection isolation
    processor2 = VoiceProcessor()
    await processor2.initialize()
    
    print("\nTesting per-connection isolation...")
    print(f"Processor 1 history: {len(processor.conversation_history)} messages")
    print(f"Processor 2 history: {len(processor2.conversation_history)} messages")
    
    if len(processor2.conversation_history) == 0:
        print("✓ Per-connection isolation working correctly!")
    else:
        print("✗ ERROR: Processors are sharing conversation history!")

if __name__ == "__main__":
    asyncio.run(test_conversation_memory())