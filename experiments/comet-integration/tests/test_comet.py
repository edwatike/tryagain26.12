"""
Тесты для Comet клиента.
"""
import asyncio
import sys
from pathlib import Path

# Добавляем src в путь для импортов
sys.path.append(str(Path(__file__).parent.parent / "src"))

from comet_client import CometClient


async def test_comet_connection():
    """Тест соединения с Comet."""
    print("🔧 Тест соединения с Comet...")
    
    try:
        client = CometClient()
        is_connected = await client.test_comet_connection()
        
        if is_connected:
            print("✅ Comet соединение успешно")
            return True
        else:
            print("❌ Comet соединение не удалось")
            return False
    except Exception as e:
        print(f"❌ Ошибка теста соединения: {e}")
        return False


async def test_single_domain():
    """Тест извлечения информации для одного домена."""
    print("\n🧪 Тест извлечения для одного домена...")
    
    try:
        client = CometClient()
        result = await client.extract_company_info("google.com", "привет")
        
        print(f"Результат: {result}")
        
        if result.get("success", False):
            print("✅ Одно доменное извлечение успешно")
            return True
        else:
            print("❌ Одно доменное извлечение не удалось")
            return False
    except Exception as e:
        print(f"❌ Ошибка теста одного домена: {e}")
        return False


async def test_batch_domains():
    """Тест пакетной обработки доменов."""
    print("\n📦 Тест пакетной обработки...")
    
    try:
        client = CometClient()
        test_domains = ["google.com", "yandex.ru"]
        
        results = await client.batch_extract_company_info(test_domains, delay=1)
        
        print(f"Обработано доменов: {len(results)}")
        
        successful = sum(1 for r in results if r.get("success", False))
        print(f"Успешных: {successful}/{len(results)}")
        
        if successful > 0:
            print("✅ Пакетная обработка успешна")
            return True
        else:
            print("❌ Пакетная обработка не удалась")
            return False
    except Exception as e:
        print(f"❌ Ошибка теста пакетной обработки: {e}")
        return False


async def run_all_tests():
    """Запуск всех тестов."""
    print("🧪 Запуск всех тестов Comet клиента")
    print("="*50)
    
    tests = [
        ("Соединение с Comet", test_comet_connection),
        ("Один домен", test_single_domain),
        ("Пакетная обработка", test_batch_domains)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Тест: {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Тест {test_name} завершился с ошибкой: {e}")
            results.append((test_name, False))
    
    # Итоги
    print("\n" + "="*50)
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ")
    print("="*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПАЛ"
        print(f"{test_name}: {status}")
    
    print(f"\nВсего: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены!")
    else:
        print("⚠️ Некоторые тесты не пройдены")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
