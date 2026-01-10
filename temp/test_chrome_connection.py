"""Test Chrome CDP connection and page opening."""
import asyncio
import sys

# Set event loop policy for Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from playwright.async_api import async_playwright

async def test():
    print("Testing Chrome CDP connection...")
    
    try:
        playwright = await async_playwright().start()
        print("Playwright started")
        
        browser = await playwright.chromium.connect_over_cdp("http://127.0.0.1:9222")
        print("Connected to Chrome CDP")
        
        contexts = browser.contexts
        if len(contexts) == 0:
            context = await browser.new_context(viewport={"width": 800, "height": 600})
            print("Created new context")
        else:
            context = contexts[0]
            print(f"Using existing context with {len(context.pages)} pages")
        
        page = await context.new_page()
        print("Created new page")
        
        print("Opening Google search page...")
        await page.goto("https://www.google.com/search?q=кирпич+купить&hl=ru", timeout=60000, wait_until="domcontentloaded")
        print(f"Page loaded: {page.url}")
        print(f"Page title: {await page.title()}")
        
        # Wait a bit
        await asyncio.sleep(3)
        
        # Try to find links
        elems = page.locator("a")
        count = await elems.count()
        print(f"Found {count} links on page")
        
        # Get first 10 links
        links_found = []
        for i in range(min(count, 10)):
            try:
                href = await elems.nth(i).get_attribute("href")
                if href:
                    links_found.append(href)
                    print(f"Link {i}: {href[:80]}...")
            except:
                pass
        
        # Filter .ru links
        ru_links = [l for l in links_found if ".ru" in l and "google" not in l.lower()]
        print(f"\nFound {len(ru_links)} .ru links:")
        for link in ru_links[:5]:
            print(f"  - {link[:80]}...")
        
        await page.close()
        await browser.close()
        await playwright.stop()
        
        print("\nTest completed successfully!")
        return len(ru_links) > 0
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test())
    exit(0 if result else 1)



















