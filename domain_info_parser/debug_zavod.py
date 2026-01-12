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
        
        # Ищем ОГРН 1027804189930 и ИНН рядом
        import re
        pattern = r'1027804189930[^\d]{0,50}(\d{10})'
        matches = re.findall(pattern, html)
        print(f"Found INN near OGRN 1027804189930: {matches}")
        
        # Ищем все ИНН рядом с любыми ОГРН
        pattern2 = r'(\d{13})[^\d]{0,50}(\d{10})'
        matches2 = re.findall(pattern2, html)
        print(f"Found OGRN+INN pairs: {matches2}")
        
        await page.close()
    finally:
        await parser.close()

if __name__ == "__main__":
    asyncio.run(debug_zavod())
