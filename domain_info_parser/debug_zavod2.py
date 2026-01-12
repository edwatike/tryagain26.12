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
        await page.goto("https://zavod-rekom.ru/", wait_until='domcontentloaded', timeout=15000)
        await page.wait_for_timeout(2000)
        
        html = await page.content()
        
        # Ищем 7806019803 в HTML
        import re
        if '7806019803' in html:
            print("Found 7806019803 in HTML")
            # Найдем контекст вокруг этого числа
            index = html.find('7806019803')
            context = html[max(0, index-100):index+100]
            print(f"Context: {context}")
        
        # Ищем 4145281613 в HTML
        if '4145281613' in html:
            print("Found 4145281613 in HTML")
            index = html.find('4145281613')
            context = html[max(0, index-100):index+100]
            print(f"Context: {context}")
        
        await page.close()
    finally:
        await parser.close()

if __name__ == "__main__":
    asyncio.run(debug_zavod())
