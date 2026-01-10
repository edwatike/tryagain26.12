import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
ollama_dir = project_root / "ollama_inn_extractor"
if ollama_dir.exists() and str(ollama_dir) not in sys.path:
    sys.path.insert(0, str(ollama_dir))

from app.agents.browser_agent import BrowserAgent
from playwright.async_api import async_playwright
import re

async def test_debug():
    print("=" * 80)
    print("Debugging mc.ru contacts page")
    print("=" * 80)
    
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.connect_over_cdp('http://127.0.0.1:9222')
        
        # Get existing context or create new
        if browser.contexts:
            context = browser.contexts[0]
        else:
            context = await browser.new_context()
        
        # Get existing page or create new
        if context.pages:
            page = context.pages[0]
        else:
            page = await context.new_page()
        
        # Navigate to mc.ru contacts page
        print("\nNavigating to https://mc.ru/company/contacts...")
        await page.goto('https://mc.ru/company/contacts', wait_until='domcontentloaded', timeout=10000)
        await asyncio.sleep(3)
        
        # Get page text
        page_text = await page.inner_text('body')
        print(f"\nPage text length: {len(page_text)}")
        print(f"First 500 chars: {page_text[:500]}")
        
        # Search for INN pattern
        inn_pattern = r'\b\d{10}\b|\b\d{12}\b'
        matches = re.findall(inn_pattern, page_text)
        print(f"\nFound {len(matches)} potential INN matches: {matches[:10]}")
        
        # Search for org forms
        org_forms = ['ооо', 'ао', 'оао', 'зао', 'пао', 'ип']
        found_org_forms = []
        page_text_lower = page_text.lower()
        for form in org_forms:
            if form in page_text_lower:
                found_org_forms.append(form)
        print(f"\nFound org forms: {found_org_forms}")
        
        # Search for "ИНН" or "INN"
        has_inn_marker = 'инн' in page_text_lower or 'inn' in page_text_lower
        print(f"\nHas 'ИНН' or 'INN' marker: {has_inn_marker}")
        
        # Test JavaScript search
        agent = BrowserAgent()
        agent.page = page
        
        print("\nTesting JavaScript search...")
        js_results = await agent.search_inn_via_javascript()
        print(f"JavaScript search found {len(js_results)} results")
        if js_results:
            for i, r in enumerate(js_results[:5], 1):
                print(f"  {i}. INN: {r.get('inn')}, has_inn_context: {r.get('has_inn_context')}, has_org_form: {r.get('has_org_form')}, priority: {r.get('priority')}")
        
        # Test storage search
        print("\nTesting storage search...")
        storage_results = await agent.search_inn_in_storage()
        print(f"Storage search found {len(storage_results)} results")
        if storage_results:
            for i, r in enumerate(storage_results[:5], 1):
                print(f"  {i}. INN: {r.get('inn')}, has_inn_context: {r.get('has_inn_context')}, has_org_form: {r.get('has_org_form')}, priority: {r.get('priority')}")
        
        await playwright.stop()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_debug())


