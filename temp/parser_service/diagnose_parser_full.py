#!/usr/bin/env python3
"""
Полная диагностика Parser Service и всех его компонентов.

Проверяет:
1. Доступность Chrome CDP (порт 9222)
2. Доступность Parser Service (порт 9003)
3. Доступность Backend (порт 8000)
4. Тестовый запрос на парсинг
5. Кодировку запросов (кириллица)
"""
import sys
import os
import json
import requests
import httpx
from pathlib import Path

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_success(message):
    """Print success message."""
    print(f"{Colors.GREEN}[OK]{Colors.RESET} {message}")

def print_error(message):
    """Print error message."""
    print(f"{Colors.RED}[FAIL]{Colors.RESET} {message}")

def print_warning(message):
    """Print warning message."""
    print(f"{Colors.YELLOW}[WARN]{Colors.RESET} {message}")

def print_info(message):
    """Print info message."""
    print(f"{Colors.BLUE}[INFO]{Colors.RESET} {message}")

def check_chrome_cdp():
    """Check if Chrome CDP is accessible."""
    print("\n" + "="*60)
    print("1. Checking Chrome CDP (port 9222)")
    print("="*60)
    
    try:
        response = requests.get("http://127.0.0.1:9222/json/version", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success("Chrome CDP is running")
            print_info(f"Browser: {data.get('Browser', 'Unknown')}")
            print_info(f"Protocol Version: {data.get('Protocol-Version', 'Unknown')}")
            ws_url = data.get('webSocketDebuggerUrl', 'N/A')
            print_info(f"WebSocket URL: {ws_url}")
            
            # Check if it's headless
            user_agent = data.get('User-Agent', '')
            if 'HeadlessChrome' in user_agent:
                print_warning("Chrome is running in HEADLESS mode (may cause issues with CAPTCHA)")
            else:
                print_success("Chrome is running in VISIBLE mode")
            
            return True, ws_url
        else:
            print_error(f"Chrome CDP returned status {response.status_code}")
            return False, None
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to Chrome CDP on port 9222")
        print_info("Please start Chrome with: --remote-debugging-port=9222")
        print_info("Example: chrome.exe --remote-debugging-port=9222 --disable-gpu")
        return False, None
    except requests.exceptions.Timeout:
        print_error("Timeout connecting to Chrome CDP")
        return False, None
    except Exception as e:
        print_error(f"Error checking Chrome CDP: {e}")
        return False, None

def check_parser_service():
    """Check if parser service is running."""
    print("\n" + "="*60)
    print("2. Checking Parser Service (port 9003)")
    print("="*60)
    
    try:
        response = requests.get("http://127.0.0.1:9003/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success("Parser Service is running")
            print_info(f"Status: {data.get('status', 'unknown')}")
            return True
        else:
            print_error(f"Parser Service returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to Parser Service on port 9003")
        print_info("Please start parser service: cd parser_service && python run_api.py")
        return False
    except requests.exceptions.Timeout:
        print_error("Timeout connecting to Parser Service")
        return False
    except Exception as e:
        print_error(f"Error checking Parser Service: {e}")
        return False

def check_backend():
    """Check if backend is running."""
    print("\n" + "="*60)
    print("3. Checking Backend (port 8000)")
    print("="*60)
    
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success("Backend is running")
            print_info(f"Status: {data.get('status', 'unknown')}")
            return True
        else:
            print_error(f"Backend returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_warning("Cannot connect to Backend on port 8000 (optional)")
        return False
    except requests.exceptions.Timeout:
        print_warning("Timeout connecting to Backend (optional)")
        return False
    except Exception as e:
        print_warning(f"Error checking Backend: {e} (optional)")
        return False

def test_parsing_encoding():
    """Test parsing with Cyrillic keyword to check encoding."""
    print("\n" + "="*60)
    print("4. Testing Parsing with Cyrillic Keyword (encoding test)")
    print("="*60)
    
    try:
        # Test with Cyrillic keyword
        test_keyword = "кирпич"
        print_info(f"Testing with keyword: '{test_keyword}'")
        
        # Use httpx to ensure proper encoding
        async def test_parse():
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "http://127.0.0.1:9003/parse",
                    json={
                        "keyword": test_keyword,
                        "max_urls": 2,
                        "source": "yandex"
                    },
                    headers={
                        "Content-Type": "application/json; charset=utf-8"
                    }
                )
                return response
        
        import asyncio
        response = asyncio.run(test_parse())
        
        if response.status_code == 200:
            data = response.json()
            print_success("Parsing request succeeded")
            print_info(f"Keyword received: {data.get('keyword', 'N/A')}")
            print_info(f"Suppliers found: {data.get('total_found', 0)}")
            
            # Check if keyword was received correctly (not mojibake)
            received_keyword = data.get('keyword', '')
            if received_keyword == test_keyword:
                print_success("Encoding is correct (Cyrillic preserved)")
            else:
                print_error(f"Encoding issue: expected '{test_keyword}', got '{received_keyword}'")
            
            return True
        else:
            print_error(f"Parsing request failed with status {response.status_code}")
            try:
                error_detail = response.json()
                print_error(f"Error detail: {error_detail}")
            except:
                print_error(f"Error response: {response.text[:200]}")
            return False
    except httpx.ConnectError:
        print_error("Cannot connect to Parser Service for parsing test")
        return False
    except httpx.TimeoutException:
        print_warning("Parsing test timed out (this is normal for long operations)")
        return False
    except Exception as e:
        print_error(f"Error during parsing test: {e}")
        import traceback
        print_error(f"Traceback: {traceback.format_exc()}")
        return False

def check_integration():
    """Check backend integration with parser service."""
    print("\n" + "="*60)
    print("5. Checking Backend Integration")
    print("="*60)
    
    try:
        # Check if backend can reach parser service
        response = requests.get("http://127.0.0.1:8000/openapi.json", timeout=5)
        if response.status_code == 200:
            openapi = response.json()
            paths = openapi.get('paths', {})
            
            # Check for parsing endpoints
            parsing_paths = [p for p in paths.keys() if 'parsing' in p.lower() or 'parse' in p.lower()]
            if parsing_paths:
                print_success(f"Backend has parsing endpoints: {len(parsing_paths)}")
                for path in parsing_paths[:3]:  # Show first 3
                    print_info(f"  - {path}")
            else:
                print_warning("No parsing endpoints found in backend OpenAPI")
            
            return True
        else:
            print_warning(f"Backend OpenAPI returned status {response.status_code}")
            return False
    except Exception as e:
        print_warning(f"Error checking backend integration: {e}")
        return False

def main():
    """Run full diagnostics."""
    print("\n" + "="*60)
    print("Parser Service Full Diagnostics")
    print("="*60)
    print(f"Platform: {sys.platform}")
    print(f"Python: {sys.version}")
    
    results = {
        'chrome_cdp': False,
        'parser_service': False,
        'backend': False,
        'parsing_test': False,
        'integration': False
    }
    
    # Run all checks
    chrome_ok, ws_url = check_chrome_cdp()
    results['chrome_cdp'] = chrome_ok
    
    parser_ok = check_parser_service()
    results['parser_service'] = parser_ok
    
    backend_ok = check_backend()
    results['backend'] = backend_ok
    
    if parser_ok:
        parsing_ok = test_parsing_encoding()
        results['parsing_test'] = parsing_ok
    else:
        print_warning("Skipping parsing test (Parser Service not available)")
    
    if backend_ok:
        integration_ok = check_integration()
        results['integration'] = integration_ok
    else:
        print_warning("Skipping integration test (Backend not available)")
    
    # Summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for check, result in results.items():
        status = "✓" if result else "✗"
        color = Colors.GREEN if result else Colors.RED
        print(f"{color}{status}{Colors.RESET} {check.replace('_', ' ').title()}")
    
    print(f"\nTotal: {passed}/{total} checks passed")
    
    if passed == total:
        print_success("All checks passed! Parser Service is ready to use.")
        return 0
    elif passed >= total - 1:  # Allow backend to be optional
        print_warning("Most checks passed. Some optional components may be missing.")
        return 0
    else:
        print_error("Some critical checks failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())


















