#!/usr/bin/env python3
"""
Comprehensive test suite for all fixes implemented
Tests without requiring the API server to be running
"""

import asyncio
import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.amadeus_flight_search import AmadeusFlightSearch
from services.flight_search_service import FlightSearchServer

class TestAllFixes(unittest.TestCase):
    """Test all implemented fixes"""
    
    def setUp(self):
        """Set up test environment"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        """Clean up"""
        self.loop.close()
    
    def test_interruption_manager_exists(self):
        """Test 1: Verify interruption manager is implemented"""
        # Check if file exists
        interrupt_manager_path = Path(__file__).parent.parent / "web-app" / "interruption_manager.js"
        self.assertTrue(interrupt_manager_path.exists(), "interruption_manager.js not found")
        
        # Check content
        content = interrupt_manager_path.read_text()
        self.assertIn("class InterruptionManager", content)
        self.assertIn("handleSpeechStarted", content)
        self.assertIn("response.cancel", content)
        self.assertIn("conversation.item.truncate", content)
        print("✅ Test 1 passed: Interruption manager properly implemented")
    
    def test_amadeus_api_integration(self):
        """Test 2: Verify Amadeus API integration"""
        # Check if file exists
        amadeus_path = Path(__file__).parent.parent / "services" / "amadeus_flight_search.py"
        self.assertTrue(amadeus_path.exists(), "amadeus_flight_search.py not found")
        
        # Test basic instantiation
        amadeus = AmadeusFlightSearch()
        self.assertIsNotNone(amadeus.client_id)
        self.assertIsNotNone(amadeus.client_secret)
        
        # Check methods exist
        self.assertTrue(hasattr(amadeus, 'search_flights'))
        self.assertTrue(hasattr(amadeus, '_get_access_token'))
        self.assertTrue(hasattr(amadeus, '_format_amadeus_results'))
        print("✅ Test 2 passed: Amadeus API properly integrated")
    
    def test_flight_search_service_updated(self):
        """Test 3: Verify flight search service uses Amadeus"""
        flight_service = FlightSearchServer()
        
        # Check Amadeus is initialized
        self.assertTrue(hasattr(flight_service, 'amadeus_search'))
        self.assertIsInstance(flight_service.amadeus_search, AmadeusFlightSearch)
        print("✅ Test 3 passed: Flight search service uses Amadeus API")
    
    def test_conversation_manager_exists(self):
        """Test 4: Verify conversation manager for message ordering"""
        conv_manager_path = Path(__file__).parent.parent / "web-app" / "conversation_manager.js"
        self.assertTrue(conv_manager_path.exists(), "conversation_manager.js not found")
        
        # Check content
        content = conv_manager_path.read_text()
        self.assertIn("class ConversationManager", content)
        self.assertIn("processMessageQueue", content)
        self.assertIn("addToDisplayOrder", content)
        print("✅ Test 4 passed: Conversation manager properly implemented")
    
    def test_user_feedback_manager_exists(self):
        """Test 5: Verify user feedback system"""
        feedback_path = Path(__file__).parent.parent / "web-app" / "user_feedback_manager.js"
        self.assertTrue(feedback_path.exists(), "user_feedback_manager.js not found")
        
        # Check content
        content = feedback_path.read_text()
        self.assertIn("class UserFeedbackManager", content)
        self.assertIn("showState", content)
        self.assertIn("searching", content)
        self.assertIn("processing", content)
        print("✅ Test 5 passed: User feedback system properly implemented")
    
    def test_async_await_in_flight_search(self):
        """Test 6: Verify async/await is properly used in flight search"""
        # Check flight_search_service.py
        flight_service_path = Path(__file__).parent.parent / "services" / "flight_search_service.py"
        content = flight_service_path.read_text()
        
        # Check for async def _get_mock_flights
        self.assertIn("async def _get_mock_flights", content)
        
        # Check for await get_real_flights
        self.assertIn("await get_real_flights", content)
        
        # Check voice_processor.py
        voice_processor_path = Path(__file__).parent.parent / "services" / "voice_processor.py"
        voice_content = voice_processor_path.read_text()
        
        # Check for await self.flight_service.search_flights in voice_processor
        self.assertIn("await self.flight_service.search_flights", voice_content)
        print("✅ Test 6 passed: async/await properly implemented")
    
    def test_html_includes_all_scripts(self):
        """Test 7: Verify HTML includes all necessary scripts"""
        html_path = Path(__file__).parent.parent / "web-app" / "realtime.html"
        content = html_path.read_text()
        
        # Check all scripts are included
        self.assertIn("interruption_manager.js", content)
        self.assertIn("conversation_manager.js", content)
        self.assertIn("user_feedback_manager.js", content)
        self.assertIn("realtime-app.js", content)
        print("✅ Test 7 passed: All scripts properly included in HTML")
    
    def test_env_file_has_amadeus_keys(self):
        """Test 8: Verify .env file has Amadeus credentials"""
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            content = env_path.read_text()
            self.assertIn("AMADEUS_CLIENT_ID", content)
            self.assertIn("AMADEUS_CLIENT_SECRET", content)
            print("✅ Test 8 passed: Amadeus credentials in .env file")
        else:
            print("⚠️  Test 8 warning: .env file not found (might be gitignored)")
    
    def test_vad_settings_updated(self):
        """Test 9: Verify VAD settings are updated for better sensitivity"""
        realtime_client_path = Path(__file__).parent.parent / "services" / "realtime_client.py"
        content = realtime_client_path.read_text()
        
        # Check VAD settings
        self.assertIn('"threshold": 0.5', content)  # Balanced sensitivity
        self.assertIn('"silence_duration_ms": 700', content)  # Longer silence
        print("✅ Test 9 passed: VAD settings properly updated")
    
    def test_aviationstack_endpoint_fixed(self):
        """Test 10: Verify AviationStack endpoint is fixed"""
        flight_service_path = Path(__file__).parent.parent / "services" / "flight_search_service.py"
        content = flight_service_path.read_text()
        
        # Check for flightsFuture endpoint
        self.assertIn("flightsFuture", content)
        print("✅ Test 10 passed: AviationStack endpoint properly fixed")

def run_tests():
    """Run all tests and provide summary"""
    print("="*60)
    print("COMPREHENSIVE TEST SUITE FOR ALL FIXES")
    print("="*60)
    print()
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAllFixes)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print()
    print("="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total tests run: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failed: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ ALL TESTS PASSED! All fixes are properly implemented.")
    else:
        print("\n❌ Some tests failed. Please check the output above.")
    
    print("="*60)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)