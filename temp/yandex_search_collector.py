"""
Скрипт для сбора всех результатов из поисковика Яндекса.
Запуск в 2 клика через yandex-search-collector.bat
"""
import asyncio
import sys
import os
import json
import time
import random
from datetime import datetime
from typing import List, Dict, Any

# Добавляем путь к модулям
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ollama_inn_extractor'))

from app.agents.browser_agent import BrowserAgent


async def human_like_mouse_movement(page, target_x: int = None, target_y: int = None, steps: int = 20):
    """Имитация человеческого движения мыши с плавной траекторией.
    
    Args:
        page: Playwright page object
        target_x: Целевая координата X (если None - случайная)
        target_y: Целевая координата Y (если None - случайная)
        steps: Количество шагов для плавного движения (используется в Playwright mouse.move)
    """
    try:
        # Получаем размеры viewport
        viewport = page.viewport_size
        if not viewport:
            viewport = {'width': 1920, 'height': 1080}
        
        # Если целевые координаты не указаны, выбираем случайные
        if target_x is None:
            target_x = random.randint(100, viewport['width'] - 100)
        if target_y is None:
            target_y = random.randint(100, viewport['height'] - 100)
        
        # Ограничиваем координаты viewport
        target_x = max(0, min(target_x, viewport['width'] - 1))
        target_y = max(0, min(target_y, viewport['height'] - 1))
        
        # В Playwright mouse.move() с параметром steps автоматически создает плавное движение
        # Используем случайное количество шагов для более естественного движения
        mouse_steps = random.randint(max(10, steps - 5), steps + 5)
        
        # Плавное движение мыши к целевой точке
        await page.mouse.move(target_x, target_y, steps=mouse_steps)
        
        # Небольшая пауза после движения (имитация человеческой реакции)
        await asyncio.sleep(random.uniform(0.1, 0.3))
        
    except Exception as e:
        # Если движение мыши не удалось, просто продолжаем
        print(f"[MOUSE] Ошибка движения мыши: {e}")
        pass


async def click_pagination_button_human_like(page, page_num: int):
    """Найти и кликнуть на кнопку переключения страницы как человек.
    
    Args:
        page: Playwright page object
        page_num: Номер страницы для переключения
    """
    try:
        # Ищем кнопки пагинации (разные варианты селекторов)
        pagination_selectors = [
            f'a[href*="p={page_num}"]',  # Ссылка с параметром p=
            f'a:has-text("{page_num}")',  # Ссылка с текстом номера страницы
            '.pager__item_kind_page',  # Класс кнопки страницы
            '.pager__item',  # Общий класс пагинации
        ]
        
        button_found = False
        for selector in pagination_selectors:
            try:
                # Ищем элемент
                elements = await page.query_selector_all(selector)
                for element in elements:
                    text = await element.inner_text()
                    # Проверяем, что это действительно кнопка с нужным номером
                    if str(page_num) in text or f"p={page_num}" in await element.get_attribute('href') or '':
                        # Получаем координаты элемента
                        box = await element.bounding_box()
                        if box:
                            # Двигаем мышь к кнопке
                            center_x = int(box['x'] + box['width'] / 2)
                            center_y = int(box['y'] + box['height'] / 2)
                            
                            # Плавное движение мыши к кнопке
                            await human_like_mouse_movement(page, center_x, center_y, steps=15)
                            
                            # Небольшая пауза перед кликом (как человек наводит)
                            await asyncio.sleep(random.uniform(0.2, 0.5))
                            
                            # Наведение на элемент
                            await element.hover()
                            await asyncio.sleep(random.uniform(0.1, 0.3))
                            
                            # Клик
                            await element.click()
                            button_found = True
                            print(f"[MOUSE] Клик по кнопке страницы {page_num} (человекообразное движение мыши)")
                            return True
            except:
                continue
        
        if not button_found:
            print(f"[MOUSE] Кнопка страницы {page_num} не найдена, используем прямой переход по URL")
            return False
            
    except Exception as e:
        print(f"[MOUSE] Ошибка при клике по кнопке: {e}")
        return False


async def wait_for_captcha_solution(browser_agent: BrowserAgent, page_num: int, max_wait: int = 120) -> bool:
    """Ожидание решения капчи с автоматическим обнаружением.
    
    Args:
        browser_agent: BrowserAgent instance
        page_num: Номер страницы (для логирования)
        max_wait: Максимальное время ожидания в секундах (по умолчанию 120 = 2 минуты)
        
    Returns:
        True если капча решена или её нет, False если таймаут
    """
    try:
        # Проверяем текущий URL
        current_url = browser_agent.page.url if browser_agent.page else ""
        
        # Проверяем наличие капчи
        if "showcaptcha" not in current_url.lower() and "captcha" not in current_url.lower():
            # Проверяем содержимое страницы на наличие капчи
            try:
                page_content = await browser_agent.page.content()
                if "captcha" not in page_content.lower() and "showcaptcha" not in page_content.lower():
                    return True  # Капчи нет
            except:
                pass
        
        # Капча обнаружена
        print(f"[CAPTCHA] Обнаружена капча на странице {page_num}")
        print(f"[CAPTCHA] Активируем окно браузера для решения капчи...")
        
        # Активируем окно браузера
        try:
            await browser_agent.page.bring_to_front()
            await browser_agent.page.evaluate("() => { window.focus(); }")
            # Увеличиваем размер окна
            await browser_agent.page.set_viewport_size({"width": 1920, "height": 1080})
            print(f"[CAPTCHA] Окно браузера активировано")
        except Exception as e:
            print(f"[CAPTCHA] Ошибка активации окна: {e}")
        
        # Ждем решения капчи (проверяем каждые 3 секунды)
        start_time = time.time()
        check_interval = 3  # Проверяем каждые 3 секунды
        
        while True:
            elapsed = time.time() - start_time
            
            if elapsed > max_wait:
                print(f"[CAPTCHA] Таймаут ожидания решения капчи ({max_wait} секунд)")
                return False
            
            # Проверяем текущий URL
            try:
                current_url_check = browser_agent.page.url if browser_agent.page else ""
            except:
                current_url_check = ""
            
            # Проверяем содержимое страницы
            try:
                page_content = await browser_agent.page.content()
                has_captcha = (
                    "showcaptcha" in current_url_check.lower() or 
                    "captcha" in current_url_check.lower() or
                    "captcha" in page_content.lower() or
                    "showcaptcha" in page_content.lower()
                )
            except:
                has_captcha = "showcaptcha" in current_url_check.lower() or "captcha" in current_url_check.lower()
            
            if not has_captcha:
                print(f"[CAPTCHA] Капча решена! (время ожидания: {elapsed:.1f} секунд)")
                await asyncio.sleep(2)  # Дополнительная задержка после решения
                return True
            
            # Показываем прогресс каждые 10 секунд
            if int(elapsed) % 10 == 0 and int(elapsed) > 0:
                print(f"[CAPTCHA] Ожидание решения капчи... ({int(elapsed)}/{max_wait} сек)")
            
            await asyncio.sleep(check_interval)
            
    except Exception as e:
        print(f"[CAPTCHA] Ошибка при ожидании капчи: {e}")
        return False


async def extract_yandex_results_from_page(browser_agent: BrowserAgent, max_results: int = 50) -> List[Dict[str, Any]]:
    """Извлечь результаты поиска с текущей страницы Яндекса.
    
    Args:
        browser_agent: BrowserAgent instance
        max_results: Максимальное количество результатов
        
    Returns:
        Список результатов
    """
    if not browser_agent.page:
        return []
    
    try:
        js_code = f"""
        ((maxResults) => {{
            const results = [];
            
            // Yandex result selectors
            const selectors = [
                'li.serp-item',  // Standard Yandex result container
                'div.organic',  // Alternative selector
            ];
            
            for (const selector of selectors) {{
                const containers = Array.from(document.querySelectorAll(selector));
                for (const container of containers) {{
                    // Get link
                    const link = container.querySelector('a.link, a[href^="http"]');
                    if (!link) continue;
                    
                    const url = link.href;
                    const title = link.textContent?.trim() || link.innerText?.trim() || '';
                    
                    // Get snippet text (description)
                    const snippetEl = container.querySelector('.text-container, .organic__text, .serp-item__text');
                    const snippet = snippetEl ? (snippetEl.textContent || snippetEl.innerText || '').trim() : '';
                    
                    // Filter out Yandex's own pages
                    if (url && 
                        url.startsWith('http') && 
                        !url.includes('yandex.ru') &&
                        !url.includes('yandex.net') &&
                        (title.length > 0 || snippet.length > 0)) {{
                        
                        if (!results.some(r => r.url === url)) {{
                            results.push({{
                                title: title.substring(0, 200),
                                url: url,
                                snippet: snippet.substring(0, 300)
                            }});
                            
                            if (results.length >= maxResults) {{
                                return results;
                            }}
                        }}
                    }}
                }}
                
                if (results.length > 0) {{
                    break;
                }}
            }}
            
            return results;
        }})({max_results});
        """
        
        results = await browser_agent.page.evaluate(js_code)
        return results if results else []
        
    except Exception as e:
        print(f"[ERROR] Ошибка извлечения результатов: {e}")
        return []


async def collect_yandex_results(query: str, pages: int = 1) -> List[Dict[str, Any]]:
    """Собрать все результаты из Яндекса.
    
    Args:
        query: Поисковый запрос
        pages: Количество страниц для сбора (глубина поиска)
        
    Returns:
        Список всех результатов: [{"title": "...", "url": "...", "snippet": "..."}, ...]
    """
    browser_agent = BrowserAgent(chrome_cdp_url="http://127.0.0.1:9222")
    all_results = []
    
    try:
        # Подключение к браузеру
        print(f"[INFO] Подключение к браузеру...")
        await browser_agent.connect()
        print(f"[OK] Браузер подключен")
        
        # Собираем результаты со всех страниц
        for page_num in range(1, pages + 1):
            print(f"\n{'=' * 80}")
            print(f"Страница {page_num} из {pages}")
            print(f"{'=' * 80}")
            
            # Человекообразная задержка между страницами (кроме первой)
            if page_num > 1:
                delay = random.uniform(2.0, 5.0)  # 2-5 секунд между страницами
                print(f"[INFO] Пауза перед следующей страницей: {delay:.1f} сек (имитация человеческого поведения)")
                await asyncio.sleep(delay)
            
            try:
                # Поиск в Яндексе (с указанием страницы через параметр p=)
                import urllib.parse
                encoded_query = urllib.parse.quote_plus(query)
                
                if page_num == 1:
                    # Первая страница - обычный поиск
                    yandex_url = f"https://yandex.ru/search/?text={encoded_query}"
                    print(f"[INFO] Переход на: {yandex_url}")
                    await browser_agent.navigate(yandex_url, wait_until="domcontentloaded", timeout=15000)
                else:
                    # Последующие страницы - пытаемся кликнуть по кнопке как человек
                    print(f"[INFO] Попытка переключения на страницу {page_num} через кнопку пагинации...")
                    
                    # Пробуем найти и кликнуть по кнопке пагинации
                    button_clicked = await click_pagination_button_human_like(browser_agent.page, page_num)
                    
                    if not button_clicked:
                        # Если кнопка не найдена, используем прямой переход по URL
                        yandex_url = f"https://yandex.ru/search/?text={encoded_query}&p={page_num}"
                        print(f"[INFO] Прямой переход на: {yandex_url}")
                        await browser_agent.navigate(yandex_url, wait_until="domcontentloaded", timeout=15000)
                    else:
                        # Если кликнули по кнопке, ждем загрузки новой страницы
                        await asyncio.sleep(random.uniform(1.0, 2.0))
                        # Проверяем, что страница загрузилась
                        try:
                            await browser_agent.page.wait_for_load_state("domcontentloaded", timeout=10000)
                        except:
                            pass
                
                # Человекообразная задержка после загрузки страницы
                post_load_delay = random.uniform(1.0, 3.0)  # 1-3 секунды
                await asyncio.sleep(post_load_delay)
                
                # Проверка на капчу и ожидание её решения
                captcha_solved = await wait_for_captcha_solution(browser_agent, page_num)
                if not captcha_solved:
                    print(f"[CAPTCHA] Капча не решена в течение 2 минут, пропускаем страницу {page_num}")
                    continue  # Пропускаем эту страницу
                
                # Ждем появления результатов
                try:
                    await browser_agent.page.wait_for_selector('li.serp-item, div.organic', timeout=10000, state='attached')
                    
                    # Имитация человеческого поведения: небольшая прокрутка, движение мыши и пауза
                    try:
                        # Случайное движение мыши по странице (имитация чтения)
                        viewport = browser_agent.page.viewport_size
                        if viewport:
                            mouse_x = random.randint(200, viewport['width'] - 200)
                            mouse_y = random.randint(200, viewport['height'] - 200)
                            await human_like_mouse_movement(browser_agent.page, mouse_x, mouse_y, steps=8)
                            await asyncio.sleep(random.uniform(0.3, 0.8))
                        
                        # Прокручиваем немного вниз (как человек просматривает страницу)
                        await browser_agent.page.evaluate("window.scrollBy(0, 300)")
                        await asyncio.sleep(random.uniform(0.5, 1.5))
                        
                        # Еще одно движение мыши
                        if viewport:
                            mouse_x2 = random.randint(200, viewport['width'] - 200)
                            mouse_y2 = random.randint(300, viewport['height'] - 200)
                            await human_like_mouse_movement(browser_agent.page, mouse_x2, mouse_y2, steps=8)
                            await asyncio.sleep(random.uniform(0.3, 0.8))
                        
                        # Прокручиваем обратно вверх
                        await browser_agent.page.evaluate("window.scrollTo(0, 0)")
                        await asyncio.sleep(random.uniform(0.3, 1.0))
                    except:
                        pass
                    
                except Exception as e:
                    # Проверяем, не капча ли это
                    current_url_check = await browser_agent.get_current_url()
                    if "showcaptcha" in current_url_check.lower() or "captcha" in current_url_check.lower():
                        print(f"[CAPTCHA] Обнаружена капча после ожидания результатов")
                        print(f"[CAPTCHA] Пропускаем страницу {page_num}")
                        continue
                    print(f"[WARNING] Таймаут ожидания результатов: {e}")
                
                # Извлекаем результаты со страницы (без повторной навигации)
                results = await extract_yandex_results_from_page(browser_agent, max_results=50)
                
                # Небольшая пауза после извлечения результатов (имитация чтения)
                if results:
                    reading_delay = random.uniform(0.5, 1.5)  # 0.5-1.5 секунды
                    await asyncio.sleep(reading_delay)
                
                if results:
                    print(f"[OK] Найдено результатов на странице {page_num}: {len(results)}")
                    all_results.extend(results)
                    
                    # Показываем результаты
                    for i, result in enumerate(results, 1):
                        title = result.get("title", "Без названия")
                        url = result.get("url", "")
                        snippet = result.get("snippet", "")[:100]
                        print(f"  {i}. {title}")
                        print(f"     URL: {url}")
                        if snippet:
                            print(f"     Сниппет: {snippet}...")
                else:
                    print(f"[WARNING] На странице {page_num} результатов не найдено")
                    break  # Если результатов нет, прекращаем сбор
                    
            except Exception as page_error:
                print(f"[ERROR] Ошибка при сборе страницы {page_num}: {page_error}")
                continue
        
        print(f"\n{'=' * 80}")
        print(f"ИТОГО СОБРАНО: {len(all_results)} результатов")
        print(f"{'=' * 80}")
        
        return all_results
        
    except Exception as e:
        print(f"[ERROR] Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        # Браузер остается открытым (не закрываем)
        print("\n[INFO] Браузер остается открытым для повторного использования")


async def main():
    """Главная функция."""
    print("=" * 80)
    print("СБОР РЕЗУЛЬТАТОВ ИЗ ПОИСКОВИКА ЯНДЕКСА")
    print("=" * 80)
    print()
    
    # Ввод данных
    if len(sys.argv) > 1:
        query = sys.argv[1]
    else:
        query = input("Введите поисковый запрос: ").strip()
    
    if len(sys.argv) > 2:
        try:
            pages = int(sys.argv[2])
        except ValueError:
            pages = 1
    else:
        pages_input = input("Введите глубину поиска (количество страниц, по умолчанию 1): ").strip()
        pages = int(pages_input) if pages_input else 1
    
    if not query:
        print("[ERROR] Поисковый запрос не может быть пустым!")
        return
    
    print(f"\nЗапрос: {query}")
    print(f"Глубина поиска: {pages} страниц")
    print()
    
    # Сбор результатов
    start_time = datetime.now()
    results = await collect_yandex_results(query, pages)
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Сохранение результатов
    if results:
        # Создаем имя файла на основе запроса
        safe_query = "".join(c for c in query if c.isalnum() or c in (' ', '-', '_')).strip()[:50]
        safe_query = safe_query.replace(' ', '_')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"yandex_results_{safe_query}_{timestamp}.json"
        filepath = os.path.join("temp", filename)
        
        # Создаем папку temp если её нет
        os.makedirs("temp", exist_ok=True)
        
        # Сохраняем в JSON
        output_data = {
            "query": query,
            "pages": pages,
            "total_results": len(results),
            "collected_at": datetime.now().isoformat(),
            "duration_seconds": duration,
            "results": results
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n{'=' * 80}")
        print("РЕЗУЛЬТАТЫ СОХРАНЕНЫ")
        print(f"{'=' * 80}")
        print(f"Файл: {filepath}")
        print(f"Всего результатов: {len(results)}")
        print(f"Время сбора: {duration:.2f} секунд")
        print(f"{'=' * 80}\n")
    else:
        print("\n[WARNING] Результаты не найдены")


if __name__ == "__main__":
    asyncio.run(main())

