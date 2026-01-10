"""
Быстрый тест агента на домене
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
ollama_dir = project_root / "ollama_inn_extractor"
if ollama_dir.exists() and str(ollama_dir) not in sys.path:
    sys.path.insert(0, str(ollama_dir))

from app.agents.interactive_inn_finder import InteractiveINNFinder
from app.ollama_client import OllamaClient

async def test_domain(domain: str, start_url: str):
    print("=" * 80)
    print(f"ТЕСТ АГЕНТА НА ДОМЕНЕ: {domain}")
    print("=" * 80)
    print(f"URL: {start_url}")
    print(f"Время начала: {datetime.now().strftime('%H:%M:%S')}\n")
    
    start_time = datetime.now()
    
    try:
        ollama_client = OllamaClient(base_url="http://127.0.0.1:11434", model_name="qwen2.5:7b")
        finder = InteractiveINNFinder(
            chrome_cdp_url="http://127.0.0.1:9222",
            ollama_client=ollama_client,
            max_attempts=10  # Ограничиваем для быстрого теста
        )
        
        result = await finder.find_inn(
            domain=domain,
            start_url=start_url,
            timeout=90  # 90 секунд для теста
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "=" * 80)
        print("РЕЗУЛЬТАТЫ")
        print("=" * 80)
        print(f"Время: {duration:.1f} сек")
        print(f"Успех: {'✅ ДА' if result.get('success') else '❌ НЕТ'}")
        print(f"ИНН: {result.get('inn') or 'НЕ НАЙДЕН'}")
        print(f"URL: {result.get('url', 'N/A')}")
        print(f"Попыток: {result.get('attempts', 0)}")
        
        if result.get('success'):
            print("\n✅ АГЕНТ УСПЕШНО НАШЕЛ ИНН!")
        else:
            print("\n❌ ИНН не найден")
            if result.get('error'):
                print(f"Ошибка: {result.get('error')}")
        
        await finder.close()
        await ollama_client.close()
        
        return result.get('success')
        
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Тестируем на mc.ru
    domain = "mc.ru"
    start_url = "https://mc.ru"
    
    success = asyncio.run(test_domain(domain, start_url))
    sys.exit(0 if success else 1)

