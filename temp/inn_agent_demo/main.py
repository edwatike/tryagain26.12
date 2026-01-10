"""Demo program for INN search agent with detailed logging."""
import asyncio
import sys
import logging
import argparse
from pathlib import Path
from typing import Optional

# Add parent directories to path for imports
project_root = Path(__file__).parent.parent.parent
current_dir = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "ollama_inn_extractor"))
sys.path.insert(0, str(current_dir))  # For importing start_chrome

# Import agent components
from app.agents.interactive_inn_finder import InteractiveINNFinder
from app.ollama_client import OllamaClient
from start_chrome import start_chrome_with_cdp, check_cdp_available, DEFAULT_CDP_PORT

# Set up detailed logging
def setup_logging(level: str = "DEBUG"):
    """Set up detailed logging to terminal.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    log_level = getattr(logging, level.upper(), logging.DEBUG)
    
    # Create formatter with detailed information
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)-8s] [%(name)-30s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    
    # Set specific loggers to appropriate levels
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.INFO)
    
    # Create custom loggers for different components
    agent_logger = logging.getLogger("AGENT")
    agent_logger.setLevel(log_level)
    
    ai_logger = logging.getLogger("AI")
    ai_logger.setLevel(log_level)
    
    browser_logger = logging.getLogger("BROWSER")
    browser_logger.setLevel(log_level)
    
    inn_logger = logging.getLogger("INN")
    inn_logger.setLevel(log_level)
    
    result_logger = logging.getLogger("RESULT")
    result_logger.setLevel(log_level)


async def find_inn_on_website(
    url: str,
    chrome_cdp_url: str = f"http://127.0.0.1:{DEFAULT_CDP_PORT}",
    ollama_url: Optional[str] = None,
    model_name: Optional[str] = None,
    max_attempts: int = 15
) -> dict:
    """Find INN on website using AI agent.
    
    Args:
        url: Website URL to search
        chrome_cdp_url: Chrome CDP URL
        ollama_url: Ollama API URL (optional)
        model_name: Ollama model name (optional)
        max_attempts: Maximum number of search attempts
        
    Returns:
        Result dictionary with INN search results
    """
    logger = logging.getLogger("RESULT")
    agent_logger = logging.getLogger("AGENT")
    
    # Extract domain from URL
    from urllib.parse import urlparse
    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")
    
    agent_logger.info("=" * 80)
    agent_logger.info(f"Starting INN search for website: {url}")
    agent_logger.info(f"Domain: {domain}")
    agent_logger.info(f"Chrome CDP URL: {chrome_cdp_url}")
    agent_logger.info("=" * 80)
    
    # Initialize Ollama client if needed
    ollama_client = None
    if ollama_url or model_name:
        ollama_client = OllamaClient(
            base_url=ollama_url,
            model_name=model_name
        )
        agent_logger.info(f"Using Ollama: {ollama_client.base_url}, model: {ollama_client.model_name}")
    
    # Initialize INN finder
    finder = InteractiveINNFinder(
        chrome_cdp_url=chrome_cdp_url,
        ollama_client=ollama_client,
        max_attempts=max_attempts
    )
    
    try:
        # Start search
        agent_logger.info(f"Starting interactive INN search...")
        result = await finder.find_inn(
            domain=domain,
            start_url=url,
            timeout=120  # 2 minutes timeout
        )
        
        # Log results
        logger.info("=" * 80)
        logger.info("SEARCH RESULTS")
        logger.info("=" * 80)
        logger.info(f"Success: {result.get('success', False)}")
        logger.info(f"INN: {result.get('inn', 'Not found')}")
        logger.info(f"Context: {result.get('context', 'N/A')}")
        logger.info(f"Final URL: {result.get('url', url)}")
        logger.info(f"Attempts: {result.get('attempts', 0)}")
        logger.info(f"Actions taken: {len(result.get('actions_taken', []))}")
        logger.info("=" * 80)
        
        # Log action history
        if result.get('actions_taken'):
            logger.info("Action History:")
            for i, action in enumerate(result['actions_taken'], 1):
                logger.info(f"  {i}. {action}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error during INN search: {e}", exc_info=True)
        return {
            "success": False,
            "inn": None,
            "error": str(e),
            "url": url,
            "attempts": 0,
            "actions_taken": []
        }
    
    finally:
        # Close connections
        try:
            await finder.close()
            if ollama_client:
                await ollama_client.close()
        except Exception as e:
            logging.getLogger("AGENT").warning(f"Error closing connections: {e}")


def validate_and_normalize_url(url: str) -> str:
    """Validate and normalize URL.
    
    Args:
        url: URL string (may be missing protocol)
        
    Returns:
        Normalized URL with protocol
        
    Raises:
        ValueError: If URL is invalid
    """
    url = url.strip()
    
    # If no protocol specified, add https://
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
        logging.getLogger("RESULT").info(f"Added https:// to URL: {url}")
    
    # Basic URL validation
    from urllib.parse import urlparse
    parsed = urlparse(url)
    
    if not parsed.netloc:
        raise ValueError(f"Invalid URL: {url}. Please provide a valid URL like 'example.com' or 'https://example.com'")
    
    return url


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Demo program for INN search agent with detailed logging",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py example.com
  python main.py https://www.obi.ru
  python main.py https://www.obi.ru --model qwen2.5:14b
  python main.py example.com --chrome-port 9223 --no-auto-chrome
        """
    )
    
    parser.add_argument(
        "url",
        type=str,
        help="Website URL to search for INN (e.g., 'example.com' or 'https://example.com')"
    )
    
    parser.add_argument(
        "--chrome-port",
        type=int,
        default=DEFAULT_CDP_PORT,
        help=f"Chrome CDP port (default: {DEFAULT_CDP_PORT})"
    )
    
    parser.add_argument(
        "--chrome-path",
        help="Path to Chrome executable (auto-detected if not specified)"
    )
    
    parser.add_argument(
        "--no-auto-chrome",
        action="store_true",
        help="Don't automatically start Chrome (assume it's already running)"
    )
    
    parser.add_argument(
        "--ollama-url",
        default="http://127.0.0.1:11434",
        help="Ollama API URL (default: http://127.0.0.1:11434)"
    )
    
    parser.add_argument(
        "--model",
        help="Ollama model name (default: from config)"
    )
    
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=15,
        help="Maximum number of search attempts (default: 15)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="DEBUG",
        help="Logging level (default: DEBUG)"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(level=args.log_level)
    logger = logging.getLogger("RESULT")
    
    # Validate and normalize URL
    try:
        normalized_url = validate_and_normalize_url(args.url)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # Check/start Chrome
    chrome_cdp_url = f"http://127.0.0.1:{args.chrome_port}"
    
    if not args.no_auto_chrome:
        logger.info("Checking Chrome CDP availability...")
        if not check_cdp_available(chrome_cdp_url):
            logger.info("Chrome CDP not available, starting Chrome...")
            success = start_chrome_with_cdp(
                chrome_path=args.chrome_path,
                cdp_port=args.chrome_port,
                wait_for_ready=True,
                max_wait_time=30
            )
            if not success:
                logger.error("Failed to start Chrome with CDP. Exiting.")
                sys.exit(1)
        else:
            logger.info("Chrome CDP is already available")
    else:
        logger.info("Skipping Chrome auto-start (--no-auto-chrome specified)")
        if not check_cdp_available(chrome_cdp_url):
            logger.warning(f"Chrome CDP not available at {chrome_cdp_url}")
            logger.warning("Please start Chrome manually with CDP enabled")
            sys.exit(1)
    
    # Run async main
    try:
        result = asyncio.run(
            find_inn_on_website(
                url=normalized_url,
                chrome_cdp_url=chrome_cdp_url,
                ollama_url=args.ollama_url,
                model_name=args.model,
                max_attempts=args.max_attempts
            )
        )
        
        # Exit with appropriate code
        if result.get("success") and result.get("inn"):
            logger.info(f"\n[SUCCESS] INN found: {result['inn']}")
            sys.exit(0)
        else:
            logger.warning(f"\n[FAILED] INN not found")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n[INTERRUPTED] Search interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"\n[ERROR] Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

