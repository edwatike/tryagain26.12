"""
Тестовый эксперимент с исправленной активацией ассистента.
"""
import asyncio
import sys
import json
from pathlib import Path
from typing import List
import logging

# Добавляем текущую директорию в путь для импортов
sys.path.append(str(Path(__file__).parent))

from fixed_shortcut_session import FixedShortcutSession

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_fixed_session():
    """Тест исправленной сессии."""
    print("🧪 ТЕСТ ИСПРАВЛЕННОЙ АКТИВАЦИИ АССИСТЕНТА")
    print("="*60)
    print("💡 Пробуем разные способы активации ассистента")
    print("🎯 Цель: проверить ввод команды /requisites")
    print("="*60)
    
    # Тестовые домены (только 3 для быстрого теста)
    test_domains = [
        "metallsnab-nn.ru",
        "wodoprovod.ru", 
        "gremir.ru"
    ]
    
    print(f"📝 Тестовые домены: {test_domains}")
    print(f"\n⚠️  Важно:")
    print("   ✅ Shortcut /requisites создан в Comet")
    print("   ✅ Наблюдайте за процессом активации")
    print("   ✅ Не трогайте мышь/клавиатуру")
    print(f"\n🔧 Будут пробоваться:")
    print("   1. Alt+A для активации ассистента")
    print("   2. Ctrl+K для поисковой строки")
    print("   3. Прямой ввод команды")
    print("\nНажмите Enter для начала теста...")
    input()
    
    session = FixedShortcutSession()
    results = []
    
    try:
        # Открываем браузер
        await session.open_browser(test_domains[0])
        
        # Обрабатываем домены
        for i, domain in enumerate(test_domains, 1):
            print(f"\n📝 [{i}/{len(test_domains)}] Тест: {domain}")
            
            result = await session.extract_info_with_shortcut(domain)
            results.append(result)
            
            if result.get("success", False):
                print(f"✅ Успех: ИНН={result['inn']}, Email={result['email']}")
            else:
                print(f"❌ Ошибка: {result.get('error')}")
            
            if i < len(test_domains):
                print("⏳ Задержка 3 секунды...")
                await asyncio.sleep(3)
        
        # Анализ результатов
        successful = sum(1 for r in results if r.get("success", False))
        
        print(f"\n📊 РЕЗУЛЬТАТЫ ТЕСТА:")
        print(f"Успешно: {successful}/{len(results)}")
        
        if successful == len(results):
            print("🎉 ОТЛИЧНО! Все домены обработаны успешно")
        elif successful > 0:
            print("⚠️ ЧАСТИЧНЫЙ УСПЕХ. Некоторые домены обработаны")
        else:
            print("❌ НИЧЕГО НЕ РАБОТАЕТ. Нужна доработка")
        
        # Показываем результаты
        print(f"\n🎯 РЕЗУЛЬТАТЫ:")
        for result in results:
            if result.get("success", False):
                json_result = {
                    "domain": result['domain'],
                    "inn": result['inn'],
                    "email": result['email'],
                    "source_url": result.get('source_url', 'не указано')
                }
                print(json.dumps(json_result, ensure_ascii=False, indent=2))
                print()
        
    except Exception as e:
        logger.error(f"❌ Ошибка теста: {e}")
    finally:
        await session.close_browser()
        print("\n🔄 Браузер закрыт")


if __name__ == "__main__":
    try:
        asyncio.run(test_fixed_session())
    except KeyboardInterrupt:
        print("\n⚠️ Тест прерван")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
