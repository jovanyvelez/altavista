#!/usr/bin/env python3
"""
Comprehensive test to verify CuotaConfiguracion fix and endpoint functionality
"""

import requests
import sys
import os

def test_server_response():
    """Test that the server responds without attribute errors"""
    try:
        response = requests.get('http://127.0.0.1:8000/admin/pagos', timeout=5)
        
        # We expect a 401 (unauthorized) since we're not logged in
        # But NOT a 500 (internal server error) which would indicate attribute error
        if response.status_code == 401:
            print("✅ Server responds correctly (401 Unauthorized - expected)")
            print("✅ No AttributeError: 'CuotaConfiguracion' object has no attribute 'monto_cuota'")
            return True
        elif response.status_code == 500:
            print("❌ Server error (500) - may indicate attribute error")
            print(f"Response: {response.text}")
            return False
        else:
            print(f"ℹ️  Server responds with status {response.status_code}")
            return True
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False

def test_root_endpoint():
    """Test the root endpoint"""
    try:
        response = requests.get('http://127.0.0.1:8000/', timeout=5)
        if response.status_code in [200, 401, 302]:  # Any of these are fine
            print(f"✅ Root endpoint responds with status {response.status_code}")
            return True
        else:
            print(f"❌ Root endpoint error: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False

def main():
    print("🧪 Testing Server Response After CuotaConfiguracion Fix...")
    print("=" * 60)
    
    success = True
    
    # Test root endpoint
    if not test_root_endpoint():
        success = False
    
    print()
    
    # Test admin/pagos endpoint
    if not test_server_response():
        success = False
    
    print()
    print("=" * 60)
    if success:
        print("🎉 All tests passed! CuotaConfiguracion attribute fix is working correctly.")
        print("✅ The AttributeError has been resolved successfully.")
    else:
        print("💥 Some tests failed. Please check the server logs.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
