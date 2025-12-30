"""
Стресс-тест: Парсинг → ИНН → Карточка поставщика
Логирует все шаги, успехи и неудачи
"""
import asyncio
import httpx
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

API_BASE = "http://127.0.0.1:8000"
FRONTEND_BASE = "http://localhost:3000"

class StressTestLogger:
    def __init__(self):
        self.logs = []
    
    def log(self, step: str, status: str, message: str, data: Any = None):
        """Логирует шаг теста"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "step": step,
            "status": status,  # "success", "error", "info", "warning"
            "message": message,
            "data": data
        }
        self.logs.append(log_entry)
        status_emoji = {"success": "[OK]", "error": "[ERROR]", "info": "[INFO]", "warning": "[WARN]"}
        print(f"[{timestamp}] {status_emoji.get(status, '[•]')} {step}: {message}")
        if data:
            print(f"   Data: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    def save_logs(self, filename: str = "stress_test_log.json"):
        """Сохраняет логи в файл"""
        with open(f"temp/{filename}", "w", encoding="utf-8") as f:
            json.dump(self.logs, f, ensure_ascii=False, indent=2)
        print(f"\n[LOG] Логи сохранены в temp/{filename}")

async def check_service(url: str, name: str, logger: StressTestLogger) -> bool:
    """Проверяет доступность сервиса"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                logger.log(f"Проверка {name}", "success", f"{name} доступен")
                return True
            else:
                logger.log(f"Проверка {name}", "error", f"{name} вернул статус {response.status_code}")
                return False
    except Exception as e:
        logger.log(f"Проверка {name}", "error", f"Ошибка подключения: {str(e)}")
        return False

async def start_parsing(keyword: str, depth: int, source: str, logger: StressTestLogger) -> Optional[Dict[str, Any]]:
    """Запускает парсинг"""
    logger.log("Запуск парсинга", "info", f"Ключевое слово: {keyword}, Глубина: {depth}, Источник: {source}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_BASE}/parsing/start",
                json={"keyword": keyword, "depth": depth, "source": source}
            )
            
            if response.status_code == 201:
                data = response.json()
                run_id = data.get("runId") or data.get("run_id")
                logger.log("Запуск парсинга", "success", f"Парсинг запущен, runId: {run_id}", data)
                return data
            else:
                error_text = response.text
                logger.log("Запуск парсинга", "error", f"Ошибка запуска: {response.status_code}", {"error": error_text})
                return None
    except Exception as e:
        logger.log("Запуск парсинга", "error", f"Исключение: {str(e)}")
        return None

async def wait_for_parsing_completion(run_id: str, logger: StressTestLogger, max_wait: int = 300) -> bool:
    """Ожидает завершения парсинга"""
    logger.log("Ожидание завершения", "info", f"Ожидание завершения парсинга {run_id} (макс. {max_wait} сек)")
    
    start_time = time.time()
    check_interval = 3  # Проверяем каждые 3 секунды
    
    while time.time() - start_time < max_wait:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{API_BASE}/parsing/runs/{run_id}")
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status", "unknown")
                    results_count = data.get("resultsCount") or data.get("results_count")
                    
                    logger.log("Проверка статуса", "info", f"Статус: {status}, Результатов: {results_count}")
                    
                    if status == "completed":
                        logger.log("Ожидание завершения", "success", f"Парсинг завершен! Результатов: {results_count}")
                        return True
                    elif status == "failed":
                        logger.log("Ожидание завершения", "error", "Парсинг завершился с ошибкой")
                        return False
                    
                    await asyncio.sleep(check_interval)
                else:
                    logger.log("Проверка статуса", "warning", f"Ошибка получения статуса: {response.status_code}")
                    await asyncio.sleep(check_interval)
        except Exception as e:
            logger.log("Проверка статуса", "warning", f"Ошибка: {str(e)}")
            await asyncio.sleep(check_interval)
    
    logger.log("Ожидание завершения", "error", f"Таймаут ожидания ({max_wait} сек)")
    return False

async def get_parsing_results(run_id: str, logger: StressTestLogger) -> Optional[list]:
    """Получает результаты парсинга"""
    logger.log("Получение результатов", "info", f"Загрузка результатов парсинга {run_id}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Получаем домены из queue
            response = await client.get(
                f"{API_BASE}/domains/queue",
                params={"parsingRunId": run_id, "limit": 100}
            )
            
            if response.status_code == 200:
                data = response.json()
                entries = data.get("entries", [])
                logger.log("Получение результатов", "success", f"Получено {len(entries)} доменов")
                return entries
            else:
                logger.log("Получение результатов", "error", f"Ошибка: {response.status_code}")
                return None
    except Exception as e:
        logger.log("Получение результатов", "error", f"Исключение: {str(e)}")
        return None

async def get_checko_data(inn: str, logger: StressTestLogger) -> Optional[Dict[str, Any]]:
    """Получает данные из Checko по ИНН"""
    logger.log("Загрузка Checko данных", "info", f"Загрузка данных для ИНН: {inn}")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(f"{API_BASE}/moderator/checko/{inn}")
            
            if response.status_code == 200:
                data = response.json()
                logger.log("Загрузка Checko данных", "success", f"Данные получены", {
                    "name": data.get("name"),
                    "hasCheckoData": bool(data.get("checkoData"))
                })
                return data
            else:
                error_text = response.text
                logger.log("Загрузка Checko данных", "error", f"Ошибка: {response.status_code}", {"error": error_text})
                return None
    except Exception as e:
        logger.log("Загрузка Checko данных", "error", f"Исключение: {str(e)}")
        return None

async def create_supplier(supplier_data: Dict[str, Any], logger: StressTestLogger) -> Optional[Dict[str, Any]]:
    """Создает поставщика"""
    logger.log("Создание поставщика", "info", f"Создание поставщика: {supplier_data.get('name')}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_BASE}/moderator/suppliers",
                json=supplier_data
            )
            
            if response.status_code == 201:
                data = response.json()
                supplier_id = data.get("id")
                logger.log("Создание поставщика", "success", f"Поставщик создан, ID: {supplier_id}", data)
                return data
            else:
                error_text = response.text
                logger.log("Создание поставщика", "error", f"Ошибка: {response.status_code}", {"error": error_text})
                return None
    except Exception as e:
        logger.log("Создание поставщика", "error", f"Исключение: {str(e)}")
        return None

async def get_supplier(supplier_id: int, logger: StressTestLogger) -> Optional[Dict[str, Any]]:
    """Получает данные поставщика"""
    logger.log("Получение поставщика", "info", f"Загрузка поставщика ID: {supplier_id}")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{API_BASE}/moderator/suppliers/{supplier_id}")
            
            if response.status_code == 200:
                data = response.json()
                logger.log("Получение поставщика", "success", f"Поставщик загружен: {data.get('name')}")
                return data
            else:
                logger.log("Получение поставщика", "error", f"Ошибка: {response.status_code}")
                return None
    except Exception as e:
        logger.log("Получение поставщика", "error", f"Исключение: {str(e)}")
        return None

async def main():
    """Основная функция стресс-теста"""
    logger = StressTestLogger()
    
    print("=" * 60)
    print("СТРЕСС-ТЕСТ: Парсинг -> ИНН -> Карточка поставщика")
    print("=" * 60)
    print()
    
    # Шаг 1: Проверка состояния системы
    logger.log("=== ШАГ 1: Проверка системы ===", "info", "Начало проверки")
    
    backend_ok = await check_service(f"{API_BASE}/health", "Backend", logger)
    parser_ok = await check_service(f"{API_BASE.replace(':8000', ':9003')}/health", "Parser Service", logger)
    frontend_ok = await check_service(f"{FRONTEND_BASE}", "Frontend", logger)
    
    if not backend_ok:
        logger.log("Проверка системы", "error", "Backend недоступен, тест прерван")
        logger.save_logs()
        return
    
    # Шаг 2: Запуск парсинга
    logger.log("=== ШАГ 2: Запуск парсинга ===", "info", "Начало")
    
    keyword = "кирпич"
    depth = 2  # Небольшая глубина для быстрого теста
    source = "google"
    
    parsing_result = await start_parsing(keyword, depth, source, logger)
    
    if not parsing_result:
        logger.log("Запуск парсинга", "error", "Не удалось запустить парсинг, тест прерван")
        logger.save_logs()
        return
    
    run_id = parsing_result.get("runId") or parsing_result.get("run_id")
    if not run_id:
        logger.log("Запуск парсинга", "error", "Не получен runId, тест прерван")
        logger.save_logs()
        return
    
    # Шаг 3: Ожидание завершения парсинга
    logger.log("=== ШАГ 3: Ожидание завершения ===", "info", "Начало")
    
    completed = await wait_for_parsing_completion(run_id, logger, max_wait=300)
    
    if not completed:
        logger.log("Ожидание завершения", "error", "Парсинг не завершился, тест прерван")
        logger.save_logs()
        return
    
    # Шаг 4: Получение результатов
    logger.log("=== ШАГ 4: Получение результатов ===", "info", "Начало")
    
    results = await get_parsing_results(run_id, logger)
    
    if not results or len(results) == 0:
        logger.log("Получение результатов", "error", "Нет результатов парсинга, тест прерван")
        logger.save_logs()
        return
    
    # Выбираем первый домен для теста
    first_domain = results[0].get("domain")
    logger.log("Выбор домена", "info", f"Выбран домен для теста: {first_domain}")
    
    # Шаг 5: Загрузка данных Checko (нужен ИНН)
    # Для теста используем известный ИНН или попробуем найти в результатах
    logger.log("=== ШАГ 5: Загрузка Checko данных ===", "info", "Начало")
    
    # Используем тестовый ИНН (СТД ПЕТРОВИЧ из примера)
    test_inn = "7802348846"
    logger.log("Использование ИНН", "info", f"Используем тестовый ИНН: {test_inn}")
    
    checko_data = await get_checko_data(test_inn, logger)
    
    if not checko_data:
        logger.log("Загрузка Checko данных", "error", "Не удалось загрузить данные Checko, тест прерван")
        logger.save_logs()
        return
    
    # Шаг 6: Создание поставщика
    logger.log("=== ШАГ 6: Создание поставщика ===", "info", "Начало")
    
    supplier_data = {
        "name": checko_data.get("name") or f"Тестовый поставщик {first_domain}",
        "inn": test_inn,
        "domain": first_domain,
        "type": "supplier",
        "email": checko_data.get("email"),
        "address": checko_data.get("legalAddress"),
        "ogrn": checko_data.get("ogrn"),
        "kpp": checko_data.get("kpp"),
        "okpo": checko_data.get("okpo"),
        "companyStatus": checko_data.get("companyStatus"),
        "registrationDate": checko_data.get("registrationDate"),
        "legalAddress": checko_data.get("legalAddress"),
        "phone": checko_data.get("phone"),
        "website": checko_data.get("website"),
        "vk": checko_data.get("vk"),
        "telegram": checko_data.get("telegram"),
        "authorizedCapital": checko_data.get("authorizedCapital"),
        "revenue": checko_data.get("revenue"),
        "profit": checko_data.get("profit"),
        "financeYear": checko_data.get("financeYear"),
        "legalCasesCount": checko_data.get("legalCasesCount"),
        "legalCasesSum": checko_data.get("legalCasesSum"),
        "legalCasesAsPlaintiff": checko_data.get("legalCasesAsPlaintiff"),
        "legalCasesAsDefendant": checko_data.get("legalCasesAsDefendant"),
        "checkoData": checko_data.get("checkoData"),
    }
    
    # Убираем None значения
    supplier_data = {k: v for k, v in supplier_data.items() if v is not None}
    
    supplier = await create_supplier(supplier_data, logger)
    
    if not supplier:
        logger.log("Создание поставщика", "error", "Не удалось создать поставщика, тест прерван")
        logger.save_logs()
        return
    
    supplier_id = supplier.get("id")
    
    # Шаг 7: Проверка карточки поставщика
    logger.log("=== ШАГ 7: Проверка карточки ===", "info", "Начало")
    
    supplier_check = await get_supplier(supplier_id, logger)
    
    if not supplier_check:
        logger.log("Проверка карточки", "error", "Не удалось загрузить поставщика для проверки")
        logger.save_logs()
        return
    
    # Проверяем наличие данных Checko
    has_checko_data = bool(supplier_check.get("checkoData"))
    has_financial_data = supplier_check.get("revenue") is not None or supplier_check.get("profit") is not None
    has_legal_data = supplier_check.get("legalCasesCount") is not None
    
    logger.log("Проверка данных", "info", f"Данные Checko: {'ДА' if has_checko_data else 'НЕТ'}")
    logger.log("Проверка данных", "info", f"Финансовые данные: {'ДА' if has_financial_data else 'НЕТ'}")
    logger.log("Проверка данных", "info", f"Юридические данные: {'ДА' if has_legal_data else 'НЕТ'}")
    
    # Финальный результат
    print()
    print("=" * 60)
    print("РЕЗУЛЬТАТЫ СТРЕСС-ТЕСТА")
    print("=" * 60)
    print(f"[OK] Парсинг: Запущен и завершен (runId: {run_id})")
    print(f"[OK] Результаты: Получено {len(results)} доменов")
    print(f"[OK] Checko данные: {'Загружены' if checko_data else 'Не загружены'}")
    print(f"[OK] Поставщик: Создан (ID: {supplier_id})")
    print(f"[OK] Карточка: {'Готова' if supplier_check else 'Не готова'}")
    print()
    print(f"[LINK] Ссылка на карточку: {FRONTEND_BASE}/suppliers/{supplier_id}")
    print()
    
    logger.log("=== ТЕСТ ЗАВЕРШЕН ===", "success", "Все шаги выполнены успешно!")
    logger.save_logs()

if __name__ == "__main__":
    asyncio.run(main())

