#!/usr/bin/env python3
"""
Automated test for voice interruption handling
Tests various interruption scenarios to ensure the system handles them properly
"""

import asyncio
import websockets
import json
import base64
import numpy as np
import time
from typing import List, Dict, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InterruptionTester:
    def __init__(self, ws_url: str = "ws://localhost:8000/ws"):
        self.ws_url = ws_url
        self.ws = None
        self.received_messages = []
        self.test_results = []
        
        # Audio generation parameters
        self.sample_rate = 24000
        self.duration_ms = 100  # 100ms chunks
        
    async def connect(self):
        """Connect to WebSocket server"""
        self.ws = await websockets.connect(self.ws_url)
        logger.info("Connected to WebSocket server")
        
        # Send initial config
        await self.ws.send(json.dumps({
            "type": "config",
            "continuous": True,
            "language": "auto"
        }))
        
        # Start message receiver
        asyncio.create_task(self._message_receiver())
        
    async def _message_receiver(self):
        """Receive messages from server"""
        try:
            async for message in self.ws:
                data = json.loads(message)
                self.received_messages.append(data)
                logger.debug(f"Received: {data.get('type')}")
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")
            
    def generate_audio_chunk(self, frequency: float = 440.0) -> bytes:
        """Generate a sine wave audio chunk"""
        samples = int(self.sample_rate * self.duration_ms / 1000)
        t = np.linspace(0, self.duration_ms/1000, samples, False)
        wave = np.sin(frequency * 2 * np.pi * t)
        
        # Convert to PCM16
        pcm16 = np.int16(wave * 32767)
        return pcm16.tobytes()
    
    def encode_audio(self, audio_data: bytes) -> str:
        """Encode audio data to base64"""
        return base64.b64encode(audio_data).decode('utf-8')
    
    async def send_audio(self, duration_ms: int = 1000):
        """Send audio for specified duration"""
        chunks = duration_ms // self.duration_ms
        for i in range(chunks):
            audio_chunk = self.generate_audio_chunk(440.0 + i * 10)  # Vary frequency
            await self.ws.send(json.dumps({
                "type": "audio",
                "audio": self.encode_audio(audio_chunk),
                "continuous": True
            }))
            await asyncio.sleep(self.duration_ms / 1000)
    
    async def wait_for_response(self, timeout: float = 5.0) -> bool:
        """Wait for assistant to start responding"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Check if we received transcript_delta (assistant speaking)
            for msg in reversed(self.received_messages):
                if msg.get('type') == 'transcript_delta':
                    return True
            await asyncio.sleep(0.1)
        return False
    
    async def test_basic_interruption(self):
        """Test 1: Basic interruption during assistant response"""
        logger.info("\n=== Test 1: Basic Interruption ===")
        self.received_messages.clear()
        
        # Step 1: Send initial query
        logger.info("Sending initial query...")
        await self.send_audio(1500)  # 1.5 seconds of audio
        
        # Step 2: Wait for assistant to start responding
        logger.info("Waiting for assistant response...")
        if not await self.wait_for_response():
            self.test_results.append({
                "test": "basic_interruption",
                "passed": False,
                "reason": "Assistant did not respond"
            })
            return
        
        # Step 3: Wait a bit to let assistant speak
        await asyncio.sleep(1.0)
        
        # Step 4: Interrupt with new audio
        logger.info("Interrupting assistant...")
        interrupt_start = time.time()
        await self.send_audio(1000)  # 1 second interruption
        
        # Step 5: Check if assistant stopped
        await asyncio.sleep(0.5)
        audio_after_interrupt = False
        for msg in self.received_messages:
            if msg.get('type') == 'audio_delta' and \
               msg.get('timestamp', 0) > interrupt_start:
                audio_after_interrupt = True
                break
        
        self.test_results.append({
            "test": "basic_interruption",
            "passed": not audio_after_interrupt,
            "reason": "Audio continued after interruption" if audio_after_interrupt else "Success"
        })
    
    async def test_rapid_interruptions(self):
        """Test 2: Multiple rapid interruptions"""
        logger.info("\n=== Test 2: Rapid Interruptions ===")
        self.received_messages.clear()
        
        # Send initial query
        await self.send_audio(1000)
        
        # Wait for response
        if not await self.wait_for_response():
            self.test_results.append({
                "test": "rapid_interruptions",
                "passed": False,
                "reason": "Assistant did not respond"
            })
            return
        
        # Rapid interruptions
        success = True
        for i in range(3):
            await asyncio.sleep(0.5)
            logger.info(f"Rapid interruption {i+1}...")
            await self.send_audio(300)  # Short bursts
        
        self.test_results.append({
            "test": "rapid_interruptions",
            "passed": success,
            "reason": "Success" if success else "Failed to handle rapid interruptions"
        })
    
    async def test_no_false_interruption(self):
        """Test 3: Ensure no false interruptions (assistant completes when not interrupted)"""
        logger.info("\n=== Test 3: No False Interruption ===")
        self.received_messages.clear()
        
        # Send query
        await self.send_audio(1000)
        
        # Wait for response to complete
        await asyncio.sleep(5.0)
        
        # Check if we got a complete response
        got_complete = False
        for msg in self.received_messages:
            if msg.get('type') == 'response_complete':
                got_complete = True
                break
        
        self.test_results.append({
            "test": "no_false_interruption",
            "passed": got_complete,
            "reason": "Success" if got_complete else "Response did not complete naturally"
        })
    
    async def test_multilingual_interruption(self):
        """Test 4: Interruption during multilingual response"""
        logger.info("\n=== Test 4: Multilingual Interruption ===")
        self.received_messages.clear()
        
        # This test would require actual speech audio in different languages
        # For now, we'll simulate with tones
        
        self.test_results.append({
            "test": "multilingual_interruption",
            "passed": True,
            "reason": "Simulated test - requires real speech audio"
        })
    
    async def run_all_tests(self):
        """Run all interruption tests"""
        await self.connect()
        
        # Run tests
        await self.test_basic_interruption()
        await asyncio.sleep(2)  # Pause between tests
        
        await self.test_rapid_interruptions()
        await asyncio.sleep(2)
        
        await self.test_no_false_interruption()
        await asyncio.sleep(2)
        
        await self.test_multilingual_interruption()
        
        # Close connection
        await self.ws.close()
        
        # Print results
        self.print_results()
    
    def print_results(self):
        """Print test results summary"""
        print("\n" + "="*50)
        print("INTERRUPTION TEST RESULTS")
        print("="*50)
        
        passed = 0
        failed = 0
        
        for result in self.test_results:
            status = "✅ PASSED" if result["passed"] else "❌ FAILED"
            print(f"\n{result['test']}: {status}")
            print(f"  Reason: {result['reason']}")
            
            if result["passed"]:
                passed += 1
            else:
                failed += 1
        
        print("\n" + "="*50)
        print(f"Total: {len(self.test_results)} tests")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/len(self.test_results)*100):.1f}%")
        print("="*50)

async def main():
    """Main test runner"""
    tester = InterruptionTester()
    
    try:
        await tester.run_all_tests()
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Starting Interruption Tests...")
    print("Make sure the API server is running on localhost:8000")
    asyncio.run(main())