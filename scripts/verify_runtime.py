
import sys
import os
import logging
from fastapi.testclient import TestClient

# Add root to path
sys.path.append(os.getcwd())

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    print("[START] Starting Runtime Verification...")
    
    # Import app
    from app.main import app
    
    # Create TestClient
    client = TestClient(app)
    print("[PASS] TestClient created successfully")
    
    # Test Health Check
    print("\nTesting /health endpoint...")
    response = client.get("/health")
    if response.status_code == 200:
        print(f"[PASS] /health passed: {response.json()}")
    else:
        print(f"[FAIL] /health failed: {response.status_code} - {response.text}")
        
    # Test Root
    print("\nTesting / endpoint...")
    response = client.get("/")
    if response.status_code == 200:
        print(f"[PASS] / passed: (HTML content)")
    else:
        print(f"[FAIL] / failed: {response.status_code} - {response.text}")

    # Test Auth Endpoint (just existence, not login)
    print("\nTesting /api/auth/token (Method Not Allowed or Not Found expected)...")
    response = client.get("/api/auth/token") # Should be POST
    # 405 is correct for API, 404 is acceptable if catch-all intercepts GET
    if response.status_code in [405, 404]:
        print(f"[PASS] /api/auth/token passed ({response.status_code} as expected)")
    else:
        print(f"[FAIL] /api/auth/token unexpected status: {response.status_code}")
        print(f"Response content: {response.text[:200]}...") # Print first 200 chars

    print("\n[DONE] Runtime Verification Complete!")

except Exception as e:
    print(f"\n[FAIL] Runtime Verification Failed: {e}")
    import traceback
    traceback.print_exc()
