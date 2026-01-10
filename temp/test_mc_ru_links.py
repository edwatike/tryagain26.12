import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
ollama_dir = project_root / "ollama_inn_extractor"
if ollama_dir.exists() and str(ollama_dir) not in sys.path:
    sys.path.insert(0, str(ollama_dir))

from app.agents.browser_agent import BrowserAgent
from playwright.async_api import async_playwright

async def test_links():
    print("=" * 80)
    print("Testing links on mc.ru homepage")
    print("=" * 80)
    
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.connect_over_cdp('http://127.0.0.1:9222')
        
        if browser.contexts:
            context = browser.contexts[0]
        else:
            context = await browser.new_context()
        
        if context.pages:
            page = context.pages[0]
        else:
            page = await context.new_page()
        
        print("\nNavigating to https://mc.ru...")
        await page.goto('https://mc.ru', wait_until='networkidle', timeout=30000)
        await asyncio.sleep(3)
        
        # Get all links
        agent = BrowserAgent()
        agent.page = page
        
        links = await agent.get_links()
        print(f"\nFound {len(links)} links on page:")
        for i, link in enumerate(links[:30], 1):
            print(f"{i}. Text: '{link.get('text', '')}', href: {link.get('href', '')[:100]}")
        
        # Search for "О компании" or similar
        print("\n" + "=" * 80)
        print("Searching for 'О компании' or similar links...")
        print("=" * 80)
        
        keywords = ['о компании', 'о нас', 'about', 'company', 'контакты', 'contacts', 'реквизиты', 'requisites']
        found_links = []
        for link in links:
            text_lower = link.get('text', '').lower()
            for keyword in keywords:
                if keyword in text_lower:
                    found_links.append(link)
                    break
        
        print(f"\nFound {len(found_links)} links matching keywords:")
        for i, link in enumerate(found_links, 1):
            print(f"{i}. Text: '{link.get('text', '')}', href: {link.get('href', '')}")
        
        # Try to click on "О компании"
        if found_links:
            target_link = found_links[0]
            print(f"\nTrying to click on: '{target_link.get('text', '')}'")
            clicked = await agent.click_link(target_link.get('text', ''))
            print(f"Click result: {clicked}")
            
            if clicked:
                await asyncio.sleep(2)
                new_url = await agent.get_current_url()
                print(f"New URL: {new_url}")
        
        await playwright.stop()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_links())


