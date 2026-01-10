"""
Простая проверка работы агента - только подключение и первая страница
"""
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
ollama_dir = project_root / "ollama_inn_extractor"
if ollama_dir.exists() and str(ollama_dir) not in sys.path:
    sys.path.insert(0, str(ollama_dir))

from app.agents.browser_agent import BrowserAgent
from app.ollama_client import OllamaClient

async def quick_test():
    print("=" * 80)
    print("БЫСТРАЯ ПРОВЕРКА АГЕНТА")
    print("=" * 80)
    
    domain = "mc.ru"
    url = "https://mc.ru"
    
    print(f"\nДомен: {domain}")
    print(f"URL: {url}\n")
    
    try:
        # Проверка подключения к Chrome
        print("[1/3] Подключение к Chrome...")
        browser_agent = BrowserAgent(chrome_cdp_url="http://127.0.0.1:9222")
        await browser_agent.connect()
        print("[OK] Chrome подключен")
        
        # Навигация
        print(f"\n[2/3] Навигация на {url}...")
        await browser_agent.navigate(url)
        current_url = await browser_agent.get_current_url()
        print(f"[OK] Перешли на: {current_url}")
        
        # Поиск ИНН
        print(f"\n[3/3] Поиск ИНН на странице...")
        result = await browser_agent.search_inn_comprehensive()
        
        if result:
            print(f"\n[SUCCESS] INN FOUND!")
            print(f"   INN: {result.get('inn')}")
            print(f"   Source: {result.get('source')}")
            print(f"   Context: {result.get('context', '')[:100]}...")
        else:
            print("\n[INFO] INN not found on first page")
            print("   (Agent will continue searching on other pages)")
        
        await browser_agent.close()
        
        print("\n" + "=" * 80)
        print("Check completed")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(quick_test())

