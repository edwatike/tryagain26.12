"""Test uvicorn direct startup."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import uvicorn
from app.main import app

# Check routes before starting
from fastapi.routing import APIRoute
routes = [r for r in app.routes if isinstance(r, APIRoute)]
inn_routes = [r for r in routes if 'inn' in r.path.lower()]
print(f"Routes before uvicorn: {len(routes)}")
print(f"INN routes: {[r.path for r in inn_routes]}")

# Start uvicorn in a way that we can test
print("\nStarting uvicorn...")
print("Note: This will start the server. Press Ctrl+C to stop.")

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8002,  # Different port to avoid conflicts
        log_level="info"
    )

