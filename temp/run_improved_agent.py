"""
Простой скрипт для запуска улучшенного агента поиска ИНН.
Использует все улучшения по рекомендациям COMET.
"""
import sys
import warnings
import os

# АГРЕССИВНОЕ подавление всех ResourceWarning и asyncio warnings
# ДОЛЖНО БЫТЬ ДО ИМПОРТА asyncio!
warnings.filterwarnings("ignore")
os.environ["PYTHONWARNINGS"] = "ignore"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

# Подавляем stderr для asyncio warnings ДО импорта asyncio
class SuppressAsyncioWarnings:
    def __init__(self, original):
        self.original = original
    
    def write(self, s):
        if s:
            # Фильтруем все asyncio warnings
            text = str(s)
            if "Exception ignored" in text:
                return
            if "_ProactorBasePipeTransport" in text:
                return
            if "BaseSubprocessTransport" in text:
                return
            if "I/O operation on closed pipe" in text:
                return
            if "unclosed transport" in text:
                return
            if "ValueError: I/O operation on closed pipe" in text:
                return
        self.original.write(s)
    
    def flush(self):
        self.original.flush()
    
    def __getattr__(self, name):
        return getattr(self.original, name)

# Применяем фильтр ДО всех импортов
sys.stderr = SuppressAsyncioWarnings(sys.stderr)

# Теперь импортируем остальное
import asyncio
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
ollama_dir = project_root / "ollama_inn_extractor"
if ollama_dir.exists() and str(ollama_dir) not in sys.path:
    sys.path.insert(0, str(ollama_dir))

from app.agents.interactive_inn_finder import InteractiveINNFinder
from app.ollama_client import OllamaClient

def _is_likely_domain(text: str) -> bool:
    """Определяет, похож ли текст на домен для поиска ИНН.
    
    Args:
        text: Введенный текст
        
    Returns:
        True если похоже на домен, False если это вопрос
    """
    text = text.strip().lower()
    
    # Если содержит специальные символы вопроса - это вопрос
    if any(char in text for char in ['?', '?', 'что', 'как', 'почему', 'когда', 'где', 'кто', 'объясни', 'расскажи']):
        return False
    
    # Если слишком длинный (больше 50 символов) - вероятно вопрос
    if len(text) > 50:
        return False
    
    # Если содержит пробелы и больше 2 слов - вероятно вопрос
    words = text.split()
    if len(words) > 2:
        return False
    
    # Если содержит точку и похоже на домен (например: mc.ru, example.com)
    if '.' in text and len(text.split('.')) <= 3:
        # Проверяем, что это не URL с протоколом (но это тоже домен)
        if text.startswith(('http://', 'https://')):
            return True
        # Проверяем, что части домена не слишком длинные
        parts = text.split('.')
        if all(len(part) <= 63 for part in parts):  # Максимальная длина части домена
            return True
    
    # Если короткий текст без пробелов - может быть домен
    if len(text) <= 30 and ' ' not in text and '.' in text:
        return True
    
    # По умолчанию считаем вопросом
    return False

async def main(domain: str = None, start_url: str = None):
    # Параметры (можно изменить или передать через аргументы)
    import sys
    
    if domain and start_url:
        DOMAIN = domain
        START_URL = start_url
    elif len(sys.argv) >= 3:
        DOMAIN = sys.argv[1]
        START_URL = sys.argv[2]
    elif len(sys.argv) >= 2:
        DOMAIN = sys.argv[1]
        # Автоматически добавляем https:// если нет
        if not DOMAIN.startswith(('http://', 'https://')):
            START_URL = f"https://{DOMAIN}"
        else:
            START_URL = DOMAIN
            # Извлекаем домен из URL
            from urllib.parse import urlparse
            parsed = urlparse(START_URL)
            DOMAIN = parsed.netloc or parsed.path.split('/')[0]
    else:
        # Значения по умолчанию
        DOMAIN = "mc.ru"
        START_URL = "https://mc.ru"
    
    CHROME_CDP_URL = "http://127.0.0.1:9222"  # Chrome должен быть запущен с --remote-debugging-port=9222
    
    print("=" * 80)
    print("Улучшенный агент поиска ИНН (по рекомендациям COMET)")
    print("=" * 80)
    print(f"\nДомен: {DOMAIN}")
    print(f"URL: {START_URL}")
    print(f"Chrome CDP: {CHROME_CDP_URL}")
    print(f"\nВремя начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nУлучшения:")
    print("  ✓ networkidle2 для всех страниц")
    print("  ✓ Retry логика с экспоненциальной задержкой")
    print("  ✓ Поиск в мета-тегах (title, description, keywords)")
    print("  ✓ Поиск через CSS селекторы для контактных блоков")
    print("  ✓ Улучшенная обработка динамического контента")
    print("  ✓ Детальное логирование")
    print("  ✓ Оптимизированные таймауты (120s общий, 20s AI, 30s действие)")
    print("\n" + "=" * 80)
    print("Запуск агента...")
    print("=" * 80 + "\n")
    
    start_time = datetime.now()
    
    try:
        # Инициализация (используем модель из настроек или по умолчанию)
        from app.config import settings
        
        # Определить стратегию из аргументов или использовать universal по умолчанию
        strategy = "universal"  # По умолчанию используем быструю стратегию
        interactive_mode = False
        
        if len(sys.argv) >= 4:
            strategy_arg = sys.argv[3].lower()
            if strategy_arg in ["universal", "interactive"]:
                strategy = strategy_arg
        
        # Проверка флага --interactive или -i
        if "--interactive" in sys.argv or "-i" in sys.argv:
            interactive_mode = True
            import os
            os.environ["INN_AGENT_INTERACTIVE"] = "true"
        
        if interactive_mode:
            print(f"Strategy: {strategy} (interactive mode enabled)")
        else:
            print(f"Strategy: {strategy}")
        
        # Всегда создаем OllamaClient для интерактивного режима (даже если strategy=universal)
        ollama_client = OllamaClient(base_url="http://127.0.0.1:11434", model_name=settings.MODEL_NAME)
        finder = InteractiveINNFinder(
            chrome_cdp_url=CHROME_CDP_URL,
            ollama_client=ollama_client if strategy == "interactive" else None,
            max_attempts=15,
            strategy=strategy
        )
        
        # Поиск ИНН
        result = await finder.find_inn(
            domain=DOMAIN,
            start_url=START_URL,
            timeout=120  # 120 секунд (2 минуты)
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Результаты
        print("\n" + "=" * 80)
        print("РЕЗУЛЬТАТЫ")
        print("=" * 80)
        print(f"Время выполнения: {duration:.2f} секунд ({duration/60:.2f} минут)")
        print(f"Успех: {'✅ ДА' if result.get('success') else '❌ НЕТ'}")
        print(f"ИНН: {result.get('inn') or 'НЕ НАЙДЕН'}")
        print(f"URL: {result.get('url') or 'N/A'}")
        print(f"Попыток: {result.get('attempts', 0)}")
        
        if result.get('context'):
            context = result.get('context', '')[:200]
            print(f"Контекст: {context}...")
        
        if result.get('actions_taken'):
            print(f"\nВыполнено действий: {len(result.get('actions_taken', []))}")
            print("Последние действия:")
            for action in result.get('actions_taken', [])[-5:]:
                print(f"  - {action}")
        
        if result.get('error'):
            print(f"\nОшибка: {result.get('error')}")
        
        print("\n" + "=" * 80)
        print("⚠️  ВАЖНО: Браузер НЕ закрыт - окно остается открытым!")
        print("=" * 80)
        
        # Не закрываем браузер (как требуется)
        # close() только отключает соединение, но браузер остается открытым
        try:
            await finder.close()
        except Exception as e:
            # Игнорируем ошибки закрытия (asyncio warnings)
            pass
        
        # НЕ закрываем ollama_client - он нужен для интерактивного режима!
        # if ollama_client:
        #     try:
        #         await ollama_client.close()
        #     except Exception as e:
        #         pass
        
        print("\n✅ Первый поиск завершен. Браузер остается открытым для повторного использования.")
        
        # Сохраняем контекст для интерактивного режима
        agent_context = {
            "last_search": {
                "domain": DOMAIN,
                "url": result.get("url", ""),
                "inn": result.get("inn"),
                "success": result.get("success", False),
                "phase": result.get("phase", ""),
                "actions": result.get("actions_taken", [])
            },
            "search_history": []
        }
        
        # ИНТЕРАКТИВНЫЙ РЕЖИМ - агент остается активным
        print("\n" + "=" * 80)
        print("💬 ИНТЕРАКТИВНЫЙ РЕЖИМ")
        print("=" * 80)
        print("Агент остается активным. Вы можете:")
        print("  - Ввести домен (например: mc.ru) для поиска ИНН")
        print("  - Задать вопрос агенту (например: 'Что такое ИНН?' или 'Как работает поиск?')")
        print("  - Ввести 'exit' или 'quit' для выхода")
        print("  - Ввести 'help' для справки")
        print("=" * 80 + "\n")
        
        while True:
            try:
                # Используем asyncio.to_thread для input() в async функции
                user_input = await asyncio.to_thread(input, "Агент> ")
                user_input = user_input.strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("\n👋 До свидания!")
                    break
                
                if user_input.lower() in ['help', 'h', '?']:
                    print("\n📖 Справка:")
                    print("  - Введите домен (например: mc.ru) для поиска ИНН")
                    print("  - Задайте вопрос агенту (например: 'Что такое ИНН?')")
                    print("  - 'exit' или 'quit' - выход")
                    print("  - 'help' - эта справка")
                    print()
                    continue
                
                # Определяем, это домен для поиска ИНН или вопрос для AI
                is_domain = _is_likely_domain(user_input)
                
                if is_domain:
                    # Новый поиск ИНН
                    print(f"\n🔍 Поиск ИНН для домена: {user_input}")
                    print("-" * 80)
                    
                    # Извлекаем домен из ввода
                    domain = user_input
                    if domain.startswith(('http://', 'https://')):
                        from urllib.parse import urlparse
                        parsed = urlparse(domain)
                        domain = parsed.netloc or parsed.path.split('/')[0]
                    
                    # Запускаем поиск
                    new_result = await finder.find_inn(
                        domain=domain,
                        start_url=f"https://{domain}" if not user_input.startswith(('http://', 'https://')) else user_input,
                        timeout=120
                    )
                    
                    # Обновляем контекст
                    agent_context["last_search"] = {
                        "domain": domain,
                        "url": new_result.get("url", ""),
                        "inn": new_result.get("inn"),
                        "success": new_result.get("success", False),
                        "phase": new_result.get("phase", ""),
                        "actions": new_result.get("actions_taken", [])
                    }
                    agent_context["search_history"].append({
                        "domain": domain,
                        "inn": new_result.get("inn"),
                        "success": new_result.get("success", False)
                    })
                    
                    # Показываем результат
                    print("\n" + "=" * 80)
                    print("РЕЗУЛЬТАТЫ")
                    print("=" * 80)
                    print(f"Успех: {'✅ ДА' if new_result.get('success') else '❌ НЕТ'}")
                    print(f"ИНН: {new_result.get('inn') or 'НЕ НАЙДЕН'}")
                    print(f"URL: {new_result.get('url') or 'N/A'}")
                    if new_result.get('context'):
                        context = new_result.get('context', '')[:200]
                        print(f"Контекст: {context}...")
                    print("=" * 80 + "\n")
                else:
                    # Это вопрос для AI
                    print(f"\n💬 Вопрос агенту: {user_input}")
                    print("-" * 80)
                    print("🤔 Агент думает...")
                    
                    # Подготавливаем контекст для ответа
                    last_inn = agent_context['last_search']['inn'] or "не найден"
                    last_domain = agent_context['last_search']['domain']
                    last_phase = agent_context['last_search']['phase'] or "неизвестно"
                    
                    # ВСЕГДА пытаемся использовать AI (Ollama должен быть доступен)
                    ai_response = None
                    try:
                        from app.config import settings
                        
                        # Проверяем доступность Ollama
                        print("[INFO] Проверка доступности Ollama...")
                        test_client = OllamaClient(
                            base_url="http://127.0.0.1:11434",
                            model_name=settings.MODEL_NAME,
                            timeout=5
                        )
                        ollama_available = await test_client.check_health()
                        await test_client.close()
                        
                        if not ollama_available:
                            print("[ERROR] ОШИБКА: Ollama недоступен!")
                            print("   Убедитесь, что Ollama запущен: ollama serve")
                            print("   Или проверьте: curl http://127.0.0.1:11434/api/tags")
                            raise ConnectionError("Ollama недоступен")
                        
                        print(f"[INFO] [OK] Ollama доступен, используем модель: {settings.MODEL_NAME}")
                        
                        # Формируем промпт с контекстом
                        context_prompt = f"""Ты агент поиска ИНН. Нашел ИНН {last_inn} для {last_domain} через {last_phase}.

Алгоритм: Phase 1 (локальный) → Phase 2 (Checko.ru) → Phase 3 (Google) → Phase 4 (проверка).

Вопрос: {user_input}

Ответь кратко (до 100 слов)."""
                        
                        # Используем модель из конфига
                        ai_client = OllamaClient(
                            base_url="http://127.0.0.1:11434",
                            model_name=settings.MODEL_NAME,
                            timeout=30  # Увеличиваем timeout для надежности
                        )
                        
                        # Получаем ответ от AI
                        print(f"[INFO] Отправка запроса к модели {settings.MODEL_NAME}...")
                        ai_response = await asyncio.wait_for(
                            ai_client.generate(prompt=context_prompt),
                            timeout=60  # 60 секунд на ответ
                        )
                        await ai_client.close()
                        
                        print("\n" + "=" * 80)
                        print("ОТВЕТ АГЕНТА (от AI модели)")
                        print("=" * 80)
                        print(ai_response)
                        print("=" * 80 + "\n")
                        
                    except asyncio.TimeoutError:
                        print("\n[TIMEOUT] Таймаут ответа от AI (60 сек)")
                        print("   Модель отвечает слишком долго. Использую ответ на основе контекста...")
                    except ConnectionError as conn_error:
                        print(f"\n[ERROR] ОШИБКА ПОДКЛЮЧЕНИЯ: {conn_error}")
                        print("   Использую ответ на основе контекста...")
                    except Exception as ai_error:
                        print(f"\n[ERROR] ОШИБКА AI: {ai_error}")
                        print("   Использую ответ на основе контекста...")
                    
                    # Если AI не ответил - используем fallback на основе контекста
                    if not ai_response:
                        if "алгоритм" in user_input.lower() or "как" in user_input.lower() or "определи" in user_input.lower() or "вычислил" in user_input.lower():
                            response = f"""Алгоритм поиска ИНН (4 фазы):

1. Phase 1: Локальный поиск на сайте {last_domain} (meta tags, footer, comprehensive search)
2. Phase 2: Checko.ru (самый надежный) - поиск "checko {last_domain}" → проверка "Веб-сайты" → извлечение ИНН
3. Phase 3: Google "ИНН {last_domain}" - поиск в сниппетах результатов
4. Phase 4: Проверка первых 3 результатов Google

Для {last_domain} ИНН {last_inn} найден через {last_phase}."""
                        else:
                            response = f"Я только что нашел ИНН {last_inn} для {last_domain} через {last_phase}. Что именно вас интересует?"
                        
                        print("\n" + "=" * 80)
                        print("ОТВЕТ АГЕНТА (на основе контекста)")
                        print("=" * 80)
                        print(response)
                        print("=" * 80 + "\n")
                
            except KeyboardInterrupt:
                print("\n\n👋 Прервано пользователем. До свидания!")
                break
            except EOFError:
                # Ctrl+Z или закрытие stdin
                print("\n\n👋 До свидания!")
                break
            except Exception as e:
                print(f"\n❌ Ошибка: {e}")
                print("Попробуйте еще раз или введите 'exit' для выхода.\n")
        
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        print("\n⚠️  Браузер НЕ закрыт - окно остается открытым даже при ошибке!")

if __name__ == "__main__":
    try:
        # Если запущено из bat-файла, не спрашиваем подтверждение
        if len(sys.argv) > 1:
            # Запущено с аргументами - сразу работаем
            asyncio.run(main())
        else:
            # Интерактивный режим
            print("⚠️  ВАЖНО: Убедитесь, что Chrome запущен с параметром:")
            print("   chrome.exe --remote-debugging-port=9222 --no-first-run")
            print("\n   Или используйте скрипт: .\\scripts\\start-chrome.bat\n")
            
            input("Нажмите Enter для продолжения...")
            
            asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Прервано пользователем. До свидания!")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

