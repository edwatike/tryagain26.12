"""Comprehensive test script for INN extraction on real domains from database."""
import asyncio
import httpx
import json
import sys
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select, func
from app.config import settings
from app.adapters.db.repositories import DomainQueueRepository, ModeratorSupplierRepository
from app.adapters.db.models import DomainQueueModel, ModeratorSupplierModel


# Database setup
engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_domains_from_db(limit: int = 20) -> List[str]:
    """Get domains from database for testing.
    
    Args:
        limit: Maximum number of domains to return
        
    Returns:
        List of unique domain names
    """
    async with AsyncSessionLocal() as session:
        domains = set()
        
        # Get domains from domains_queue
        repo_queue = DomainQueueRepository(session)
        queue_domains, _ = await repo_queue.list(limit=limit, offset=0)
        for entry in queue_domains:
            if entry.domain:
                domains.add(entry.domain)
        
        # Get domains from moderator_suppliers (that don't have INN yet)
        repo_suppliers = ModeratorSupplierRepository(session)
        suppliers, _ = await repo_suppliers.list(limit=limit, offset=0)
        for supplier in suppliers:
            if supplier.domain and not supplier.inn:
                domains.add(supplier.domain)
        
        # Convert to list and limit
        domain_list = list(domains)[:limit]
        print(f"[INFO] Found {len(domain_list)} unique domains from database")
        return domain_list


async def test_inn_extraction(domains: List[str]) -> Dict[str, Any]:
    """Test INN extraction for list of domains.
    
    Args:
        domains: List of domain names to test
        
    Returns:
        Dict with test results
    """
    base_url = "http://127.0.0.1:8000"
    endpoint = "/inn-extraction/extract-batch"
    
    print(f"\n[TEST] Testing INN extraction for {len(domains)} domains")
    print(f"Endpoint: {base_url}{endpoint}")
    print(f"Domains: {domains[:5]}{'...' if len(domains) > 5 else ''}")
    
    results = {
        "total": len(domains),
        "successful": 0,
        "not_found": 0,
        "errors": 0,
        "domain_results": []
    }
    
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{base_url}{endpoint}",
                json={"domains": domains}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                results["processed"] = data.get("processed", 0)
                results["successful"] = data.get("successful", 0)
                results["notFound"] = data.get("notFound", 0)
                results["failed"] = data.get("failed", 0)
                
                print(f"\n[RESULTS]")
                print(f"  Processed: {results['processed']}")
                print(f"  Successful (INN found): {results['successful']}")
                print(f"  Not Found: {results['notFound']}")
                print(f"  Failed: {results['failed']}")
                
                # Analyze each domain result
                for result in data.get("results", []):
                    domain = result.get("domain")
                    status = result.get("status")
                    inn = result.get("inn")
                    proof = result.get("proof")
                    error = result.get("error")
                    processing_time = result.get("processingTime", 0)
                    
                    domain_result = {
                        "domain": domain,
                        "status": status,
                        "inn": inn,
                        "has_proof": proof is not None,
                        "proof_context": proof.get("context") if proof else None,
                        "proof_method": proof.get("method") if proof else None,
                        "proof_confidence": proof.get("confidence") if proof else None,
                        "error": error,
                        "processing_time_ms": processing_time
                    }
                    
                    results["domain_results"].append(domain_result)
                    
                    # Count by status
                    if status == "success":
                        results["successful"] += 1
                    elif status == "not_found":
                        results["not_found"] += 1
                    elif status == "error":
                        results["errors"] += 1
                    
                    # Print result
                    if inn:
                        print(f"  [OK] {domain}: INN={inn}, method={proof.get('method') if proof else 'N/A'}, confidence={proof.get('confidence') if proof else 'N/A'}")
                    elif status == "not_found":
                        print(f"  [NOT FOUND] {domain}: INN not found")
                    else:
                        print(f"  [ERROR] {domain}: Error - {error}")
                
            else:
                print(f"[ERROR] Endpoint returned status {response.status_code}")
                print(f"Response: {response.text[:500]}")
                results["error"] = f"HTTP {response.status_code}: {response.text[:200]}"
                
    except httpx.ConnectError:
        print(f"[ERROR] Cannot connect to {base_url}")
        print("Make sure Backend is running!")
        results["error"] = "Connection error"
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")
        results["error"] = str(e)
    
    return results


async def analyze_logs(domain: str, log_dir: Path = Path("logs")) -> Dict[str, Any]:
    """Analyze logs for specific domain.
    
    Args:
        domain: Domain name to analyze
        log_dir: Directory with log files
        
    Returns:
        Dict with log analysis
    """
    analysis = {
        "domain": domain,
        "backend_logs": [],
        "parser_logs": [],
        "ollama_logs": []
    }
    
    if not log_dir.exists():
        return analysis
    
    # Find latest log files
    backend_logs = list(log_dir.glob("Backend-*.log"))
    parser_logs = list(log_dir.glob("Parser Service-*.log"))
    ollama_logs = list(log_dir.glob("Ollama Service-*.log"))
    
    # Get most recent logs
    backend_log = max(backend_logs, key=lambda p: p.stat().st_mtime) if backend_logs else None
    parser_log = max(parser_logs, key=lambda p: p.stat().st_mtime) if parser_logs else None
    ollama_log = max(ollama_logs, key=lambda p: p.stat().st_mtime) if ollama_logs else None
    
    # Read last 100 lines from each log
    for log_file, key in [(backend_log, "backend_logs"), (parser_log, "parser_logs"), (ollama_log, "ollama_logs")]:
        if log_file:
            try:
                with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                    # Filter lines related to this domain
                    domain_lines = [line for line in lines[-200:] if domain.lower() in line.lower()]
                    analysis[key] = domain_lines[-20:]  # Last 20 relevant lines
            except Exception as e:
                analysis[key] = [f"Error reading log: {e}"]
    
    return analysis


async def check_extraction_quality(result: Dict[str, Any]) -> Dict[str, Any]:
    """Check quality of INN extraction result.
    
    Args:
        result: Domain extraction result
        
    Returns:
        Dict with quality assessment
    """
    proof_context = result.get("proof_context") or ""
    quality = {
        "has_inn": result.get("inn") is not None,
        "has_proof": result.get("has_proof", False),
        "has_context": bool(proof_context),
        "context_length": len(proof_context),
        "method": result.get("proof_method"),
        "confidence": result.get("proof_confidence"),
        "issues": []
    }
    
    if quality["has_inn"]:
        if not quality["has_proof"]:
            quality["issues"].append("INN found but no proof provided")
        if not quality["has_context"]:
            quality["issues"].append("INN found but no context in proof")
        elif quality["context_length"] < 20:
            quality["issues"].append(f"Context too short ({quality['context_length']} chars)")
        
        if quality["method"] == "regex":
            quality["issues"].append("Used regex instead of Ollama model")
        elif quality["method"] == "ollama" and quality["confidence"] == "low":
            quality["issues"].append("Low confidence from Ollama model")
    else:
        if result.get("status") == "not_found":
            quality["issues"].append("INN not found - may need to check if it exists on page")
        elif result.get("status") == "error":
            quality["issues"].append(f"Error during extraction: {result.get('error')}")
    
    return quality


async def main():
    """Main test function."""
    print("=" * 80)
    print("COMPREHENSIVE INN EXTRACTION TEST")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get domains from database
    print("\n[STEP 1] Getting domains from database...")
    try:
        domains = await get_domains_from_db(limit=10)  # Start with 10 domains for testing
        if not domains:
            print("[WARNING] No domains found in database. Using test domains.")
            domains = ["cement53.ru", "cement-snab.ru"]  # Fallback test domains
    except Exception as e:
        print(f"[ERROR] Failed to get domains from database: {e}")
        print("[INFO] Using fallback test domains")
        domains = ["cement53.ru", "cement-snab.ru"]
    
    if not domains:
        print("[ERROR] No domains to test!")
        return
    
    # Test INN extraction
    print("\n[STEP 2] Testing INN extraction...")
    test_results = await test_inn_extraction(domains)
    
    # Analyze results
    print("\n[STEP 3] Analyzing results...")
    quality_report = []
    for domain_result in test_results.get("domain_results", []):
        quality = await check_extraction_quality(domain_result)
        quality_report.append({
            "domain": domain_result["domain"],
            "quality": quality
        })
        
        if quality["issues"]:
            print(f"  [WARNING] {domain_result['domain']}: {', '.join(quality['issues'])}")
    
    # Analyze logs for failed extractions
    print("\n[STEP 4] Analyzing logs for failed extractions...")
    failed_domains = [
        r["domain"] for r in test_results.get("domain_results", [])
        if r.get("status") != "success"
    ]
    
    if failed_domains:
        print(f"  Analyzing logs for {len(failed_domains)} failed domains...")
        for domain in failed_domains[:5]:  # Limit to first 5
            log_analysis = await analyze_logs(domain)
            if log_analysis.get("backend_logs") or log_analysis.get("parser_logs"):
                print(f"  ✓ Found logs for {domain}")
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total domains tested: {test_results.get('total', 0)}")
    print(f"Successful (INN found): {test_results.get('successful', 0)}")
    print(f"Not found: {test_results.get('not_found', 0)}")
    print(f"Errors: {test_results.get('errors', 0)}")
    
    # Quality summary
    quality_issues_count = sum(len(q["quality"]["issues"]) for q in quality_report)
    if quality_issues_count > 0:
        print(f"\nQuality issues found: {quality_issues_count}")
        print("Review individual domain results above for details.")
    
    # Save report
    report = {
        "test_date": datetime.now().isoformat(),
        "domains_tested": domains,
        "test_results": test_results,
        "quality_report": quality_report,
        "summary": {
            "total": test_results.get("total", 0),
            "successful": test_results.get("successful", 0),
            "not_found": test_results.get("not_found", 0),
            "errors": test_results.get("errors", 0),
            "quality_issues": quality_issues_count
        }
    }
    
    report_file = Path("temp/inn_extraction_test_report.json")
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n[INFO] Test report saved to: {report_file}")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Return success status
    success_rate = (test_results.get("successful", 0) / test_results.get("total", 1)) * 100
    print(f"\nSuccess rate: {success_rate:.1f}%")
    
    if success_rate < 50:
        print("\n[WARNING] Low success rate. Review logs and improve extraction logic.")
        return 1
    else:
        print("\n[OK] Test completed successfully.")
        return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

