"""
ФИНАЛЬНЫЙ ТЕСТ COMET CDP С УЛУЧШЕННЫМ ПАРСЕРОМ
"""
import asyncio
import subprocess
import requests
import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path
import json
import re

try:
    from playwright.async_api import async_playwright, Playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('final_comet_test.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


async def dump_debug_artifacts(page, tag: str) -> None:
    try:
        out_dir = Path("cdp_debug")
        out_dir.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_path = out_dir / f"{ts}_{tag}.html"
        content = await page.content()
        html_path.write_text(content, encoding="utf-8")
        logger.info(f"🧾 HTML dump saved: {html_path}")
    except Exception as e:
        logger.warning(f"⚠️ Failed to dump HTML: {e}")


async def find_assistant_input(page, viewport_height: int):
    candidates = []

    preferred = [
        '[data-testid*="assistant" i] textarea',
        '[data-testid*="assistant" i] input',
        '[data-testid*="chat" i] textarea',
        '[data-testid*="chat" i] input',
        'textarea[placeholder*="ассист" i]',
        'textarea[placeholder*="ask" i]',
        'textarea[placeholder*="вопрос" i]',
        'input[placeholder*="ассист" i]',
        'input[placeholder*="ask" i]',
        'input[placeholder*="вопрос" i]',
    ]

    async def consider(el, sel):
        try:
            if not await el.is_visible():
                return
            box = await el.bounding_box()
            if not box:
                return
            placeholder = await el.get_attribute("placeholder")
            testid = await el.get_attribute("data-testid")
            aria = await el.get_attribute("aria-label")
            meta = " ".join([x for x in [placeholder, testid, aria] if x]).lower()
            semantic_ok = any(k in meta for k in ["assist", "ассист", "chat", "чат", "ask", "вопрос", "prompt"])
            y_ok = box["y"] > viewport_height * 0.40
            score = (5 if semantic_ok else 0) + (2 if y_ok else 0)
            candidates.append((score, box, sel, el, meta))
        except Exception:
            return

    for sel in preferred:
        try:
            els = await page.query_selector_all(sel)
            for el in els:
                await consider(el, sel)
        except Exception:
            continue

    if not candidates:
        for sel in ["textarea", 'input[type="text"]']:
            try:
                els = await page.query_selector_all(sel)
                for el in els:
                    await consider(el, sel)
            except Exception:
                continue

    if not candidates:
        return None

    candidates.sort(key=lambda x: (x[0], x[1]["y"]), reverse=True)
    score, box, sel, el, meta = candidates[0]
    logger.info(f"🎯 Assistant input candidate: selector={sel}, score={score}, box={box}, meta='{meta}'")
    if score < 3:
        return None
    return el

def parse_comet_response(response_text: str, domain: str) -> dict:
    """Распарсить ответ ассистента."""
    result = {
        'domain': domain,
        'inn': '',
        'email': '',
        'phone': '',
        'address': '',
        'company': '',
        'success': False,
        'raw_response': response_text
    }
    
    # Ищем ИНН
    inn_patterns = [
        r'ИНН[:\s]*(\d{10,12})',
        r'ИНН\s*[:\-]?\s*(\d{10,12})',
        r'инн[:\s]*(\d{10,12})',
        r'(\b\d{10}\b)',
        r'(\b\d{12}\b)',
    ]
    
    for pattern in inn_patterns:
        matches = re.findall(pattern, response_text, re.IGNORECASE)
        if matches:
            inn = matches[0] if isinstance(matches[0], str) else matches[0][0]
            inn = re.sub(r'[^\d]', '', str(inn))
            if len(inn) in [10, 12]:
                result['inn'] = inn
                break
    
    # Ищем email
    email_patterns = [
        r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b',
        r'email[:\s]*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        r'E-mail[:\s]*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
    ]
    
    for pattern in email_patterns:
        matches = re.findall(pattern, response_text, re.IGNORECASE)
        if matches:
            result['email'] = matches[0]
            break
    
    # Ищем телефон
    phone_patterns = [
        r'\+?\s*7\s*[\(\s]*(\d{3})[\)\s]*(\d{3})[\s-]*(\d{2})[\s-]*(\d{2})',
        r'8\s*[\(\s]*(\d{3})[\)\s]*(\d{3})[\s-]*(\d{2})[\s-]*(\d{2})',
        r'\+?\d{1,3}[\s-]?\d{3}[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}',
        r'\+?\s*7\s*\(\s*\d{3}\s*\)\s*\d{3}[\s-]*\d{2}[\s-]*\d{2}',
    ]
    
    for pattern in phone_patterns:
        matches = re.findall(pattern, response_text)
        if matches:
            if isinstance(matches[0], tuple):
                phone = ''.join(matches[0])
            else:
                phone = matches[0]
            result['phone'] = phone
            break
    
    # Ищем адрес
    address_patterns = [
        r'(г\.\s*[А-Яа-яё]+\s*[А-Яа-яё\s]+\d+[\s,к\.]*\s*[А-Яа-яё]*)',
        r'(г\.\s*[А-Яа-яё\s]+,\s*ул\.\s*[А-Яа-яё\s]+[\d\s,к\.]*)',
        r'([А-Яа-яё\s]+[«""][А-Яа-яё\s]+[»""]\s*[А-Яа-яё\s]*\d*[\s,к\.]*)',
        r'(г\.\s*[А-Яа-яё\s]+,\s*ш\.\s*[А-Яа-яё\s]+\s*\d+[\s,к\.]*)',
    ]
    
    for pattern in address_patterns:
        matches = re.findall(pattern, response_text)
        if matches:
            result['address'] = matches[0].strip()
            break
    
    # Ищем название компании
    company_patterns = [
        r'([А-Яа-яё\s]+[«""][А-Яа-яё\s]+[»""])',
        r'(ООО\s+[«""][А-Яа-яё\s]+[»""])',
        r'([А-Яа-яё\s]+[«""][А-Яа-яё\s]+[»""])',
        r'©\s*([А-Яа-яё\s]+[А-Яа-яё]*)',
    ]
    
    for pattern in company_patterns:
        matches = re.findall(pattern, response_text)
        if matches:
            result['company'] = matches[0].strip()
            break
    
    # Определяем успех
    result['success'] = bool(result['inn'] or result['email'])
    
    return result

async def test_final_comet():
    """Финальный тест Comet."""
    logger.info("🚀 ФИНАЛЬНЫЙ ТЕСТ COMET CDP")
    logger.info("="*60)
    
    if not PLAYWRIGHT_AVAILABLE:
        logger.error("❌ Playwright не установлен")
        return
    
    # Проверяем CDP
    cdp_url = "http://127.0.0.1:9222"
    try:
        response = requests.get(f"{cdp_url}/json", timeout=5)
        if response.status_code != 200:
            logger.error("❌ CDP недоступен")
            return
        logger.info("✅ CDP доступен")
    except Exception as e:
        logger.error(f"❌ Ошибка CDP: {e}")
        return
    
    # Подключаемся
    playwright = await async_playwright().start()
    browser = await playwright.chromium.connect_over_cdp(cdp_url)
    logger.info("✅ Подключено к Comet")
    
    try:
        # Тестируем metallsnab-nn.ru
        domain = "metallsnab-nn.ru"
        logger.info(f"🌐 Тестирую домен: {domain}")
        
        # Создаем страницу
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        # Открываем домен
        url = f"https://{domain}"
        logger.info(f"📍 Открываю: {url}")
        await page.goto(url, timeout=30000)
        await page.wait_for_timeout(3000)

        # Открываем ассистента
        logger.info("📍 Открываю ассистента: Ctrl+J...")
        await page.keyboard.press('Control+J')
        await page.wait_for_timeout(1500)
        
        # Ищем ассистента
        logger.info("🔍 Ищу ассистента...")
        
        assistant_input = await find_assistant_input(page, viewport_height=1080)
        if not assistant_input:
            await dump_debug_artifacts(page, "assistant_input_not_found")
            logger.error("❌ Ассистент не найден (или найденное поле выглядит как поле сайта)")
            return
        
        # Вводим промпт
        prompt = f"Найди ИНН и email компании на этой странице. Верни контактные данные."
        logger.info(f"🤖 Ввожу промпт: {prompt[:50]}...")
        
        # Снимем состояние ответов до отправки
        response_selectors = [
            '.chat-response',
            '.assistant-response',
            '[data-testid*="chat" i] .message',
            '[data-testid*="chat" i] [data-testid*="response" i]',
            '.response-content',
            '.message-content',
            '.chat-message',
            '.assistant-message'
        ]

        async def collect_responses():
            texts = []
            for sel in response_selectors:
                try:
                    els = await page.query_selector_all(sel)
                    for el in els:
                        t = (await el.inner_text()).strip()
                        if t:
                            texts.append(t)
                except Exception:
                    continue
            uniq = []
            for t in texts:
                if t not in uniq:
                    uniq.append(t)
            return uniq

        before_texts = await collect_responses()
        logger.info(f"🧩 Responses before send: {len(before_texts)}")

        try:
            await assistant_input.click()
        except Exception:
            pass

        try:
            await assistant_input.fill('')
        except Exception:
            await page.keyboard.press('Control+A')
            await page.keyboard.press('Delete')

        await assistant_input.type(prompt, delay=50)
        await page.wait_for_timeout(1000)
        
        # Отправляем
        await assistant_input.press('Enter')
        logger.info("✅ Промпт отправлен")
        
        # Ждем новый ответ ассистента (строго)
        logger.info("⏳ Жду новый ответ ассистента (таймаут 25с)...")
        response_text = ""
        deadline = time.time() + 25
        while time.time() < deadline:
            await page.wait_for_timeout(1000)
            after_texts = await collect_responses()
            new_texts = [t for t in after_texts if t not in before_texts]
            if new_texts:
                response_text = new_texts[-1]
                break

        if not response_text:
            await dump_debug_artifacts(page, "assistant_no_response")
            logger.error("❌ Ассистент не дал нового ответа")
            return

        logger.info(f"📋 Ответ ассистента: {response_text}")
        result = parse_comet_response(response_text, domain)
        
        logger.info("📊 РЕЗУЛЬТАТ:")
        logger.info(f"   Домен: {result['domain']}")
        logger.info(f"   ИНН: {result['inn']}")
        logger.info(f"   Email: {result['email']}")
        logger.info(f"   Телефон: {result['phone']}")
        logger.info(f"   Адрес: {result['address']}")
        logger.info(f"   Компания: {result['company']}")
        logger.info(f"   Успех: {result['success']}")
        
        if result['success']:
            logger.info("🎉 УСПЕХ - Данные найдены!")
        else:
            logger.warning("⚠️ Данные не найдены")
        
        # Сохраняем результат
        with open('final_result.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info("✅ Результат сохранен в final_result.json")
        
        # Закрываем контекст
        await context.close()
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
    
    finally:
        await browser.close()
        logger.info("🎉 ТЕСТ ЗАВЕРШЕН!")

async def main():
    """Главная функция."""
    await test_final_comet()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⚠️ Тест прерван")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
