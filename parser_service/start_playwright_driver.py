"""Start Playwright driver in a separate process with correct event loop policy."""
import asyncio
import sys

# CRITICAL: Set event loop policy BEFORE any imports
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

async def start_driver():
    """Start Playwright driver and keep it running."""
    from playwright.async_api import async_playwright
    
    print("Starting Playwright driver with ProactorEventLoop...")
    playwright = await async_playwright().start()
    print("Playwright driver started successfully!")
    print("Driver is ready. Press Ctrl+C to stop.")
    
    # Keep the driver running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping Playwright driver...")
        await playwright.stop()
        print("Playwright driver stopped.")

if __name__ == "__main__":
    asyncio.run(start_driver())













