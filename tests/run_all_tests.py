#!/usr/bin/env python3
"""Run all tests for Polyglot RAG Assistant"""

import asyncio
import subprocess
import sys
from pathlib import Path

async def run_test(test_file):
    """Run a single test file"""
    print(f"\n{'='*60}")
    print(f"Running {test_file.name}")
    print('='*60)
    
    try:
        # Run the test file
        result = subprocess.run(
            [sys.executable, str(test_file)],
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to run {test_file.name}: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Polyglot RAG Assistant - Test Suite")
    print("=" * 60)
    
    # Find all test files
    test_dir = Path(__file__).parent
    test_files = [
        # Core API tests
        test_dir / "test_amadeus_sdk.py",
        test_dir / "test_aviationstack.py", 
        test_dir / "test_browserless.py",
        # Integration tests
        test_dir / "test_apis.py",
        test_dir / "test_voice_pipeline.py",
        test_dir / "test_flight_search.py",
        test_dir / "test_gradio_interface.py",
        # Additional tests
        test_dir / "test_realtime_connection.py",
        test_dir / "test_interruption.py"
    ]
    
    # Run tests
    results = []
    for test_file in test_files:
        if test_file.exists():
            result = await run_test(test_file)
            results.append((test_file.name, result))
    
    # Summary
    print("\n" + "="*60)
    print("📊 FINAL TEST SUMMARY")
    print("="*60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Ready for demo.")
    else:
        print("\n⚠️  Some tests failed. Check your configuration.")

if __name__ == "__main__":
    asyncio.run(main())