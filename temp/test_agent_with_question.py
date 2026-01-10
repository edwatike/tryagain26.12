"""Автоматический тест агента: поиск ИНН и вопрос про алгоритм."""
import asyncio
import sys
import os
from datetime import datetime

# Добавляем путь к модулям
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ollama_inn_extractor'))

from app.agents.interactive_inn_finder import InteractiveINNFinder
from app.ollama_client import OllamaClient
from app.config import settings


async def test_agent():
    """Тест агента: поиск ИНН и вопрос про алгоритм."""
    print("=" * 80)
    print("ТЕСТ АГЕНТА: ПОИСК ИНН И ВОПРОС ПРО АЛГОРИТМ")
    print("=" * 80)
    print(f"Домен: cvetmetall.ru")
    print(f"URL: https://cvetmetall.ru/")
    print(f"Модель: {settings.MODEL_NAME}")
    print()
    
    # Инициализация
    ollama_client = OllamaClient(
        base_url="http://127.0.0.1:11434",
        model_name=settings.MODEL_NAME
    )
    
    finder = InteractiveINNFinder(
        chrome_cdp_url="http://127.0.0.1:9222",
        ollama_client=ollama_client,
        strategy="universal"
    )
    
    try:
        # Шаг 1: Поиск ИНН
        print("[1] Запуск поиска ИНН для cvetmetall.ru...")
        print("-" * 80)
        
        result = await finder.find_inn(
            domain="cvetmetall.ru",
            start_url="https://cvetmetall.ru/",
            timeout=120
        )
        
        print("\n" + "=" * 80)
        print("РЕЗУЛЬТАТЫ ПОИСКА ИНН")
        print("=" * 80)
        print(f"Успех: {'ДА' if result.get('success') else 'НЕТ'}")
        print(f"ИНН: {result.get('inn') or 'НЕ НАЙДЕН'}")
        print(f"URL: {result.get('url') or 'N/A'}")
        print(f"Фаза: {result.get('phase') or 'N/A'}")
        print("=" * 80)
        
        if not result.get('success'):
            print("\n[ERROR] ИНН не найден! Тест не может быть продолжен.")
            return
        
        # Шаг 2: Вопрос про алгоритм
        print("\n[2] Задаю вопрос агенту про алгоритм...")
        print("-" * 80)
        
        # Подготавливаем контекст
        last_inn = result.get('inn')
        last_domain = "cvetmetall.ru"
        last_phase = result.get('phase') or "неизвестно"
        
        question = "какой алгоритм ты использовал для получения инн"
        print(f"Вопрос: {question}")
        print()
        
        # Формируем промпт с контекстом
        context_prompt = f"""Ты агент поиска ИНН. Нашел ИНН {last_inn} для {last_domain} через {last_phase}.

Алгоритм: Phase 1 (локальный) → Phase 2 (Checko.ru) → Phase 3 (Google) → Phase 4 (проверка).

Вопрос: {question}

Ответь кратко (до 100 слов)."""
        
        # Получаем ответ от AI
        print("[INFO] Отправка запроса к модели...")
        ai_response = await asyncio.wait_for(
            ollama_client.generate(prompt=context_prompt),
            timeout=60
        )
        
        print("\n" + "=" * 80)
        print("ОТВЕТ АГЕНТА (от AI модели)")
        print("=" * 80)
        print(ai_response)
        print("=" * 80)
        
        # Проверка качества ответа
        print("\n[3] Проверка качества ответа...")
        print("-" * 80)
        
        # Проверяем, что ответ не пустой и содержит информацию об алгоритме
        if not ai_response or len(ai_response.strip()) < 10:
            print("[FAIL] Ответ слишком короткий или пустой")
            return
        
        # Проверяем, что ответ содержит упоминание алгоритма или фаз
        response_lower = ai_response.lower()
        algorithm_keywords = ['алгоритм', 'algorithm', 'фаза', 'phase', 'checko', 'google', 'локальный', 'local']
        has_algorithm_info = any(keyword in response_lower for keyword in algorithm_keywords)
        
        if has_algorithm_info:
            print("[OK] Ответ содержит информацию об алгоритме")
        else:
            print("[WARNING] Ответ может не содержать достаточно информации об алгоритме")
        
        # Проверяем, что ответ не является простым fallback
        fallback_phrases = [
            'я только что нашел',
            'для cvetmetall.ru инн',
            'найден через phase'
        ]
        is_fallback = any(phrase in response_lower for phrase in fallback_phrases)
        
        if is_fallback:
            print("[WARNING] Ответ похож на fallback, возможно модель не использовалась")
        else:
            print("[OK] Ответ выглядит как ответ от AI модели")
        
        print("\n" + "=" * 80)
        print("ТЕСТ ЗАВЕРШЕН")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n[ERROR] Ошибка при выполнении теста: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Не закрываем браузер (как требуется)
        print("\n[INFO] Браузер остается открытым")
        # Закрываем только Ollama клиент
        await ollama_client.close()


if __name__ == "__main__":
    asyncio.run(test_agent())

