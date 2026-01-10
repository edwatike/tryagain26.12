"""Test script for INN extraction endpoint."""
import asyncio
import httpx
import json


async def test_inn_extraction_endpoint():
    """Test the INN extraction endpoint."""
    print("=" * 60)
    print("Testing INN Extraction Endpoint")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:8000"
    endpoint = "/inn-extraction/extract-batch"
    
    # Test data
    test_domains = ["example.com", "test.ru"]
    
    print(f"\n[TEST] Testing endpoint: {base_url}{endpoint}")
    print(f"Test domains: {test_domains}")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{base_url}{endpoint}",
                json={"domains": test_domains}
            )
            
            print(f"\n[RESULT] Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"[OK] Endpoint works!")
                print(f"Response structure:")
                print(f"  - Total: {data.get('total')}")
                print(f"  - Processed: {data.get('processed')}")
                print(f"  - Successful: {data.get('successful')}")
                print(f"  - Failed: {data.get('failed')}")
                print(f"  - Not Found: {data.get('notFound')}")
                print(f"\nResults:")
                for result in data.get("results", []):
                    print(f"  - {result.get('domain')}: {result.get('status')} - INN: {result.get('inn')}")
                    if result.get("proof"):
                        print(f"    Proof: {result['proof'].get('url')} - {result['proof'].get('method')}")
            else:
                print(f"[FAIL] Endpoint returned error: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                
    except httpx.ConnectError:
        print(f"[ERROR] Cannot connect to {base_url}")
        print("Make sure Backend is running!")
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(test_inn_extraction_endpoint())





