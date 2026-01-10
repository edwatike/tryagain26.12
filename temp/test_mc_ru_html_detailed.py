import asyncio
import sys
from pathlib import Path
import re

project_root = Path(__file__).parent.parent
ollama_dir = project_root / "ollama_inn_extractor"
if ollama_dir.exists() and str(ollama_dir) not in sys.path:
    sys.path.insert(0, str(ollama_dir))

from playwright.async_api import async_playwright

async def test_html_detailed():
    print("=" * 80)
    print("Detailed HTML analysis of mc.ru/company/contacts")
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
        
        print("\nNavigating to https://mc.ru/company/contacts...")
        await page.goto('https://mc.ru/company/contacts', wait_until='networkidle', timeout=30000)
        await asyncio.sleep(5)
        
        # Scroll to load all content
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(2)
        
        # Get full HTML
        html = await page.content()
        html_lower = html.lower()
        
        print(f"\nHTML length: {len(html)}")
        
        # Search for "реквизиты" or "requisites"
        requisites_keywords = ['реквизиты', 'requisites', 'реквизит', 'юридический', 'юридическ', 'юр. лицо']
        found_requisites = []
        for keyword in requisites_keywords:
            if keyword in html_lower:
                found_requisites.append(keyword)
        print(f"\nFound requisites keywords: {found_requisites}")
        
        # Search for INN pattern in HTML
        inn_pattern = r'\b\d{10}\b|\b\d{12}\b'
        all_inns = re.findall(inn_pattern, html)
        print(f"\nFound {len(all_inns)} potential INN numbers in HTML: {all_inns[:20]}")
        
        # Search for "ИНН" markers in HTML
        inn_markers_html = []
        for match in re.finditer(r'инн[:\s]*(\d{10,12})', html_lower):
            inn_markers_html.append(match.group(1))
        print(f"\nFound INN after 'ИНН' marker in HTML: {inn_markers_html}")
        
        # Search for structure: city -> requisites -> INN
        print("\n" + "=" * 80)
        print("Searching for city -> requisites -> INN structure in HTML...")
        print("=" * 80)
        
        # Look for sections with requisites
        if found_requisites:
            for req_keyword in found_requisites:
                req_positions = [m.start() for m in re.finditer(req_keyword, html_lower)]
                print(f"\nFound '{req_keyword}' at {len(req_positions)} positions")
                
                for i, req_pos in enumerate(req_positions[:5], 1):
                    # Get context around requisites (500 chars before and after)
                    start = max(0, req_pos - 500)
                    end = min(len(html), req_pos + len(req_keyword) + 500)
                    context = html[start:end]
                    context_lower = context.lower()
                    
                    # Search for INN in this context
                    inns_in_context = re.findall(inn_pattern, context)
                    
                    # Search for org forms
                    org_forms = ['ооо', 'ао', 'оао', 'зао', 'пао', 'ип']
                    org_forms_in_context = [form for form in org_forms if form in context_lower]
                    
                    # Search for cities
                    cities = ['москва', 'санкт-петербург', 'новосибирск', 'екатеринбург']
                    cities_in_context = [city for city in cities if city in context_lower]
                    
                    if inns_in_context or org_forms_in_context or cities_in_context:
                        print(f"\n{i}. Requisites section '{req_keyword}':")
                        print(f"   INNs: {inns_in_context}")
                        print(f"   Org forms: {org_forms_in_context}")
                        print(f"   Cities: {cities_in_context}")
                        # Show clean text (remove HTML tags)
                        clean_context = re.sub(r'<[^>]+>', ' ', context)
                        clean_context = re.sub(r'\s+', ' ', clean_context)
                        print(f"   Context (first 300): {clean_context[:300]}...")
        
        # Try to find all elements with "ИНН" or "реквизиты"
        print("\n" + "=" * 80)
        print("Searching for elements containing 'ИНН' or 'реквизиты'...")
        print("=" * 80)
        
        elements_with_inn = await page.evaluate("""
        (function() {
            const results = [];
            const allElements = document.querySelectorAll('*');
            
            for (let el of allElements) {
                if (el.textContent) {
                    const text = el.textContent;
                    const textLower = text.toLowerCase();
                    
                    if (textLower.includes('инн') || textLower.includes('реквизиты') || 
                        textLower.includes('requisites') || textLower.includes('юридический')) {
                        results.push({
                            tagName: el.tagName,
                            className: el.className,
                            id: el.id,
                            text: text.substring(0, 200),
                            innerHTML: el.innerHTML.substring(0, 500)
                        });
                    }
                }
            }
            
            return results.slice(0, 20); // Limit to first 20
        })();
        """)
        
        print(f"\nFound {len(elements_with_inn)} elements with 'ИНН' or 'реквизиты':")
        for i, el in enumerate(elements_with_inn[:10], 1):
            print(f"\n{i}. Tag: {el.get('tagName')}, Class: {el.get('className')}, ID: {el.get('id')}")
            print(f"   Text: {el.get('text', '')[:150]}...")
            # Search for INN in innerHTML
            inner_html = el.get('innerHTML', '')
            inns_in_html = re.findall(inn_pattern, inner_html)
            if inns_in_html:
                print(f"   INNs in HTML: {inns_in_html}")
        
        await playwright.stop()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_html_detailed())


