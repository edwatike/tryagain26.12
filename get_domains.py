"""Get domains from parsing run."""
import requests
import json

run_id = "a0097613-61ab-4831-8d48-ef9c8cbfac8b"
url = f"http://127.0.0.1:8000/domains/queue?parsingRunId={run_id}&limit=100"

print(f"Fetching domains from: {url}")
response = requests.get(url)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    total = data.get("total", 0)
    entries = data.get("entries", [])
    
    print(f"\nTotal domains: {total}")
    print(f"Fetched: {len(entries)}")
    
    domains = [e["domain"] for e in entries]
    print(f"\nDomains list:")
    for i, domain in enumerate(domains[:20], 1):
        print(f"{i}. {domain}")
    
    # Save to file
    with open("domains_list.txt", "w", encoding="utf-8") as f:
        for domain in domains:
            f.write(f"{domain}\n")
    
    print(f"\n✅ Saved {len(domains)} domains to domains_list.txt")
else:
    print(f"Error: {response.text}")
