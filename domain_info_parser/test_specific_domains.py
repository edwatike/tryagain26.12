import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from parser import DomainInfoParser

async def test_domains():
    domains = ['zavod-rekom.ru', 'bigam.ru']
    parser = DomainInfoParser(headless=True, timeout=15000)
    await parser.start()
    try:
        results = await parser.parse_domains(domains)
        for r in results:
            print(f'{r["domain"]}: INN={r["inn"]}, Email={r["emails"]}, Error={r["error"]}')
            print(f'  Source URLs: {r["source_urls"]}')
    finally:
        await parser.close()

if __name__ == "__main__":
    asyncio.run(test_domains())
