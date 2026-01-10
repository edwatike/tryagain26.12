"""
Тест с одним доменом для проверки реальной работы с Comet.
"""
import asyncio
import sys
from pathlib import Path
import logging

# Добавляем текущую директорию в путь для импортов
sys.path.append(str(Path(__file__).parent))

from comet_session import CometSession

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_single_domain():
    """Тест с одним доменом."""
    print("🧪 Single Domain Test - Реальный Comet")
    print("="*50)
    print("⚠️  Важно: Этот тест откроет реальный браузер Comet!")
    print("⚠️  Убедитесь, что готовы к автоматизации")
    print("="*50)
    
    # Тестовый домен
    test_domain = "google.com"
    
    print(f"📝 Тестовый домен: {test_domain}")
    print("\n⚠️  Убедитесь, что:")
    print("   ✅ pyautogui установлен")
    print("   ✅ Comet браузер установлен")
    print("   ✅ Не будете трогать мышь/клавиатуру")
    print("\nНажмите Enter для начала теста...")
    input()
    
    session = CometSession()
    
    try:
        logger.info(f"🚀 Начало теста с доменом: {test_domain}")
        
        # Тестируем извлечение информации
        result = await session.extract_info_from_domain(test_domain)
        
        print("\n" + "="*50)
        print("📊 РЕЗУЛЬТАТ ТЕСТА")
        print("="*50)
        print(f"Домен: {result['domain']}")
        print(f"Успешно: {result['success']}")
        print(f"Время: {result['execution_time']:.2f} сек")
        print("-"*50)
        print(f"ИНН: {result['inn']}")
        print(f"Email: {result['email']}")
        print(f"Компания: {result['company']}")
        print(f"Телефон: {result['phone']}")
        
        if not result['success']:
            print(f"Ошибка: {result.get('error', 'Unknown')}")
        
        print("="*50)
        
        if result['success']:
            print("✅ Тест прошел успешно!")
        else:
            print("❌ Тест не удался")
        
    except Exception as e:
        logger.error(f"❌ Ошибка в тесте: {e}")
        print(f"\n❌ Критическая ошибка: {e}")
    finally:
        # Закрываем браузер
        await session.close_browser()
        print("\n🔄 Браузер закрыт")


if __name__ == "__main__":
    try:
        asyncio.run(test_single_domain())
    except KeyboardInterrupt:
        print("\n⚠️ Тест прерван пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
