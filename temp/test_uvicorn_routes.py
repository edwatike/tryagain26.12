"""Test script to check if routes are registered when running through uvicorn."""
import asyncio
from fastapi.testclient import TestClient
from app.main import app

# Check routes before uvicorn
print("=== Routes before uvicorn ===")
from fastapi.routing import APIRoute
routes = [r for r in app.routes if isinstance(r, APIRoute)]
inn_routes = [r for r in routes if 'inn' in r.path.lower()]
print(f"Total routes: {len(routes)}")
print(f"INN routes: {[r.path for r in inn_routes]}")

# Test with TestClient
print("\n=== Testing with TestClient ===")
client = TestClient(app)
response = client.get("/debug/all-routes")
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Total routes in response: {data.get('total_routes', 'N/A')}")
    print(f"INN routes in response: {len(data.get('inn_routes', []))}")

# Test INN extraction endpoint
print("\n=== Testing INN extraction endpoint ===")
response = client.post("/inn-extraction/extract-batch", json={"domains": ["test.com"]})
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:200]}")

