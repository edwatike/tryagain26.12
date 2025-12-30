"""Use case for getting Checko data with caching."""
import json
import time
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.adapters.checko_client import CheckoClient
from app.adapters.db.repositories import ModeratorSupplierRepository
from app.utils.checko_compression import compress_checko_data_string, decompress_checko_data_to_string

# TTL для кэша Checko данных (24 часа в секундах)
CHECKO_CACHE_TTL = 24 * 60 * 60


async def execute(
    db: AsyncSession,
    inn: str,
    force_refresh: bool = False
) -> Dict[str, Any]:
    """Get Checko data for company by INN with caching.
    
    Args:
        db: Database session
        inn: Company INN (10 or 12 digits)
        force_refresh: If True, force refresh from API even if cache exists
        
    Returns:
        Checko data in format compatible with frontend:
        {
            "name": str,
            "ogrn": str,
            "kpp": str,
            "okpo": str,
            "companyStatus": str,
            "registrationDate": str,
            "legalAddress": str,
            "phone": str,
            "website": str,
            "vk": str,
            "telegram": str,
            "authorizedCapital": int,
            "revenue": int,
            "profit": int,
            "financeYear": int,
            "legalCasesCount": int,
            "legalCasesSum": int,
            "legalCasesAsPlaintiff": int,
            "legalCasesAsDefendant": int,
            "checkoData": str  # Full JSON data
        }
        
    Raises:
        ValueError: If INN is invalid
        RuntimeError: If Checko API key is not configured
        httpx.HTTPStatusError: If Checko API request fails
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Валидация ИНН
    if not inn or not inn.isdigit() or len(inn) not in [10, 12]:
        raise ValueError("ИНН должен содержать 10 или 12 цифр")
    
    repo = ModeratorSupplierRepository(db)
    
    # Проверяем кэш в БД
    if not force_refresh:
        supplier = await repo.get_by_inn(inn)
        if supplier and supplier.checko_data:
            try:
                # Decompress if it's bytes (compressed), otherwise parse as string
                if isinstance(supplier.checko_data, bytes):
                    checko_data_str = decompress_checko_data_to_string(supplier.checko_data)
                else:
                    checko_data_str = supplier.checko_data
                
                cached_data = json.loads(checko_data_str)
                timestamp = cached_data.get("timestamp", 0)
                current_time = int(time.time())
                
                # Проверяем, не истек ли кэш (24 часа)
                if current_time - timestamp < CHECKO_CACHE_TTL:
                    logger.info(f"Using cached Checko data for INN {inn}")
                    return _format_checko_data_for_frontend(cached_data)
                else:
                    logger.info(f"Checko cache expired for INN {inn}, refreshing from API")
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning(f"Failed to parse cached Checko data for INN {inn}: {e}")
    
    # Кэш невалиден или отсутствует - запрашиваем из API
    logger.info(f"Fetching Checko data from API for INN {inn}")
    
    try:
        client = CheckoClient()
        full_data = await client.get_all_data(inn)
    except ValueError as e:
        if "API key" in str(e):
            raise RuntimeError("Checko API ключ не настроен. Установите CHECKO_API_KEY в переменных окружения.")
        raise
    except Exception as e:
        logger.error(f"Failed to fetch Checko data for INN {inn}: {e}")
        raise
    
    # Добавляем timestamp для кэширования
    full_data["timestamp"] = int(time.time())
    
    # Сохраняем в БД для будущих запросов (сжатое)
    supplier = await repo.get_by_inn(inn)
    if supplier:
        # Обновляем существующего поставщика - сжимаем данные перед сохранением
        checko_data_json = json.dumps(full_data, ensure_ascii=False)
        compressed_data = compress_checko_data_string(checko_data_json)
        supplier.checko_data = compressed_data
        await db.flush()
        logger.info(f"Updated Checko data in DB for supplier ID {supplier.id} "
                   f"(compressed: {len(checko_data_json)} -> {len(compressed_data)} bytes)")
    else:
        # Поставщика нет - просто возвращаем данные без сохранения
        # (можно создать временную запись, но пока просто возвращаем)
        logger.info(f"Supplier with INN {inn} not found in DB, returning data without saving")
    
    # Форматируем данные для frontend
    return _format_checko_data_for_frontend(full_data)


def _format_checko_data_for_frontend(full_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format Checko data for frontend consumption.
    
    Args:
        full_data: Full Checko data from API
        
    Returns:
        Formatted data for frontend
    """
    company_data = full_data
    
    # Извлекаем основные поля
    result = {
        "name": (
            company_data.get("НаимПолн") or 
            company_data.get("НаимСокр") or 
            company_data.get("Наим") or 
            None
        ),
        "ogrn": company_data.get("ОГРН"),
        "kpp": company_data.get("КПП"),
        "okpo": company_data.get("ОКПО"),
        "companyStatus": company_data.get("Статус", {}).get("Наим") if isinstance(company_data.get("Статус"), dict) else None,
        "registrationDate": company_data.get("ДатаРег"),
        "legalAddress": (
            company_data.get("ЮрАдрес") if isinstance(company_data.get("ЮрАдрес"), str)
            else (company_data.get("ЮрАдрес", {}).get("НасПункт") or 
                  company_data.get("ЮрАдрес", {}).get("Адрес") or
                  str(company_data.get("ЮрАдрес", "")) if company_data.get("ЮрАдрес") else None)
            if isinstance(company_data.get("ЮрАдрес"), dict) else None
        ),
        "phone": company_data.get("Контакты", {}).get("Телефон") if isinstance(company_data.get("Контакты"), dict) else None,
        "website": company_data.get("Контакты", {}).get("ВебСайт") if isinstance(company_data.get("Контакты"), dict) else None,
        "vk": company_data.get("Контакты", {}).get("ВК") if isinstance(company_data.get("Контакты"), dict) else None,
        "telegram": company_data.get("Контакты", {}).get("Телеграм") if isinstance(company_data.get("Контакты"), dict) else None,
        "authorizedCapital": None,
        "revenue": None,
        "profit": None,
        "financeYear": None,
        "legalCasesCount": None,
        "legalCasesSum": None,
        "legalCasesAsPlaintiff": None,
        "legalCasesAsDefendant": None,
        "checkoData": json.dumps(full_data, ensure_ascii=False),
    }
    
    # Уставной капитал
    if company_data.get("УстКап") and isinstance(company_data["УстКап"], dict):
        capital = company_data["УстКап"].get("Сумма")
        if capital is not None:
            try:
                result["authorizedCapital"] = int(capital)
            except (ValueError, TypeError):
                pass
    
    # Финансы (последний год)
    finances = full_data.get("_finances", {})
    if finances:
        years = sorted(finances.keys(), reverse=True)
        if years:
            last_year = years[0]
            last_year_data = finances[last_year]
            if isinstance(last_year_data, dict):
                # Выручка (код 2110)
                revenue = last_year_data.get("2110")
                if revenue is not None:
                    try:
                        result["revenue"] = int(revenue)
                    except (ValueError, TypeError):
                        pass
                
                # Прибыль (код 2400)
                profit = last_year_data.get("2400")
                if profit is not None:
                    try:
                        result["profit"] = int(profit)
                    except (ValueError, TypeError):
                        pass
                
                result["financeYear"] = int(last_year) if last_year.isdigit() else None
    
    # Судебные дела
    legal = full_data.get("_legal", {})
    if legal:
        result["legalCasesCount"] = legal.get("ЗапВсего")
        result["legalCasesSum"] = None
        sum_value = legal.get("ОбщСуммИск")
        if sum_value is not None:
            try:
                result["legalCasesSum"] = int(sum_value)
            except (ValueError, TypeError):
                pass
        result["legalCasesAsPlaintiff"] = legal.get("Истец")
        result["legalCasesAsDefendant"] = legal.get("Ответчик")
    
    return result


