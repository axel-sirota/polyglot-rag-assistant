#!/usr/bin/env python3
"""Quick integration test for flight search with real data"""
import asyncio
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import PolyglotRAGOrchestrator

load_dotenv()

async def test_flight_search():
    """Test real flight search through the full pipeline"""
    print("🧪 Testing Flight Search Integration with Real Data\n")
    
    # Initialize orchestrator
    orchestrator = PolyglotRAGOrchestrator()
    await orchestrator.initialize()
    
    # Calculate dates
    next_monday = datetime.now()
    days_until_monday = (7 - next_monday.weekday()) % 7
    if days_until_monday == 0:  # Today is Monday
        days_until_monday = 7
    next_monday = next_monday + timedelta(days=days_until_monday)
    next_month = datetime.now() + timedelta(days=30)
    
    # Test queries with specific dates
    test_queries = [
        {
            "query": f"Find me flights from New York to Paris on {next_monday.strftime('%Y-%m-%d')}",
            "language": "en"
        },
        {
            "query": f"Buscar vuelos de Buenos Aires a Madrid para el {next_month.strftime('%Y-%m-%d')}",
            "language": "es"
        }
    ]
    
    for test in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {test['query']}")
        print(f"Language: {test['language']}")
        print(f"{'='*60}\n")
        
        try:
            # Process the query
            response = await orchestrator.process_text_query(
                test['query'], 
                test['language']
            )
            
            print(f"Response:\n{response}\n")
            
            # Check if we got flight results
            if hasattr(orchestrator, 'last_flight_results') and orchestrator.last_flight_results:
                print(f"✅ Found {len(orchestrator.last_flight_results)} flights!")
                print("\nFirst flight details:")
                flight = orchestrator.last_flight_results[0]
                print(f"  - Airline: {flight.get('airline')}")
                print(f"  - Flight: {flight.get('flight_number')}")
                print(f"  - Price: {flight.get('price')}")
                print(f"  - Duration: {flight.get('duration')}")
            else:
                print("⚠️  No flight results captured")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Cleanup
    await orchestrator.cleanup()
    print("\n✅ Test completed!")

if __name__ == "__main__":
    asyncio.run(test_flight_search())