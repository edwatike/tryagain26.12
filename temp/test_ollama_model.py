"""Тест доступности Ollama и модели."""
import asyncio
import sys
import os

# Добавляем путь к модулям
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ollama_inn_extractor'))

from app.ollama_client import OllamaClient
from app.config import settings


async def test_model():
    """Тест модели."""
    print("=" * 80)
    print("ТЕСТ МОДЕЛИ OLLAMA")
    print("=" * 80)
    print(f"Модель из конфига: {settings.MODEL_NAME}")
    print(f"Ollama URL: {settings.OLLAMA_URL}")
    print()
    
    client = OllamaClient()
    
    try:
        # Проверка доступности
        print("[1] Проверка доступности Ollama...")
        is_available = await client.check_health()
        if is_available:
            print("[OK] Ollama доступен")
        else:
            print("[FAIL] Ollama недоступен")
            return
        
        # Тест генерации
        print(f"\n[2] Тест генерации с моделью {settings.MODEL_NAME}...")
        print("   Отправка запроса: 'Привет! Ответь одним словом: работает?'")
        
        response = await client.generate("Привет! Ответь одним словом: работает?")
        
        print(f"\n[OK] Модель ответила:")
        print(f"   {response}")
        
    except Exception as e:
        print(f"\n[ERROR] Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(test_model())

