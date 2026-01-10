"""
ПОЛНЫЙ ТЕСТОВЫЙ СКРИПТ COMET CDP
Автоматизация Comet через Chrome DevTools Protocol
"""
import asyncio
import subprocess
import requests
import csv
import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path
import json
import re


def _now_tag() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

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
        logging.FileHandler('comet_test.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class CometCDPTester:
    """Тестер Comet через CDP."""
    
    def __init__(self):
        self.cdp_url = "http://127.0.0.1:9222"
        self.comet_path = Path(os.environ.get('LOCALAPPDATA', '')) / 'Perplexity' / 'Comet' / 'Application' / 'comet.exe'
        self.temp_profile = Path('./comet-temp-profile')
        self.results_file = 'results.csv'
        self.domains_file = 'domains.txt'
        
        logger.info("🚀 CometCDPTester инициализирован")
        logger.info(f"📍 Путь к Comet: {self.comet_path}")
        logger.info(f"📍 CDP URL: {self.cdp_url}")
        logger.info(f"📍 Временный профиль: {self.temp_profile}")
    
    def check_cdp_available(self) -> bool:
        """Проверить доступность CDP."""
        try:
            response = requests.get(f"{self.cdp_url}/json", timeout=5)
            if response.status_code == 200:
                targets = response.json()
                if targets:
                    logger.info(f"✅ CDP доступен, найдено {len(targets)} целей")
                    return True
            return False
        except Exception as e:
            logger.warning(f"⚠️ CDP недоступен: {e}")
            return False
    
    def launch_comet_with_cdp(self) -> bool:
        """Запустить Comet с CDP."""
        try:
            if not self.comet_path.exists():
                logger.error(f"❌ Comet не найден по пути: {self.comet_path}")
                return False
            
            # Создаем временную папку профиля
            self.temp_profile.mkdir(exist_ok=True)
            
            # Аргументы запуска
            cmd = [
                str(self.comet_path),
                '--remote-debugging-port=9222',
                '--remote-debugging-address=127.0.0.1',
                f'--user-data-dir={self.temp_profile.absolute()}',
                '--no-first-run',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
            
            logger.info(f"🚀 Запуск Comet с CDP...")
            logger.info(f"📍 Команда: {' '.join(cmd)}")
            
            # Запуск процесса
            self.comet_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            
            # Ждем запуска
            logger.info("⏳ Ожидаю запуска Comet...")
            for i in range(30):  # 30 секунд
                time.sleep(1)
                if self.check_cdp_available():
                    logger.info(f"✅ Comet запущен с CDP через {i+1} секунд")
                    return True
                logger.info(f"   ⏳ Проверка {i+1}/30...")
            
            logger.error("❌ Comet не запустился с CDP за 30 секунд")
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска Comet: {e}")
            return False
    
    async def launch_or_connect_comet(self) -> Playwright:
        """Подключиться или запустить Comet."""
        logger.info("🔗 Подключение к Comet CDP...")
        
        # Проверяем доступность CDP
        if not self.check_cdp_available():
            logger.info("📍 CDP недоступен, запускаю Comet...")
            if not self.launch_comet_with_cdp():
                raise Exception("Не удалось запустить Comet с CDP")
        
        # Подключаемся через Playwright
        logger.info("📍 Подключаюсь через Playwright CDP...")
        playwright = await async_playwright().start()
        
        try:
            browser = await playwright.chromium.connect_over_cdp(self.cdp_url)
            logger.info("✅ Подключено к Comet через CDP")
            return browser
        except Exception as e:
            logger.error(f"❌ Ошибка подключения CDP: {e}")
            await playwright.stop()
            raise
    
    async def process_domain(self, browser, domain: str) -> dict:
        """Обработать домен."""
        start_time = time.time()
        result = {
            'domain': domain,
            'inn': '',
            'email': '',
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': '',
            'execution_time': 0
        }
        
        try:
            logger.info(f"🌐 Обработка домена: {domain}")
            
            # Создаем контекст и страницу
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            # Открываем домен
            url = f"https://{domain}"
            logger.info(f"📍 Открытие: {url}")
            await page.goto(url, timeout=30000, wait_until='domcontentloaded')
            await page.wait_for_timeout(3000)  # Ждем загрузки

            async def dump_html(tag: str):
                try:
                    debug_dir = Path("cdp_debug")
                    debug_dir.mkdir(exist_ok=True)
                    html = await page.content()
                    p = debug_dir / f"{_now_tag()}_{domain}_{tag}.html"
                    p.write_text(html, encoding="utf-8")
                    logger.info(f"🧾 HTML dump saved: {p}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to dump HTML: {e}")

            # Always open assistant explicitly
            logger.info("📍 Ctrl+J - открытие ассистента...")
            await page.keyboard.press('Control+J')
            await page.wait_for_timeout(1500)
            
            # Ищем ассистент - пробуем разные селекторы
            async def find_assistant_input():
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
                        y_ok = box["y"] > 1080 * 0.40
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

            assistant_input = await find_assistant_input()
            if not assistant_input:
                await dump_html("assistant_input_not_found")
                raise Exception("Ассистент не найден (или найденное поле выглядит как поле сайта, а не ассистента)")
            
            # Вводим промпт
            prompt = f"Найди ИНН и email компании на этой странице. Верни ТОЛЬКО: {domain} | ИНН:xxx | Email:yyy | Найдено:да/нет"
            logger.info(f"🤖 Ввод промпта: {prompt[:50]}...")

            # Collect responses before send
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

            # Focus & clear input (ElementHandle has no .clear())
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
            await page.wait_for_timeout(300)

            # Отправляем
            await page.keyboard.press('Enter')
            logger.info("✅ Промпт отправлен")

            # Ждем новый ответ (строго)
            logger.info("⏳ Ожидаю новый ответ ассистента (таймаут 25с)...")
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
                await dump_html("assistant_no_response")
                raise Exception("Ассистент не дал новый ответ (или селекторы ответа не найдены)")
            
            # Парсим ответ (только из ответа ассистента)
            parsed = self.parse_response(response_text, domain)
            result.update(parsed)
            result['domain'] = domain
            result['timestamp'] = datetime.now().isoformat()
            result['status'] = 'success' if result.get('inn') or result.get('email') else 'no_data'
            
            # Закрываем контекст
            await context.close()
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки {domain}: {e}")
            result['error'] = str(e)
        
        finally:
            result['execution_time'] = time.time() - start_time
            logger.info(f"📊 Результат для {domain}: {result}")
        
        return result
    
    def parse_response(self, response_text: str, domain: str) -> dict:
        """Распарсить ответ."""
        result = {'inn': '', 'email': ''}
        
        try:
            # Ищем формат: domain | ИНН:xxx | Email:yyy | Найдено:да/нет
            if domain in response_text:
                # Извлекаем ИНН
                import re
                inn_match = re.search(r'ИНН:(\d+)', response_text)
                if inn_match:
                    result['inn'] = inn_match.group(1)
                
                # Извлекаем email
                email_match = re.search(r'Email:([^\s|]+)', response_text)
                if email_match:
                    result['email'] = email_match.group(1)
                
                # Если формат не найден, ищем ИНН и email в тексте
                if not result['inn']:
                    inn_patterns = [r'\b\d{10}\b', r'\b\d{12}\b']
                    for pattern in inn_patterns:
                        matches = re.findall(pattern, response_text)
                        if matches:
                            result['inn'] = matches[0]
                            break
                
                if not result['email']:
                    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                    email_matches = re.findall(email_pattern, response_text)
                    if email_matches:
                        result['email'] = email_matches[0]
        
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга ответа: {e}")
        
        return result
    
    def save_results(self, results: list):
        """Сохранить результаты в CSV."""
        try:
            with open(self.results_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['domain', 'inn', 'email', 'status', 'timestamp', 'error', 'execution_time']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
            
            logger.info(f"✅ Результаты сохранены в {self.results_file}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения результатов: {e}")
    
    def create_domains_file(self):
        """Создать файл с доменами."""
        domains = [
            "metallsnab-nn.ru",           # Металлоснабжение Нижний Новгород
            "promsnab.ru",                 # Промснаб
            "stroysnab.ru",                # Стройснаб
            "electrosnab.ru",              # Электроснаб
            "medsnab.ru",                  # Медснаб
            "gazsnab.ru",                  # Газснаб
            "neftesnab.ru",                # Нефтеснаб
            "promresurs.ru",               # Промресурс
            "torgsnab.ru",                 # Торгснаб
            "techsnab.ru",                 # Техснаб
            "energosnab.ru",               # Энергоснаб
            "russnab.ru",                  # Русснаб
            "mirsnab.ru",                  # Мирснаб
            "region-snab.ru",              # Регион-снаб
            "komplekt-snab.ru"             # Комплект-снаб
        ]
        
        try:
            with open(self.domains_file, 'w', encoding='utf-8') as f:
                for domain in domains:
                    f.write(f"{domain}\n")
            
            logger.info(f"✅ Создан файл {self.domains_file} с {len(domains)} доменами")
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания файла доменов: {e}")
    
    def cleanup(self):
        """Очистка ресурсов."""
        try:
            # Закрываем процесс Comet
            if hasattr(self, 'comet_process'):
                logger.info("📍 Закрытие процесса Comet...")
                self.comet_process.terminate()
                self.comet_process.wait(timeout=10)
            
            # Удаляем временный профиль
            if self.temp_profile.exists():
                import shutil
                shutil.rmtree(self.temp_profile, ignore_errors=True)
                logger.info("📍 Временный профиль удален")
            
        except Exception as e:
            logger.error(f"❌ Ошибка очистки: {e}")
    
    async def run_test(self):
        """Запустить тест."""
        logger.info("🚀 ЗАПУСК ТЕСТА COMET CDP")
        logger.info("="*60)
        
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("❌ Playwright не установлен. Установите: pip install playwright")
            return
        
        # Создаем файл доменов
        self.create_domains_file()
        
        # Читаем домены
        try:
            with open(self.domains_file, 'r', encoding='utf-8') as f:
                domains = [line.strip() for line in f if line.strip()]
            
            logger.info(f"📋 Прочитано доменов: {len(domains)}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка чтения доменов: {e}")
            return
        
        browser = None
        results = []
        
        try:
            # Подключаемся к Comet
            browser = await self.launch_or_connect_comet()
            
            # Обрабатываем домены
            for i, domain in enumerate(domains[:5], 1):  # Первые 5 доменов
                logger.info(f"\n📍 Домен {i}/{len(domains[:5])}: {domain}")
                result = await self.process_domain(browser, domain)
                results.append(result)
                
                # Небольшая пауза между доменами
                if i < len(domains[:5]):
                    await asyncio.sleep(2)
            
            # Сохраняем результаты
            self.save_results(results)
            
            # Выводим итоги
            logger.info("\n📊 ИТОГИ ТЕСТА:")
            logger.info("="*40)
            
            success_count = sum(1 for r in results if r['status'] == 'success')
            no_data_count = sum(1 for r in results if r['status'] == 'no_data')
            error_count = sum(1 for r in results if r['status'] == 'error')
            
            logger.info(f"✅ Успешно: {success_count}")
            logger.info(f"⚠️ Нет данных: {no_data_count}")
            logger.info(f"❌ Ошибки: {error_count}")
            logger.info(f"📁 Результаты: {self.results_file}")
            logger.info(f"📋 Логи: comet_test.log")
            
            for result in results:
                status_icon = "✅" if result['status'] == 'success' else "⚠️" if result['status'] == 'no_data' else "❌"
                logger.info(f"   {status_icon} {result['domain']}: ИНН={result['inn']}, Email={result['email']}")
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка теста: {e}")
        
        finally:
            # Закрываем браузер
            if browser:
                await browser.close()
            
            # Очистка
            self.cleanup()
            
            logger.info("\n🎉 ТЕСТ ЗАВЕРШЕН!")


async def main():
    """Главная функция."""
    tester = CometCDPTester()
    await tester.run_test()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⚠️ Тест прерван")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
