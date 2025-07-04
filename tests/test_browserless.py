#!/usr/bin/env python3
"""
Test Browserless.io API for web scraping flight data
"""
import asyncio
import httpx
import json
import os
from dotenv import load_dotenv

async def test_browserless():
    """Test Browserless.io for flight search scraping"""
    load_dotenv()
    
    print("🔍 Testing Browserless.io Web Scraping")
    print("=" * 60)
    
    api_key = os.getenv("BROWSERLESS_IO_API_KEY")
    if not api_key:
        print("❌ BROWSERLESS_IO_API_KEY not found in .env")
        return
    
    # Test scraping flight search results from Google Flights
    test_routes = [
        {
            "origin": "JFK",
            "destination": "LAX",
            "date": "2025-08-01",
            "name": "New York to Los Angeles"
        },
        {
            "origin": "LHR",
            "destination": "CDG", 
            "date": "2025-08-15",
            "name": "London to Paris"
        }
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for route in test_routes:
            print(f"\n✈️  Testing: {route['name']}")
            
            # Construct Google Flights URL
            url = f"https://www.google.com/travel/flights/search?tfs=CBwQAhojagcIARIDSkZLEgoyMDI1LTA4LTAxcgcIARIDTEFYGAFwAYIBCwj___________8BQAFIAZgBAg"
            
            # Browserless.io scraping endpoint (use production URL)
            endpoint = f"https://production-sfo.browserless.io/scrape?token={api_key}"
            
            # Scraping configuration
            payload = {
                "url": url,
                "elements": [
                    {
                        "selector": "[data-is-best-flight]",
                        "timeout": 10000
                    }
                ],
                "waitForTimeout": 5000,
                "screenshot": False
            }
            
            try:
                print(f"   Scraping: {url[:50]}...")
                
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("data") and len(data["data"]) > 0:
                        print(f"   ✅ Found {len(data['data'])} flight elements")
                        
                        # Parse first result
                        element = data["data"][0]
                        print(f"   Element HTML preview: {element.get('html', '')[:100]}...")
                    else:
                        print("   ⚠️  No flight data found (may need different selectors)")
                        
                else:
                    print(f"   ❌ Request failed: {response.status_code}")
                    print(f"   Response: {response.text[:200]}")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    # Test PDF generation for flight itinerary
    print("\n\n📄 Testing PDF Generation")
    print("-" * 40)
    
    try:
        endpoint = f"https://production-sfo.browserless.io/pdf?token={api_key}"
        
        # Simple HTML for flight itinerary
        html_content = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                h1 { color: #333; }
                .flight { border: 1px solid #ddd; padding: 20px; margin: 10px 0; }
            </style>
        </head>
        <body>
            <h1>Flight Itinerary</h1>
            <div class="flight">
                <h2>Outbound Flight</h2>
                <p><strong>Flight:</strong> AA100</p>
                <p><strong>From:</strong> JFK - New York</p>
                <p><strong>To:</strong> LAX - Los Angeles</p>
                <p><strong>Date:</strong> August 1, 2025</p>
                <p><strong>Time:</strong> 08:00 - 11:30</p>
            </div>
        </body>
        </html>
        """
        
        payload = {
            "html": html_content,
            "options": {
                "displayHeaderFooter": False,
                "printBackground": True,
                "format": "A4"
            }
        }
        
        response = await client.post(
            endpoint,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("   ✅ PDF generated successfully")
            print(f"   PDF size: {len(response.content)} bytes")
            
            # Save PDF for inspection
            with open("tests/test_itinerary.pdf", "wb") as f:
                f.write(response.content)
            print("   Saved to: tests/test_itinerary.pdf")
        else:
            print(f"   ❌ PDF generation failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test screenshot functionality
    print("\n\n📸 Testing Screenshot Capture")
    print("-" * 40)
    
    try:
        endpoint = f"https://production-sfo.browserless.io/screenshot?token={api_key}"
        
        payload = {
            "url": "https://www.google.com/travel/flights",
            "options": {
                "fullPage": False,
                "type": "png"
            },
            "waitForTimeout": 3000
        }
        
        response = await client.post(
            endpoint,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("   ✅ Screenshot captured successfully")
            print(f"   Image size: {len(response.content)} bytes")
            
            # Save screenshot
            with open("tests/test_flights_screenshot.png", "wb") as f:
                f.write(response.content)
            print("   Saved to: tests/test_flights_screenshot.png")
        else:
            print(f"   ❌ Screenshot failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_browserless())