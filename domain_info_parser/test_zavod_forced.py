import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from parser import DomainInfoParser

async def test_zavod_forced():
    parser = DomainInfoParser(headless=True, timeout=15000)
    await parser.start()
    try:
        page = await parser.browser.new_page()
        
        # Загружаем главную
        await page.goto("https://zavod-rekom.ru/", wait_until='domcontentloaded', timeout=15000)
        await page.wait_for_timeout(2000)
        
        # Принудительно переходим на страницу с реквизитами
        await page.goto("https://zavod-rekom.ru/contacts/details/", wait_until='domcontentloaded', timeout=15000)
        await page.wait_for_timeout(2000)
        
        text = await page.evaluate('''() => document.body.innerText''')
        html = await page.content()
        
        inn = parser.extract_inn(text, html)
        emails = parser.extract_emails(text)
        
        print(f"zavod-rekom.ru: ИНН={inn}, Email={emails}")
        
        await page.close()
    finally:
        await parser.close()

if __name__ == "__main__":
    asyncio.run(test_zavod_forced())
