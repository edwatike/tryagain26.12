"""Test parser service."""
import requests
import json
import time

print("=" * 60)
print("Testing Parser Service")
print("=" * 60)

# Test health
print("\n[1] Checking health...")
try:
    response = requests.get("http://127.0.0.1:9003/health", timeout=5)
    print(f"Health check: {response.status_code} - {response.json()}")
except Exception as e:
    print(f"Health check failed: {e}")
    exit(1)

# Test parsing
print("\n[2] Starting parsing...")
print("Keyword: кирпич")
print("Max URLs: 10")
print("Source: google")
print("\nThis may take a while (up to 2 minutes)...")

try:
    response = requests.post(
        "http://127.0.0.1:9003/parse",
        json={
            "keyword": "кирпич",
            "max_urls": 20,  # Увеличиваем для получения больше URL
            "source": "google"
        },
        timeout=180  # Увеличиваем timeout до 3 минут
    )
    
    print(f"\nStatus: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nKeyword: {result.get('keyword')}")
        print(f"Total found: {result.get('total_found')}")
        
        suppliers = result.get('suppliers', [])
        print(f"\nSuppliers found: {len(suppliers)}")
        
        if suppliers:
            print("\nFirst 5 suppliers:")
            for i, s in enumerate(suppliers[:5], 1):
                print(f"\n{i}. Name: {s.get('name')}")
                print(f"   URL: {s.get('source_url')}")
                print(f"   Domain: {s.get('domain')}")
                print(f"   Email: {s.get('email')}")
                print(f"   Phone: {s.get('phone')}")
            
            print("\n" + "=" * 60)
            print("SUCCESS: Parser returned URLs!")
            print("=" * 60)
        else:
            print("\nWARNING: No suppliers found")
    else:
        print(f"Error: {response.text}")
        exit(1)
        
except requests.exceptions.Timeout:
    print("\nERROR: Request timed out (120 seconds)")
    exit(1)
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

