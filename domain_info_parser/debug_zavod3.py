import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from parser import DomainInfoParser

async def debug_zavod():
    parser = DomainInfoParser(headless=True, timeout=15000)
    await parser.start()
    try:
        page = await parser.browser.new_page()
        await page.goto("https://zavod-rekom.ru/contacts/details/", wait_until='domcontentloaded', timeout=15000)
        await page.wait_for_timeout(2000)
        
        html = await page.content()
        text = await page.evaluate('''() => document.body.innerText''')
        
        # Ищем 7806019803 в HTML и тексте
        print("=== HTML SEARCH ===")
        if '7806019803' in html:
            print("Found 7806019803 in HTML")
            index = html.find('7806019803')
            context = html[max(0, index-100):index+100]
            print(f"Context: {context}")
        
        print("\n=== TEXT SEARCH ===")
        if '7806019803' in text:
            print("Found 7806019803 in text")
            index = text.find('7806019803')
            context = text[max(0, index-100):index+100]
            print(f"Context: {context}")
        
        # Ищем все 10-значные числа
        import re
        numbers = re.findall(r'\d{10}', html)
        print(f"\nAll 10-digit numbers in HTML: {numbers}")
        
        await page.close()
    finally:
        await parser.close()

if __name__ == "__main__":
    asyncio.run(debug_zavod())
