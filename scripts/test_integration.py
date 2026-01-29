import requests
import sys
import os
import time

# Configuration
BASE_URL = "http://localhost:8000"
USERNAME = "testuser_integration"
PASSWORD = "Password123!"
EMAIL = "test_integration@example.com"

def print_pass(message):
    print(f"✅ PASS: {message}")

def print_fail(message):
    print(f"❌ FAIL: {message}")
    sys.exit(1)

def test_health():
    try:
        # Test root endpoint (returns React app or fallback)
        response = requests.get(f"{BASE_URL}/", allow_redirects=False)
        if response.status_code == 200:
            print_pass("Root endpoint returns 200 OK")
        else:
            print_fail(f"Root endpoint returned {response.status_code}")

        # Test health check
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print_pass("Health check passed")
        else:
            print_fail(f"Health check returned {response.status_code}")
            
    except Exception as e:
        print_fail(f"Health check exception: {e}")

def test_auth():
    # Register
    auth_data = {
        "username": USERNAME,
        "password": PASSWORD,
        "email": EMAIL,
        "full_name": "Test User"
    }
    
    # Try login first to see if user exists
    login_data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/token", data=login_data)
    
    if response.status_code == 200:
        print_pass("User already exists, logged in")
        return response.json()["access_token"]
    
    # Register if not exists
    response = requests.post(f"{BASE_URL}/api/auth/register", json=auth_data)
    if response.status_code == 200 or response.status_code == 201:
        print_pass("User registered")
    elif response.status_code == 400 and "already registered" in response.text:
        print_pass("User already registered (handled)")
    else:
        print_fail(f"Registration failed: {response.status_code} {response.text}")
        
    # Login
    response = requests.post(f"{BASE_URL}/api/auth/token", data=login_data)
    if response.status_code == 200:
        print_pass("Login successful")
        return response.json()["access_token"]
    else:
        print_fail(f"Login failed: {response.status_code} {response.text}")

def test_arbitrage(token):
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test arbitrage endpoint
    response = requests.get(f"{BASE_URL}/api/arbitrage", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print_pass(f"Arbitrage endpoint returned {len(data)} opportunities")
    else:
        print_fail(f"Arbitrage endpoint failed: {response.status_code} {response.text}")

def test_live_odds(token):
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test live odds for EPL (example)
    response = requests.get(f"{BASE_URL}/api/odds/live/soccer_epl", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print_pass(f"Live odds endpoint returned {data.get('total_matches', 0)} matches")
    else:
        # 404 or 503 is acceptable if API key is invalid or sport not active, but 500 is fail
        if response.status_code in [404, 503]:
             print_pass(f"Live odds endpoint returned {response.status_code} (expected if sport inactive/no key)")
        else:
            print_fail(f"Live odds endpoint failed: {response.status_code} {response.text}")

if __name__ == "__main__":
    print("🚀 Starting Integration Tests...")
    
    # Wait for server to be ready (optional, but good for CI)
    # time.sleep(2)
    
    test_health()
    token = test_auth()
    test_arbitrage(token)
    test_live_odds(token)
    
    print("🎉 All Integration Tests Passed!")
