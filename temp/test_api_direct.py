"""Test API endpoint directly to see what's happening."""
import requests
import json

print("=" * 60)
print("Testing Parser Service API Directly")
print("=" * 60)

# Test parse endpoint
url = "http://127.0.0.1:9003/parse"
data = {
    "keyword": "кирпич",
    "max_urls": 5,
    "source": "google"
}

print(f"\n[1] Sending POST request to {url}")
print(f"Data: {json.dumps(data, ensure_ascii=False)}")

try:
    response = requests.post(url, json=data, timeout=120)
    print(f"\n[2] Response status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"[SUCCESS] Parsing completed!")
        print(f"Found {result.get('total_found', 0)} suppliers")
        if result.get('suppliers'):
            print(f"\nFirst supplier: {result['suppliers'][0]}")
    else:
        print(f"[ERROR] Status {response.status_code}")
        print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"[ERROR] Exception: {e}")
    import traceback
    traceback.print_exc()

