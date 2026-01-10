import asyncio
import sys
from pathlib import Path
import re

project_root = Path(__file__).parent.parent
ollama_dir = project_root / "ollama_inn_extractor"
if ollama_dir.exists() and str(ollama_dir) not in sys.path:
    sys.path.insert(0, str(ollama_dir))

from playwright.async_api import async_playwright

async def test_contacts_detailed():
    print("=" * 80)
    print("Detailed analysis of mc.ru/company/contacts page")
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
        
        # Get all text content
        page_text = await page.inner_text('body')
        print(f"\nPage text length: {len(page_text)}")
        
        # Search for city names and INN patterns
        print("\n" + "=" * 80)
        print("Searching for cities and INN patterns...")
        print("=" * 80)
        
        # Common city names in Russia
        cities = ['москва', 'санкт-петербург', 'новосибирск', 'екатеринбург', 'казань', 
                  'нижний новгород', 'челябинск', 'самара', 'омск', 'ростов-на-дону',
                  'уфа', 'красноярск', 'воронеж', 'пермь', 'волгоград']
        
        page_text_lower = page_text.lower()
        
        # Find cities mentioned on page
        found_cities = []
        for city in cities:
            if city in page_text_lower:
                found_cities.append(city)
        
        print(f"\nFound cities: {found_cities}")
        
        # Search for INN pattern
        inn_pattern = r'\b\d{10}\b|\b\d{12}\b'
        all_inns = re.findall(inn_pattern, page_text)
        print(f"\nFound {len(all_inns)} potential INN numbers: {all_inns[:20]}")
        
        # Search for "ИНН" markers
        inn_markers = []
        for match in re.finditer(r'инн[:\s]*(\d{10,12})', page_text_lower):
            inn_markers.append(match.group(1))
        print(f"\nFound INN after 'ИНН' marker: {inn_markers}")
        
        # Search for org forms
        org_forms = ['ооо', 'ао', 'оао', 'зао', 'пао', 'ип']
        found_org_forms = []
        for form in org_forms:
            if form in page_text_lower:
                found_org_forms.append(form)
        print(f"\nFound org forms: {found_org_forms}")
        
        # Try to find structure: city -> org form -> INN
        print("\n" + "=" * 80)
        print("Searching for city -> org form -> INN structure...")
        print("=" * 80)
        
        # Get HTML to see structure
        html = await page.content()
        
        # Look for sections with cities
        city_sections = []
        for city in found_cities:
            city_pos = page_text_lower.find(city)
            if city_pos != -1:
                # Get context around city (500 chars)
                start = max(0, city_pos - 100)
                end = min(len(page_text), city_pos + len(city) + 500)
                context = page_text[start:end]
                
                # Search for INN in this context
                inns_in_context = re.findall(inn_pattern, context)
                org_forms_in_context = [form for form in org_forms if form in context.lower()]
                
                if inns_in_context or org_forms_in_context:
                    city_sections.append({
                        'city': city,
                        'context': context[:300],
                        'inns': inns_in_context,
                        'org_forms': org_forms_in_context
                    })
        
        print(f"\nFound {len(city_sections)} city sections with potential INN:")
        for i, section in enumerate(city_sections, 1):
            print(f"\n{i}. City: {section['city']}")
            print(f"   INNs: {section['inns']}")
            print(f"   Org forms: {section['org_forms']}")
            print(f"   Context: {section['context'][:200]}...")
        
        # Try JavaScript search in DOM
        print("\n" + "=" * 80)
        print("JavaScript DOM search...")
        print("=" * 80)
        
        js_result = await page.evaluate("""
        (function() {
            const innPattern = /\\b\\d{10}\\b|\\b\\d{12}\\b/g;
            const results = [];
            const allElements = document.querySelectorAll('*');
            
            for (let el of allElements) {
                if (el.textContent) {
                    const text = el.textContent;
                    const textLower = text.toLowerCase();
                    
                    // Check if element contains city, org form, or INN marker
                    const hasCity = textLower.includes('москва') || textLower.includes('санкт-петербург') || 
                                   textLower.includes('новосибирск') || textLower.includes('екатеринбург');
                    const hasOrgForm = textLower.includes('ооо') || textLower.includes('ао') || 
                                     textLower.includes('оао') || textLower.includes('зао');
                    const hasInnMarker = textLower.includes('инн');
                    
                    if (hasCity || hasOrgForm || hasInnMarker) {
                        const matches = text.match(innPattern);
                        if (matches) {
                            for (let match of matches) {
                                if (match.length === 10 || match.length === 12) {
                                    const matchIndex = text.indexOf(match);
                                    const context = text.substring(
                                        Math.max(0, matchIndex - 100),
                                        Math.min(text.length, matchIndex + match.length + 100)
                                    );
                                    results.push({
                                        inn: match,
                                        context: context.trim(),
                                        hasCity: hasCity,
                                        hasOrgForm: hasOrgForm,
                                        hasInnMarker: hasInnMarker,
                                        tagName: el.tagName
                                    });
                                }
                            }
                        }
                    }
                }
            }
            
            // Remove duplicates
            const uniqueResults = [];
            const seenInns = new Set();
            for (let result of results) {
                if (!seenInns.has(result.inn)) {
                    seenInns.add(result.inn);
                    uniqueResults.push(result);
                }
            }
            
            return uniqueResults;
        })();
        """)
        
        print(f"\nJavaScript found {len(js_result)} INN matches:")
        for i, r in enumerate(js_result[:10], 1):
            print(f"\n{i}. INN: {r.get('inn')}")
            print(f"   Has city: {r.get('hasCity')}")
            print(f"   Has org form: {r.get('hasOrgForm')}")
            print(f"   Has INN marker: {r.get('hasInnMarker')}")
            print(f"   Context: {r.get('context', '')[:200]}...")
        
        await playwright.stop()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_contacts_detailed())


