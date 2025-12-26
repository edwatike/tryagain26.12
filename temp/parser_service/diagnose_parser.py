"""Diagnostic script for parser service issues."""
import sys
import os
import subprocess
import requests
import json

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def check_chrome_cdp():
    """Check if Chrome CDP is accessible."""
    print("\n=== Checking Chrome CDP ===")
    try:
        response = requests.get("http://127.0.0.1:9222/json/version", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Chrome CDP is running")
            print(f"     Browser: {data.get('Browser', 'Unknown')}")
            print(f"     WebSocket URL: {data.get('webSocketDebuggerUrl', 'N/A')}")
            return True
        else:
            print(f"[FAIL] Chrome CDP returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("[FAIL] Cannot connect to Chrome CDP on port 9222")
        print("       Chrome is not running in debug mode")
        return False
    except Exception as e:
        print(f"[FAIL] Error checking Chrome CDP: {e}")
        return False

def check_parser_service():
    """Check if parser service is running."""
    print("\n=== Checking Parser Service ===")
    try:
        response = requests.get("http://127.0.0.1:9003/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Parser Service is running")
            print(f"     Status: {data.get('status', 'Unknown')}")
            return True
        else:
            print(f"[FAIL] Parser Service returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("[FAIL] Cannot connect to Parser Service on port 9003")
        print("       Parser Service is not running")
        return False
    except Exception as e:
        print(f"[FAIL] Error checking Parser Service: {e}")
        return False

def check_ports():
    """Check which processes are using ports 9222 and 9003."""
    print("\n=== Checking Ports ===")
    try:
        # Check port 9222
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            timeout=5
        )
        lines_9222 = [line for line in result.stdout.split('\n') if ':9222' in line and 'LISTENING' in line]
        if lines_9222:
            print(f"[OK] Port 9222 is in use (Chrome CDP)")
            for line in lines_9222[:3]:  # Show first 3
                print(f"     {line.strip()}")
        else:
            print("[FAIL] Port 9222 is not in use")
        
        # Check port 9003
        lines_9003 = [line for line in result.stdout.split('\n') if ':9003' in line and 'LISTENING' in line]
        if lines_9003:
            print(f"[OK] Port 9003 is in use (Parser Service)")
            for line in lines_9003[:3]:  # Show first 3
                print(f"     {line.strip()}")
        else:
            print("[FAIL] Port 9003 is not in use")
            
    except Exception as e:
        print(f"[FAIL] Error checking ports: {e}")

def test_parser_connection():
    """Test parser service connection to Chrome CDP."""
    print("\n=== Testing Parser Connection to Chrome ===")
    try:
        # Try a simple parse request
        payload = {"keyword": "test", "max_urls": 1}
        response = requests.post(
            "http://127.0.0.1:9003/parse",
            json=payload,
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Parser can connect to Chrome and parse")
            print(f"     Found {data.get('total_found', 0)} suppliers")
            return True
        else:
            print(f"[FAIL] Parser returned status {response.status_code}")
            try:
                error_data = response.json()
                print(f"     Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"     Response: {response.text[:200]}")
            return False
    except requests.exceptions.Timeout:
        print("[FAIL] Parser request timed out (may indicate Chrome connection issue)")
        return False
    except Exception as e:
        print(f"[FAIL] Error testing parser: {e}")
        return False

def main():
    """Run all diagnostics."""
    print("=" * 60)
    print("Parser Service Diagnostic Tool")
    print("=" * 60)
    
    chrome_ok = check_chrome_cdp()
    parser_ok = check_parser_service()
    check_ports()
    
    if chrome_ok and parser_ok:
        test_parser_connection()
    
    print("\n" + "=" * 60)
    print("Diagnostics complete")
    print("=" * 60)
    
    if not chrome_ok:
        print("\n[ACTION REQUIRED] Chrome is not running in debug mode")
        print("                 Run: start-chrome.bat")
    
    if not parser_ok:
        print("\n[ACTION REQUIRED] Parser Service is not running")
        print("                 Run: start-parser.bat")

if __name__ == "__main__":
    main()

