"""Domain Info Parser - извлекает ИНН и email с веб-страниц."""
import re
import asyncio
from typing import Optional, Dict, List
from urllib.parse import urljoin, urlparse
import logging

from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeout

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DomainInfoParser:
    """Парсер для извлечения ИНН и email с доменов."""
    
    def __init__(self, headless: bool = True, timeout: int = 15000):
        """
        Args:
            headless: Запускать браузер в headless режиме
            timeout: Таймаут загрузки страницы в миллисекундах
        """
        self.headless = headless
        self.timeout = timeout
        self.browser: Optional[Browser] = None
        self.playwright = None
        
    async def start(self):
        """Запустить браузер."""
        logger.info("Запуск Playwright...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        logger.info("✅ Браузер запущен")
        
    async def close(self):
        """Закрыть браузер."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("✅ Браузер закрыт")
    
    def extract_inn(self, text: str) -> Optional[str]:
        """Извлечь ИНН из текста с улучшенными паттернами."""
        # Расширенные паттерны для поиска ИНН с контекстом
        inn_patterns = [
            # Прямое упоминание ИНН
            r'ИНН[:\s]+(\d{10}|\d{12})',
            r'INN[:\s]+(\d{10}|\d{12})',
            r'инн[:\s]+(\d{10}|\d{12})',
            # С разделителями
            r'ИНН[:\s]+(\d{4}[\s\-]?\d{6})',  # ИНН: 1234 567890
            r'ИНН[:\s]+(\d{4}[\s\-]?\d{4}[\s\-]?\d{4})',  # ИНН: 1234 5678 9012
            # В таблицах/реквизитах
            r'(?:реквизит|requisite|details).*?ИНН[:\s]*(\d{10}|\d{12})',
            r'(?:реквизит|requisite|details).*?INN[:\s]*(\d{10}|\d{12})',
            # Рядом с ОГРН/КПП
            r'(?:ОГРН|OGRN).*?ИНН[:\s]*(\d{10}|\d{12})',
            r'(?:КПП|KPP).*?ИНН[:\s]*(\d{10}|\d{12})',
            # В контактах/о компании
            r'(?:о компании|about|контакт|contact).*?ИНН[:\s]*(\d{10}|\d{12})',
        ]
        
        # Ищем с явным упоминанием ИНН
        for pattern in inn_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                # Убираем пробелы и дефисы
                clean_match = re.sub(r'[\s\-]', '', match)
                if len(clean_match) in [10, 12]:
                    logger.info(f"Found INN with pattern: {clean_match}")
                    return clean_match
        
        # Поиск в контексте "реквизиты" или "о компании"
        context_patterns = [
            r'(?:реквизит|requisite|о компании|about|details|company info).*?(\d{10}|\d{12})',
        ]
        
        for pattern in context_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches[:3]:  # Проверяем первые 3 совпадения
                if len(match) in [10, 12] and not match.startswith(('7', '8', '9')):
                    logger.info(f"Found INN in context: {match}")
                    return match
        
        # Если не нашли с явным упоминанием, ищем 10 или 12 цифр подряд
        # но только если они окружены пробелами или знаками препинания
        general_pattern = r'(?<!\d)(\d{10}|\d{12})(?!\d)'
        matches = re.findall(general_pattern, text)
        
        # Фильтруем: исключаем телефоны и другие числа
        for match in matches:
            # Проверяем, что это не телефон (не начинается с 7, 8, 9)
            if len(match) == 10 and not match.startswith(('7', '8', '9')):
                logger.info(f"Found potential INN (10 digits): {match}")
                return match
            elif len(match) == 12:
                # Для 12-значных ИНН (ИП) проверяем, что не начинается с 79 (телефон)
                if not match.startswith('79'):
                    logger.info(f"Found potential INN (12 digits, IP): {match}")
                    return match
        
        logger.info("No INN found in text")
        return None
    
    def extract_emails(self, text: str) -> List[str]:
        """Извлечь email адреса из текста."""
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(pattern, text)
        
        # Фильтруем: исключаем общие email-адреса типа example@example.com
        filtered = []
        exclude_patterns = ['example', 'test', 'domain', 'email', 'yoursite', 'yourdomain']
        
        for email in emails:
            email_lower = email.lower()
            if not any(pattern in email_lower for pattern in exclude_patterns):
                filtered.append(email)
        
        return list(set(filtered))  # Убираем дубликаты
    
    async def get_page_text(self, page: Page) -> str:
        """Получить весь текст со страницы."""
        try:
            # Получаем текст из body
            text = await page.evaluate('''() => {
                return document.body.innerText;
            }''')
            return text
        except Exception as e:
            logger.warning(f"Ошибка получения текста страницы: {e}")
            return ""
    
    async def find_contact_pages(self, page: Page, base_url: str) -> List[str]:
        """Найти страницы с контактами."""
        contact_keywords = ['контакт', 'contact', 'о компании', 'about', 'реквизит']
        contact_urls = []
        
        try:
            # Получаем все ссылки на странице
            links = await page.evaluate('''() => {
                return Array.from(document.querySelectorAll('a[href]')).map(a => ({
                    href: a.href,
                    text: a.innerText.toLowerCase()
                }));
            }''')
            
            for link in links:
                href = link['href']
                text = link['text']
                
                # Проверяем, содержит ли текст ссылки ключевые слова
                if any(keyword in text for keyword in contact_keywords):
                    # Преобразуем в абсолютный URL
                    full_url = urljoin(base_url, href)
                    # Проверяем, что это тот же домен
                    if urlparse(full_url).netloc == urlparse(base_url).netloc:
                        contact_urls.append(full_url)
            
        except Exception as e:
            logger.warning(f"Ошибка поиска контактных страниц: {e}")
        
        return list(set(contact_urls))[:3]  # Максимум 3 страницы
    
    async def parse_domain(self, domain: str) -> Dict:
        """
        Парсить домен и извлечь ИНН и email.
        
        Args:
            domain: Доменное имя (например, example.com)
            
        Returns:
            Словарь с результатами: {domain, inn, emails, source_urls, error}
        """
        if not self.browser:
            raise Exception("Браузер не запущен. Вызовите start() сначала.")
        
        result = {
            'domain': domain,
            'inn': None,
            'emails': [],
            'source_urls': [],
            'error': None
        }
        
        # Формируем URL
        url = f"https://{domain}" if not domain.startswith('http') else domain
        base_url = url
        
        logger.info(f"🔍 Парсинг: {domain}")
        
        page = await self.browser.new_page()
        
        try:
            # Загружаем главную страницу
            logger.info(f"  → Загрузка главной страницы...")
            await page.goto(url, wait_until='domcontentloaded', timeout=self.timeout)
            result['source_urls'].append(page.url)
            
            # Получаем текст главной страницы
            main_text = await self.get_page_text(page)
            
            # Ищем ИНН и email на главной странице
            inn = self.extract_inn(main_text)
            emails = self.extract_emails(main_text)
            
            if inn:
                result['inn'] = inn
                logger.info(f"  ✅ ИНН найден на главной: {inn}")
            
            if emails:
                result['emails'].extend(emails)
                logger.info(f"  ✅ Email найден на главной: {emails}")
            
            # Если не нашли ИНН или email, ищем на контактных страницах
            if not inn or not emails:
                logger.info(f"  → Поиск контактных страниц...")
                contact_urls = await self.find_contact_pages(page, base_url)
                
                for contact_url in contact_urls:
                    if inn and emails:
                        break  # Уже все нашли
                    
                    try:
                        logger.info(f"  → Загрузка: {contact_url}")
                        await page.goto(contact_url, wait_until='domcontentloaded', timeout=self.timeout)
                        result['source_urls'].append(page.url)
                        
                        contact_text = await self.get_page_text(page)
                        
                        if not inn:
                            inn = self.extract_inn(contact_text)
                            if inn:
                                result['inn'] = inn
                                logger.info(f"  ✅ ИНН найден на контактной странице: {inn}")
                        
                        if not emails:
                            new_emails = self.extract_emails(contact_text)
                            if new_emails:
                                result['emails'].extend(new_emails)
                                logger.info(f"  ✅ Email найден на контактной странице: {new_emails}")
                        
                    except PlaywrightTimeout:
                        logger.warning(f"  ⏱️ Таймаут загрузки: {contact_url}")
                    except Exception as e:
                        logger.warning(f"  ⚠️ Ошибка загрузки {contact_url}: {e}")
            
            # Убираем дубликаты email
            result['emails'] = list(set(result['emails']))
            
            if result['inn'] or result['emails']:
                logger.info(f"✅ {domain}: ИНН={result['inn']}, Email={result['emails']}")
            else:
                logger.warning(f"⚠️ {domain}: Ничего не найдено")
            
        except PlaywrightTimeout:
            error_msg = f"Таймаут загрузки страницы"
            result['error'] = error_msg
            logger.error(f"❌ {domain}: {error_msg}")
            
        except Exception as e:
            error_msg = f"Ошибка парсинга: {str(e)}"
            result['error'] = error_msg
            logger.error(f"❌ {domain}: {error_msg}")
            
        finally:
            await page.close()
        
        return result
    
    async def parse_domains(self, domains: List[str]) -> List[Dict]:
        """
        Парсить список доменов.
        
        Args:
            domains: Список доменов
            
        Returns:
            Список результатов для каждого домена
        """
        results = []
        
        for i, domain in enumerate(domains, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"Домен {i}/{len(domains)}")
            logger.info(f"{'='*60}")
            
            result = await self.parse_domain(domain)
            results.append(result)
            
            # Небольшая пауза между запросами
            await asyncio.sleep(1)
        
        return results
