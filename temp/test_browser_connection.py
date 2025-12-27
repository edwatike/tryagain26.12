"""Test if parser connects to existing browser."""
import asyncio
import sys

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from playwright.async_api import async_playwright
import httpx

async def test():
    print("=" * 60)
    print("Testing Browser Connection")
    print("=" * 60)
    
    # Check Chrome CDP
    print("\n[1] Checking Chrome CDP...")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://127.0.0.1:9222/json/version")
            cdp_info = response.json()
            ws_url = cdp_info.get("webSocketDebuggerUrl")
            print(f"[OK] Chrome CDP available")
            print(f"  WebSocket URL: {ws_url}")
    except Exception as e:
        print(f"[ERROR] Chrome CDP not available: {e}")
        return False
    
    # Connect via Playwright
    print("\n[2] Connecting via Playwright...")
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.connect_over_cdp(ws_url)
        print(f"[OK] Connected to browser")
        
        # Check contexts
        contexts = browser.contexts
        print(f"\n[3] Browser contexts: {len(contexts)}")
        for i, ctx in enumerate(contexts):
            pages = ctx.pages
            print(f"  Context {i}: {len(pages)} pages")
            for j, page in enumerate(pages):
                try:
                    url = page.url
                    title = await page.title()
                    print(f"    Page {j}: {url[:60]}... (title: {title[:40]}...)")
                except:
                    print(f"    Page {j}: (error getting info)")
        
        # Use existing context
        if len(contexts) > 0:
            context = contexts[0]
            print(f"\n[4] Using existing context with {len(context.pages)} pages")
            
            # Create new page in existing context
            page = await context.new_page()
            print(f"[OK] Created new page in existing context")
            
            # Navigate to Google
            print(f"\n[5] Navigating to Google...")
            await page.goto("https://www.google.com/search?q=кирпич+купить&hl=ru", timeout=30000)
            print(f"[OK] Page loaded: {page.url}")
            
            # Check if we can see the page
            title = await page.title()
            print(f"  Title: {title}")
            
            # Try to find links
            elems = page.locator("a")
            count = await elems.count()
            print(f"  Found {count} links")
            
            # Get some links
            ru_links = []
            for i in range(min(count, 20)):
                try:
                    href = await elems.nth(i).get_attribute("href")
                    if href and ".ru" in href and "google" not in href.lower():
                        ru_links.append(href.split("&")[0].split("?")[0])
                except:
                    pass
            
            print(f"\n[6] Found {len(ru_links)} .ru links:")
            for link in ru_links[:5]:
                print(f"  - {link}")
            
            await page.close()
            await browser.close()
            await playwright.stop()
            
            print(f"\n{'='*60}")
            if len(ru_links) > 0:
                print("[SUCCESS] Parser can connect and find URLs!")
                return True
            else:
                print("[WARNING] Parser connects but finds no URLs (may be CAPTCHA)")
                return False
        else:
            print("[ERROR] No browser contexts found")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test())
    exit(0 if result else 1)

