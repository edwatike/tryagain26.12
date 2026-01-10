"""Start Chrome browser with CDP (Chrome DevTools Protocol) for remote debugging."""
import subprocess
import time
import sys
import os
import logging
import httpx
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Default Chrome CDP port
DEFAULT_CDP_PORT = 9222
DEFAULT_CDP_URL = f"http://127.0.0.1:{DEFAULT_CDP_PORT}"

# Common Chrome executable paths
CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
]


def find_chrome_executable() -> Optional[str]:
    """Find Chrome executable on the system.
    
    Returns:
        Path to Chrome executable or None if not found
    """
    for path in CHROME_PATHS:
        if os.path.exists(path):
            logger.info(f"Found Chrome at: {path}")
            return path
    
    logger.warning("Chrome executable not found in common locations")
    return None


def check_cdp_available(cdp_url: str = DEFAULT_CDP_URL, timeout: int = 5) -> bool:
    """Check if Chrome CDP is already available.
    
    Args:
        cdp_url: Chrome CDP URL
        timeout: Request timeout in seconds
        
    Returns:
        True if CDP is available, False otherwise
    """
    try:
        version_url = f"{cdp_url}/json/version"
        response = httpx.get(version_url, timeout=timeout)
        if response.status_code == 200:
            logger.info(f"Chrome CDP is already available at {cdp_url}")
            return True
    except Exception as e:
        logger.debug(f"Chrome CDP not available: {e}")
    
    return False


def start_chrome_with_cdp(
    chrome_path: Optional[str] = None,
    cdp_port: int = DEFAULT_CDP_PORT,
    user_data_dir: Optional[str] = None,
    wait_for_ready: bool = True,
    max_wait_time: int = 30
) -> bool:
    """Start Chrome browser with CDP enabled.
    
    Args:
        chrome_path: Path to Chrome executable (auto-detected if None)
        cdp_port: CDP port (default: 9222)
        user_data_dir: User data directory for Chrome (uses temp if None)
        wait_for_ready: Whether to wait for CDP to become available
        max_wait_time: Maximum time to wait for CDP in seconds
        
    Returns:
        True if Chrome started successfully, False otherwise
    """
    # Check if CDP is already available
    cdp_url = f"http://127.0.0.1:{cdp_port}"
    if check_cdp_available(cdp_url):
        logger.info("Chrome CDP is already running, skipping start")
        return True
    
    # Find Chrome executable
    if not chrome_path:
        chrome_path = find_chrome_executable()
        if not chrome_path:
            logger.error("Chrome executable not found. Please install Chrome or specify --chrome-path")
            return False
    
    if not os.path.exists(chrome_path):
        logger.error(f"Chrome executable not found at: {chrome_path}")
        return False
    
    # Set up user data directory
    if not user_data_dir:
        # Use temp directory for debug profile
        project_root = Path(__file__).parent.parent.parent
        user_data_dir = project_root / "temp" / "chrome_debug_profile"
    
    user_data_dir = Path(user_data_dir)
    user_data_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting Chrome with CDP on port {cdp_port}...")
    logger.info(f"Chrome path: {chrome_path}")
    logger.info(f"User data dir: {user_data_dir}")
    
    # Build Chrome command
    chrome_args = [
        chrome_path,
        f"--remote-debugging-port={cdp_port}",
        f"--user-data-dir={user_data_dir}",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-blink-features=AutomationControlled",
    ]
    
    try:
        # Start Chrome process
        logger.info(f"Executing: {' '.join(chrome_args[:3])} ...")
        process = subprocess.Popen(
            chrome_args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
        )
        
        logger.info(f"Chrome process started (PID: {process.pid})")
        
        # Wait for CDP to become available
        if wait_for_ready:
            logger.info(f"Waiting for Chrome CDP to become available (max {max_wait_time}s)...")
            for attempt in range(max_wait_time):
                time.sleep(1)
                if check_cdp_available(cdp_url, timeout=2):
                    logger.info(f"Chrome CDP is ready! (took {attempt + 1}s)")
                    return True
                if attempt % 5 == 0 and attempt > 0:
                    logger.debug(f"Still waiting for Chrome CDP... (attempt {attempt + 1}/{max_wait_time})")
            
            logger.warning(f"Chrome started but CDP not available after {max_wait_time}s")
            logger.warning("Chrome may still be starting. Continuing anyway...")
            return False
        else:
            logger.info("Chrome started (not waiting for CDP)")
            return True
            
    except Exception as e:
        logger.error(f"Failed to start Chrome: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    import argparse
    parser = argparse.ArgumentParser(description="Start Chrome with CDP")
    parser.add_argument("--chrome-path", help="Path to Chrome executable")
    parser.add_argument("--port", type=int, default=DEFAULT_CDP_PORT, help="CDP port (default: 9222)")
    parser.add_argument("--user-data-dir", help="Chrome user data directory")
    parser.add_argument("--no-wait", action="store_true", help="Don't wait for CDP to be ready")
    
    args = parser.parse_args()
    
    success = start_chrome_with_cdp(
        chrome_path=args.chrome_path,
        cdp_port=args.port,
        user_data_dir=args.user_data_dir,
        wait_for_ready=not args.no_wait
    )
    
    if success:
        print(f"\n[OK] Chrome CDP is ready at http://127.0.0.1:{args.port}")
        sys.exit(0)
    else:
        print(f"\n[ERROR] Failed to start Chrome with CDP")
        sys.exit(1)



