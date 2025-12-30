"""Test parsing to verify only one tab opens."""
import requests
import json
import time

# Test parsing with source=google (should open 1 tab)
print("Testing parsing with source=google (should open 1 tab)...")
response = requests.post(
    "http://127.0.0.1:8000/parsing/start",
    json={"keyword": "тест", "depth": 1, "source": "google"},
    headers={"Content-Type": "application/json; charset=utf-8"}
)
print(f"Response status: {response.status_code}")
if response.status_code == 201:
    data = response.json()
    print(f"Run ID: {data.get('runId')}")
    print("Waiting 10 seconds for parsing to start...")
    time.sleep(10)
    print("Check browser tabs - should be only 1 Google tab")
else:
    print(f"Error: {response.text}")







