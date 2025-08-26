#!/usr/bin/env python3
"""
Test script for Aviation Standing Data API
Runs basic tests against the API endpoints to verify functionality
"""

import requests
import json
import time
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:30000"

def test_endpoint(endpoint: str, expected_keys: list = None, params: Dict[str, Any] = None) -> bool:
    """Test a single API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    try:
        print(f"Testing {endpoint}...", end=" ")
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if response is a list
            if isinstance(data, list):
                if len(data) > 0:
                    # Check if first item has expected keys
                    if expected_keys:
                        first_item = data[0]
                        missing_keys = [key for key in expected_keys if key not in first_item]
                        if missing_keys:
                            print(f"❌ Missing keys: {missing_keys}")
                            return False
                    print(f"✅ ({len(data)} items)")
                    return True
                else:
                    print("⚠️  Empty response")
                    return True
            else:
                # Non-list response (like health check)
                print("✅ Success")
                return True
        else:
            print(f"❌ Status {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed")
        return False
    except requests.exceptions.Timeout:
        print("❌ Timeout")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def wait_for_service(max_wait: int = 60) -> bool:
    """Wait for the service to be available"""
    print(f"Waiting for service at {BASE_URL}...", end="")
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                print(" ✅ Service is ready!")
                return True
        except:
            pass
        print(".", end="", flush=True)
        time.sleep(2)
    
    print(" ❌ Service not ready after {max_wait} seconds")
    return False

def main():
    """Run all API tests"""
    print("🧪 Aviation Standing Data API Test Suite")
    print("=" * 50)
    
    # Wait for service to be ready
    if not wait_for_service():
        sys.exit(1)
    
    tests = [
        # Basic endpoints
        ("/health", None),
        
        # Data endpoints with expected keys
        ("/countries", ["ISO", "Name"]),
        ("/airlines", ["Code", "Name", "ICAO", "IATA"]),
        
        # Search endpoints with parameters
        ("/aircraft", ["ICAO", "Registration"], {"limit": "5"}),
        ("/airports", ["Code", "Name"], {"limit": "5"}),
        ("/routes", ["Callsign", "Code"], {"limit": "5"}),
        ("/model-types", ["ICAO", "Manufacturer"], None),
        
        # Specific searches
        ("/aircraft", ["ICAO", "Registration"], {"icao": "40", "limit": "3"}),
        ("/airports", ["Code", "Name"], {"country": "US", "limit": "3"}),
        ("/airports", ["Code", "Name"], {"icao": "EGLL", "limit": "3"}),
        ("/airports", ["Code", "Name"], {"iata": "LHR", "limit": "3"}),
        ("/airlines", ["Code", "Name"], None),
    ]
    
    print("\n🔍 Running endpoint tests:")
    passed = 0
    total = len(tests)
    
    for endpoint, expected_keys, params in tests:
        if test_endpoint(endpoint, expected_keys, params):
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! API is working correctly.")
        
        print("\n💡 Sample queries to try:")
        print(f"   curl '{BASE_URL}/aircraft?registration=VP&limit=3'")
        print(f"   curl '{BASE_URL}/airports?country=GB&limit=5'")
        print(f"   curl '{BASE_URL}/airports?icao=EGLL'")
        print(f"   curl '{BASE_URL}/airports?iata=LHR'")
        print(f"   curl '{BASE_URL}/airports?code=LHR'")
        print(f"   curl '{BASE_URL}/airlines' | jq '.[] | select(.ICAO==\"BAW\")'")
        print(f"   curl '{BASE_URL}/routes?airline_code=EZY&limit=3'")
        
    else:
        print("❌ Some tests failed. Check the API logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()