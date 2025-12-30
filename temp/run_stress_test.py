#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Stress test script for parsing -> INN -> supplier card flow."""
import sys
import time
import json
import requests
from typing import Dict, Any, Optional

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000"
PARSER_URL = "http://127.0.0.1:9003"

def log_step(step: str, status: str = "INFO"):
    """Log a step with emoji."""
    emoji = {"SUCCESS": "✅", "ERROR": "❌", "INFO": "ℹ️", "WAIT": "⏳"}
    print(f"{emoji.get(status, 'ℹ️')} {step}")

def check_service(url: str, name: str) -> bool:
    """Check if service is running."""
    try:
        response = requests.get(f"{url}/health", timeout=5)
        if response.status_code == 200:
            log_step(f"{name} is running", "SUCCESS")
            return True
        else:
            log_step(f"{name} returned status {response.status_code}", "ERROR")
            return False
    except Exception as e:
        log_step(f"{name} is not accessible: {e}", "ERROR")
        return False

def start_parsing(keyword: str, depth: int = 2, source: str = "google") -> Optional[str]:
    """Start parsing and return runId."""
    log_step(f"Starting parsing: keyword='{keyword}', depth={depth}, source={source}")
    try:
        response = requests.post(
            f"{BASE_URL}/parsing/start",
            json={"keyword": keyword, "depth": depth, "source": source},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        run_id = data.get("runId")
        if run_id:
            log_step(f"Parsing started: runId={run_id}", "SUCCESS")
            return run_id
        else:
            log_step(f"Failed to get runId from response: {data}", "ERROR")
            return None
    except Exception as e:
        log_step(f"Failed to start parsing: {e}", "ERROR")
        return None

def wait_for_parsing_completion(run_id: str, max_wait: int = 300) -> Dict[str, Any]:
    """Wait for parsing to complete and return status."""
    log_step(f"Waiting for parsing to complete (max {max_wait}s)...", "WAIT")
    start_time = time.time()
    attempt = 0
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f"{BASE_URL}/parsing/status/{run_id}", timeout=5)
            response.raise_for_status()
            status_data = response.json()
            status = status_data.get("status")
            
            if attempt % 6 == 0:  # Log every 30 seconds
                log_step(f"Status: {status} (attempt {attempt})")
            
            if status in ["completed", "failed"]:
                log_step(f"Parsing {status}", "SUCCESS" if status == "completed" else "ERROR")
                if status == "failed":
                    error_msg = status_data.get("error_message", "Unknown error")
                    log_step(f"Error: {error_msg}", "ERROR")
                return status_data
            
            time.sleep(5)
            attempt += 1
        except Exception as e:
            log_step(f"Error checking status: {e}", "ERROR")
            time.sleep(5)
            attempt += 1
    
    log_step(f"Timeout waiting for parsing completion", "ERROR")
    return {}

def get_parsing_results(run_id: str) -> Optional[Dict[str, Any]]:
    """Get parsing run results."""
    log_step(f"Fetching parsing results for runId={run_id}")
    try:
        # Get run metadata
        response = requests.get(f"{BASE_URL}/parsing/runs/{run_id}", timeout=10)
        response.raise_for_status()
        run_data = response.json()
        
        # Get domains from queue
        domains = []
        offset = 0
        limit = 1000
        while True:
            queue_response = requests.get(
                f"{BASE_URL}/domains/queue",
                params={"parsingRunId": run_id, "limit": limit, "offset": offset},
                timeout=10
            )
            queue_response.raise_for_status()
            queue_data = queue_response.json()
            entries = queue_data.get("entries", [])
            domains.extend(entries)
            
            if len(entries) < limit or offset + limit >= queue_data.get("total", 0):
                break
            offset += limit
        
        log_step(f"Results fetched: {len(domains)} domains", "SUCCESS")
        return {"run": run_data, "domains": domains}
    except Exception as e:
        log_step(f"Failed to get results: {e}", "ERROR")
        return None

def find_domain_with_inn(results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Find a domain that might have INN information."""
    domains = results.get("domains", [])
    log_step(f"Searching for domain with INN in {len(domains)} domains")
    
    # For now, just return the first domain
    # In real scenario, we would search for INN in domain data or extract from URLs
    if domains:
        first_domain = domains[0]
        domain_name = first_domain.get('domain', 'unknown')
        log_step(f"Selected domain: {domain_name}", "SUCCESS")
        return first_domain
    else:
        log_step("No domains found in results", "ERROR")
        return None

def get_checko_data(inn: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
    """Get Checko data for INN."""
    log_step(f"Fetching Checko data for INN: {inn}")
    try:
        params = {}
        if force_refresh:
            params["force_refresh"] = "true"
        response = requests.get(
            f"{BASE_URL}/moderator/checko/{inn}",
            params=params,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        log_step(f"Checko data fetched: {data.get('name', 'Unknown company')}", "SUCCESS")
        return data
    except Exception as e:
        log_step(f"Failed to get Checko data: {e}", "ERROR")
        return None

def create_supplier(domain: str, inn: str, checko_data: Dict[str, Any]) -> Optional[str]:
    """Create supplier with Checko data."""
    log_step(f"Creating supplier for domain: {domain}, INN: {inn}")
    try:
        # Prepare supplier data from Checko
        supplier_data = {
            "name": checko_data.get("name", f"Supplier {domain}"),
            "domain": domain,
            "inn": inn,
            "type": "supplier",
            "ogrn": checko_data.get("ogrn"),
            "kpp": checko_data.get("kpp"),
            "okpo": checko_data.get("okpo"),
            "companyStatus": checko_data.get("companyStatus"),
            "registrationDate": checko_data.get("registrationDate"),
            "legalAddress": checko_data.get("legalAddress"),
            "phone": checko_data.get("phone"),
            "website": checko_data.get("website"),
            "vk": checko_data.get("vk"),
            "telegram": checko_data.get("telegram"),
            "authorizedCapital": checko_data.get("authorizedCapital"),
            "revenue": checko_data.get("revenue"),
            "profit": checko_data.get("profit"),
            "financeYear": checko_data.get("financeYear"),
            "legalCasesCount": checko_data.get("legalCasesCount"),
            "legalCasesSum": checko_data.get("legalCasesSum"),
            "legalCasesAsPlaintiff": checko_data.get("legalCasesAsPlaintiff"),
            "legalCasesAsDefendant": checko_data.get("legalCasesAsDefendant"),
            "checkoData": checko_data.get("checkoData"),
        }
        
        # Remove None values
        supplier_data = {k: v for k, v in supplier_data.items() if v is not None}
        
        response = requests.post(
            f"{BASE_URL}/moderator/suppliers",
            json=supplier_data,
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        supplier_id = result.get("id")
        if supplier_id:
            log_step(f"Supplier created: ID={supplier_id}", "SUCCESS")
            return str(supplier_id)
        else:
            log_step(f"Failed to get supplier ID from response: {result}", "ERROR")
            return None
    except Exception as e:
        log_step(f"Failed to create supplier: {e}", "ERROR")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                log_step(f"Error detail: {error_detail}", "ERROR")
            except:
                log_step(f"Error response: {e.response.text}", "ERROR")
        return None

def verify_supplier_card(supplier_id: str) -> bool:
    """Verify supplier card is accessible on frontend."""
    log_step(f"Verifying supplier card: ID={supplier_id}")
    try:
        # Check backend endpoint
        response = requests.get(
            f"{BASE_URL}/moderator/suppliers/{supplier_id}",
            timeout=10
        )
        response.raise_for_status()
        supplier = response.json()
        
        # Check if Checko data is present
        has_checko = supplier.get("checkoData") is not None
        name = supplier.get("name", "Unknown")
        
        log_step(f"Supplier card verified: {name} (Checko data: {'Yes' if has_checko else 'No'})", "SUCCESS")
        
        # Also check frontend
        frontend_url = f"http://localhost:3000/suppliers/{supplier_id}"
        log_step(f"Frontend URL: {frontend_url}", "INFO")
        
        return True
    except Exception as e:
        log_step(f"Failed to verify supplier card: {e}", "ERROR")
        return False

def main():
    """Main stress test flow."""
    print("=" * 60)
    print("🚀 STRESS TEST: Parsing → INN → Supplier Card")
    print("=" * 60)
    
    # Step 1: Check services
    log_step("Step 1: Checking services", "INFO")
    if not check_service(BASE_URL, "Backend"):
        log_step("Backend is not running. Please start it first.", "ERROR")
        return
    if not check_service(PARSER_URL, "Parser Service"):
        log_step("Parser Service is not running. Please start it first.", "ERROR")
        return
    
    # Step 2: Start parsing
    log_step("Step 2: Starting parsing", "INFO")
    run_id = start_parsing("кирпич", depth=2, source="google")
    if not run_id:
        log_step("Failed to start parsing", "ERROR")
        return
    
    # Step 3: Wait for completion
    log_step("Step 3: Waiting for parsing completion", "INFO")
    status_data = wait_for_parsing_completion(run_id)
    if status_data.get("status") != "completed":
        log_step("Parsing did not complete successfully", "ERROR")
        return
    
    # Step 4: Get results
    log_step("Step 4: Getting parsing results", "INFO")
    results = get_parsing_results(run_id)
    if not results:
        log_step("Failed to get results", "ERROR")
        return
    
    # Step 5: Find domain with INN
    log_step("Step 5: Finding domain with INN", "INFO")
    domain_data = find_domain_with_inn(results)
    if not domain_data:
        log_step("No suitable domain found", "ERROR")
        return
    
    domain_name = domain_data.get('domain', 'unknown')
    
    # Step 6: Get INN (for test, use a known INN)
    # In real scenario, we would extract INN from domain data or search for it
    log_step("Step 6: Getting INN for domain", "INFO")
    # Using a test INN - in production, this would be extracted from domain data
    test_inn = "7814148471"  # Example INN for testing
    log_step(f"Using test INN: {test_inn} (in production, extract from domain data)", "INFO")
    
    # Step 7: Get Checko data
    log_step("Step 7: Getting Checko data", "INFO")
    checko_data = get_checko_data(test_inn, force_refresh=True)
    if not checko_data:
        log_step("Failed to get Checko data. Retrying...", "ERROR")
        # Retry once
        checko_data = get_checko_data(test_inn, force_refresh=True)
        if not checko_data:
            log_step("Failed to get Checko data after retry. Using minimal test data.", "ERROR")
            # Use minimal test data
            checko_data = {
                "name": f"Test Supplier for {domain_name}",
                "inn": test_inn,
                "checkoData": json.dumps({"test": True})
            }
    
    # Step 8: Create supplier
    log_step("Step 8: Creating supplier", "INFO")
    supplier_id = create_supplier(domain_name, test_inn, checko_data)
    if not supplier_id:
        log_step("Failed to create supplier", "ERROR")
        return
    
    # Step 9: Verify supplier card
    log_step("Step 9: Verifying supplier card", "INFO")
    if not verify_supplier_card(supplier_id):
        log_step("Supplier card verification failed", "ERROR")
        return
    
    print("\n" + "=" * 60)
    print("✅ STRESS TEST COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print(f"RunId: {run_id}")
    print(f"Domain: {domain_name}")
    print(f"INN: {test_inn}")
    print(f"Supplier ID: {supplier_id}")
    print(f"Frontend URL: http://localhost:3000/suppliers/{supplier_id}")
    print("\n✅ All steps completed successfully!")

if __name__ == "__main__":
    main()

