import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from parser import DomainInfoParser

async def test_domains():
    domains = ['ecomont.ru','sm2000.ru','bigam.ru','inoxpoint.ru','stks-perm.ru','mkuralsteel-chlb.ru','cs27.ru','metall-ural.ru','zavod-rekom.ru','rts-ufa.ru']
    parser = DomainInfoParser(headless=True, timeout=15000)
    await parser.start()
    try:
        results = await parser.parse_domains(domains)
        for r in results:
            print(f'{r["domain"]}: INN={r["inn"]}, Email={r["emails"]}, Error={r["error"]}')
    finally:
        await parser.close()

if __name__ == "__main__":
    asyncio.run(test_domains())
