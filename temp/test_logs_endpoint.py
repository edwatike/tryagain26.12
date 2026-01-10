"""Test script for logs endpoint."""
import requests
import json
import time

# Test 1: Create a parsing run
print("=== Test 1: Create parsing run ===")
r = requests.post('http://127.0.0.1:8000/parsing/start', json={'keyword': 'test', 'depth': 1, 'source': 'google'})
data = r.json()
run_id = data.get('runId')
print(f'Run ID: {run_id}')
print(f'Status: {data.get("status")}')

time.sleep(2)

# Test 2: Try to get logs
print("\n=== Test 2: Get logs ===")
logs_r = requests.get(f'http://127.0.0.1:8000/parsing/runs/{run_id}/logs')
print(f'GET /parsing/runs/{run_id}/logs status: {logs_r.status_code}')
if logs_r.status_code == 200:
    print('SUCCESS! Response:', json.dumps(logs_r.json(), indent=2))
else:
    print('FAILED! Response:', logs_r.text[:300])

# Test 3: Try to update logs
print("\n=== Test 3: Update logs ===")
put_r = requests.put(
    f'http://127.0.0.1:8000/parsing/runs/{run_id}/logs',
    json={'parsing_logs': {'google': {'total_links': 5, 'pages_processed': 1, 'last_links': ['http://test.com']}}}
)
print(f'PUT /parsing/runs/{run_id}/logs status: {put_r.status_code}')
if put_r.status_code == 200:
    print('SUCCESS! Response:', json.dumps(put_r.json(), indent=2))
else:
    print('FAILED! Response:', put_r.text[:300])

# Test 4: Get logs again after update
print("\n=== Test 4: Get logs after update ===")
get_r2 = requests.get(f'http://127.0.0.1:8000/parsing/runs/{run_id}/logs')
print(f'GET /parsing/runs/{run_id}/logs status: {get_r2.status_code}')
if get_r2.status_code == 200:
    result = get_r2.json()
    print('SUCCESS! Response:', json.dumps(result, indent=2))
    if result.get('parsing_logs'):
        print('\n✅ Logs endpoint is working!')
    else:
        print('\n⚠️ Endpoint works but logs are empty')
else:
    print('FAILED! Response:', get_r2.text[:300])











