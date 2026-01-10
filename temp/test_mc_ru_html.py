import asyncio
import sys
from pathlib import Path
import re

project_root = Path(__file__).parent.parent
ollama_dir = project_root / "ollama_inn_extractor"
if ollama_dir.exists() and str(ollama_dir) not in sys.path:
    sys.path.insert(0, str(ollama_dir))

from app.agents.browser_agent import BrowserAgent
from playwright.async_api import async_playwright

async def test_html_search():
    print("=" * 80)
    print("Testing HTML search on mc.ru contacts page")
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
        
        # Get full HTML
        html = await page.content()
        print(f"\nHTML length: {len(html)}")
        
        # Search for INN pattern in HTML
        inn_pattern = r'\b\d{10}\b|\b\d{12}\b'
        matches = re.findall(inn_pattern, html)
        print(f"\nFound {len(matches)} potential INN matches in HTML: {matches[:10]}")
        
        # Search for "ИНН" or "INN" in HTML
        html_lower = html.lower()
        has_inn_marker = 'инн' in html_lower or 'inn' in html_lower
        print(f"\nHas 'ИНН' or 'INN' marker in HTML: {has_inn_marker}")
        
        # Search for org forms in HTML
        org_forms = ['ооо', 'ао', 'оао', 'зао', 'пао', 'ип']
        found_org_forms = []
        for form in org_forms:
            if form in html_lower:
                found_org_forms.append(form)
        print(f"\nFound org forms in HTML: {found_org_forms}")
        
        # Try to find INN near "ИНН" or org form
        if has_inn_marker:
            inn_pos = html_lower.find('инн') if 'инн' in html_lower else html_lower.find('inn')
            if inn_pos != -1:
                start = max(0, inn_pos - 200)
                end = min(len(html), inn_pos + 200)
                context_area = html[start:end]
                matches_near = re.findall(inn_pattern, context_area)
                print(f"\nFound {len(matches_near)} INN matches near 'ИНН'/'INN': {matches_near}")
        
        if found_org_forms:
            for org_form in found_org_forms:
                org_pos = html_lower.find(org_form)
                if org_pos != -1:
                    start = max(0, org_pos - 200)
                    end = min(len(html), org_pos + len(org_form) + 200)
                    context_area = html[start:end]
                    matches_near = re.findall(inn_pattern, context_area)
                    if matches_near:
                        print(f"\nFound {len(matches_near)} INN matches near '{org_form}': {matches_near}")
                        print(f"Context: {context_area[:300]}")
        
        # Test comprehensive search
        agent = BrowserAgent()
        agent.page = page
        
        print("\nTesting comprehensive search...")
        result = await agent.search_inn_comprehensive()
        
        print("\n" + "=" * 80)
        print("RESULTS")
        print("=" * 80)
        if result:
            print(f"INN: {result.get('inn')}")
            print(f"Source: {result.get('source')}")
            print(f"Has INN context: {result.get('has_inn_context')}")
            print(f"Has org form: {result.get('has_org_form')}")
            context_text = result.get('context', '')[:500]
            print(f"Context: {context_text}...")
        else:
            print("INN not found")
        
        await playwright.stop()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_html_search())


