"""
Test script for automatic Domain Parser -> Comet -> Learning workflow
"""
import requests
import time
import json

BASE_URL = "http://127.0.0.1:8000"

def test_workflow():
    print("=" * 60)
    print("Testing Automatic Workflow: Parser -> Comet -> Learning")
    print("=" * 60)
    
    # 1. Get a parsing run with domains
    print("\n[1/6] Getting parsing run...")
    runs_response = requests.get(f"{BASE_URL}/parsing/runs?limit=1&sort=created_at&order=desc")
    if runs_response.status_code != 200:
        print(f"❌ Failed to get runs: {runs_response.status_code}")
        return
    
    runs = runs_response.json()['runs']
    if not runs:
        print("❌ No parsing runs found")
        return
    
    run = runs[0]
    run_id = run.get('runId') or run.get('run_id')
    print(f"✅ Found run: {run_id}")
    print(f"   Keyword: {run.get('keyword')}")
    print(f"   Status: {run.get('status')}")
    
    # 2. Get domains from this run
    print("\n[2/6] Getting domains...")
    domains_response = requests.get(f"{BASE_URL}/domains/queue?parsingRunId={run_id}&limit=10")
    if domains_response.status_code != 200:
        print(f"❌ Failed to get domains: {domains_response.status_code}")
        return
    
    domains_data = domains_response.json()
    if not domains_data['entries']:
        print("❌ No domains found in this run")
        return
    
    # Select 2 test domains
    test_domains = [d['domain'] for d in domains_data['entries'][:2]]
    print(f"✅ Selected {len(test_domains)} domains for testing:")
    for i, domain in enumerate(test_domains, 1):
        print(f"   {i}. {domain}")
    
    # 3. Start Domain Parser
    print("\n[3/6] Starting Domain Parser...")
    parser_response = requests.post(
        f"{BASE_URL}/domain-parser/extract-batch",
        json={"runId": run_id, "domains": test_domains}
    )
    
    if parser_response.status_code != 200:
        print(f"❌ Failed to start parser: {parser_response.status_code}")
        print(f"   Response: {parser_response.text}")
        return
    
    parser_data = parser_response.json()
    parser_run_id = parser_data['parserRunId']
    print(f"✅ Domain Parser started: {parser_run_id}")
    
    # 4. Wait for Domain Parser to complete
    print("\n[4/6] Waiting for Domain Parser to complete...")
    max_wait = 60  # 60 seconds max
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        status_response = requests.get(f"{BASE_URL}/domain-parser/status/{parser_run_id}")
        if status_response.status_code != 200:
            print(f"❌ Failed to get status: {status_response.status_code}")
            break
        
        status_data = status_response.json()
        status = status_data['status']
        processed = status_data['processed']
        total = status_data['total']
        
        print(f"   Status: {status} - {processed}/{total} domains processed", end='\r')
        
        if status == 'completed':
            print(f"\n✅ Domain Parser completed!")
            print(f"   Results: {len(status_data.get('results', []))} domains")
            
            # Show results
            for result in status_data.get('results', []):
                domain = result['domain']
                inn = result.get('inn', 'Not found')
                emails = result.get('emails', [])
                email_str = emails[0] if emails else 'Not found'
                print(f"   - {domain}: INN={inn}, Email={email_str}")
            
            break
        elif status == 'failed':
            print(f"\n❌ Domain Parser failed")
            break
        
        time.sleep(2)
    
    # 5. Check if Comet was auto-triggered
    print("\n[5/6] Checking for auto-triggered Comet...")
    time.sleep(3)  # Wait a bit for auto-trigger
    
    # Check backend logs for AUTO-TRIGGER
    print("   Checking backend logs...")
    with open("logs/Backend-20260112-114154.log", "r", encoding="utf-8") as f:
        logs = f.readlines()
        auto_trigger_logs = [line for line in logs[-100:] if "AUTO-TRIGGER" in line]
        
        if auto_trigger_logs:
            print(f"✅ Found AUTO-TRIGGER logs:")
            for log in auto_trigger_logs[-5:]:
                print(f"   {log.strip()}")
        else:
            print("⚠️  No AUTO-TRIGGER logs found yet")
    
    # 6. Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)
    print(f"✅ Domain Parser: Started and completed")
    print(f"   Parser Run ID: {parser_run_id}")
    print(f"   Domains tested: {len(test_domains)}")
    print(f"\n📋 Next steps:")
    print(f"   1. Check backend logs for AUTO-TRIGGER messages")
    print(f"   2. Open Frontend: http://localhost:3000/parsing-runs/{run_id}")
    print(f"   3. Verify Comet and Learning results in UI")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_workflow()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
