import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
ollama_dir = project_root / "ollama_inn_extractor"
if ollama_dir.exists() and str(ollama_dir) not in sys.path:
    sys.path.insert(0, str(ollama_dir))

from app.agents.browser_agent import BrowserAgent
from playwright.async_api import async_playwright

async def test_comprehensive():
    print("=" * 80)
    print("Test: search_inn_comprehensive on mc.ru/company/contacts")
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
        
        agent = BrowserAgent()
        agent.page = page
        
        # Navigate
        print("\nNavigating to https://mc.ru/company/contacts...")
        await agent.navigate('https://mc.ru/company/contacts')
        await asyncio.sleep(2)
        
        # Get page text
        print("\nGetting page text...")
        text = await agent.get_page_text()
        print(f"Page text length: {len(text)}")
        print(f"First 500 chars: {text[:500]}")
        
        # Test comprehensive search
        print("\nTesting search_inn_comprehensive...")
        result = await agent.search_inn_comprehensive()
        
        print("\n" + "=" * 80)
        print("RESULTS")
        print("=" * 80)
        if result:
            print(f"[FOUND] INN: {result.get('inn')}")
            print(f"Source: {result.get('source')}")
            print(f"Priority: {result.get('priority')}")
            print(f"Context: {result.get('context', '')[:200]}")
        else:
            print("[NOT FOUND] No INN found")
        
        # Try regex search
        print("\nTesting regex search in page text...")
        import re
        inn_pattern = r'\b\d{10}\b'
        matches = re.findall(inn_pattern, text)
        print(f"Regex matches (10 digits): {matches[:10]}")
        
        # Check for "ИНН" in text
        if "ИНН" in text or "INN" in text:
            print("\n[INFO] Found 'ИНН' or 'INN' in page text")
            # Find context around ИНН
            idx = text.find("ИНН")
            if idx != -1:
                print(f"Context around ИНН: {text[max(0, idx-100):idx+200]}")
        else:
            print("\n[INFO] 'ИНН' or 'INN' not found in page text")
        
        await playwright.stop()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_comprehensive())


