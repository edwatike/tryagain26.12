"""
PROOF TEST: Comet Assistant Activation
This test will PROVE that Comet assistant opens and input field is found.
"""
import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'experiments' / 'comet-integration'))

async def test_comet_assistant():
    """Test Comet assistant activation and provide PROOF"""
    from playwright.async_api import async_playwright
    import time
    
    print("="*70)
    print("🔥 PROOF TEST: COMET ASSISTANT ACTIVATION")
    print("="*70)
    
    cdp_url = "http://127.0.0.1:9222"
    playwright = await async_playwright().start()
    
    try:
        # Connect to Comet CDP
        print("\n1️⃣ Подключаюсь к Comet CDP...")
        browser = await playwright.chromium.connect_over_cdp(cdp_url)
        print("   ✅ Подключено к Comet")
        
        # Get context
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        
        # Open test page
        page = await context.new_page()
        domain = "elektro.ru"
        url = f"https://{domain}"
        
        print(f"\n2️⃣ Открываю тестовую страницу: {url}")
        await page.goto(url, timeout=30000)
        await page.wait_for_timeout(3000)
        print("   ✅ Страница загружена")
        
        # Try to open assistant
        print(f"\n3️⃣ Открываю ассистент Comet (Alt+A)...")
        await page.keyboard.press('Alt+A')
        await page.wait_for_timeout(2000)
        
        # Find sidecar page
        print(f"\n4️⃣ Ищу страницу sidecar...")
        sidecar_page = None
        for p in context.pages:
            try:
                u = p.url.lower()
                if 'perplexity.ai/sidecar' in u or 'chrome://sidebar' in u:
                    sidecar_page = p
                    print(f"   ✅ Найден sidecar: {p.url}")
                    break
            except:
                continue
        
        if not sidecar_page:
            print("   ❌ ОШИБКА: Sidecar не найден!")
            print("\n💡 РЕШЕНИЕ:")
            print("   1. Открой Comet браузер вручную")
            print("   2. Нажми Alt+A чтобы активировать ассистент")
            print("   3. Убедись, что панель ассистента открывается")
            print("   4. Запусти этот тест снова")
            return False
        
        # Wait for sidecar UI to load (CRITICAL FIX)
        print(f"\n5️⃣ Жду загрузки UI sidecar (3 секунды)...")
        await sidecar_page.bring_to_front()
        await sidecar_page.wait_for_timeout(3000)
        
        # Wait for interactive elements
        print(f"\n6️⃣ Жду появления интерактивных элементов...")
        try:
            await sidecar_page.wait_for_selector('textarea, [contenteditable="true"], [role="textbox"]', timeout=10000)
            print("   ✅ Интерактивные элементы обнаружены!")
        except Exception as e:
            print(f"   ⚠️ Интерактивные элементы не найдены за 10 секунд")
            print(f"   Ошибка: {e}")
        
        # Check for input field
        print(f"\n7️⃣ Проверяю наличие поля ввода...")
        inputs = await sidecar_page.evaluate("""
            () => {
                const inputs = document.querySelectorAll('textarea, [contenteditable="true"], [role="textbox"]');
                return Array.from(inputs).map(el => ({
                    tag: el.tagName.toLowerCase(),
                    visible: el.getBoundingClientRect().width > 0,
                    width: el.getBoundingClientRect().width,
                    height: el.getBoundingClientRect().height
                }));
            }
        """)
        
        print(f"   Найдено элементов ввода: {len(inputs)}")
        visible_inputs = [inp for inp in inputs if inp['visible']]
        print(f"   Видимых элементов: {len(visible_inputs)}")
        
        if visible_inputs:
            print("\n" + "="*70)
            print("✅ ✅ ✅ PROOF: COMET ASSISTANT РАБОТАЕТ! ✅ ✅ ✅")
            print("="*70)
            print(f"\n📊 Детали:")
            for i, inp in enumerate(visible_inputs):
                print(f"   Input {i+1}: {inp['tag']}, размер: {inp['width']}x{inp['height']}")
            print("\n🎯 РЕЗУЛЬТАТ: Ассистент открылся, поле ввода найдено!")
            print("="*70)
            return True
        else:
            print("\n" + "="*70)
            print("❌ ❌ ❌ PROOF: COMET ASSISTANT НЕ РАБОТАЕТ ❌ ❌ ❌")
            print("="*70)
            print(f"\n📊 Детали:")
            print(f"   - Sidecar открылся: ДА")
            print(f"   - Элементов ввода найдено: {len(inputs)}")
            print(f"   - Видимых элементов: 0")
            print("\n💡 ПРОБЛЕМА: UI не загрузился полностью")
            print("="*70)
            return False
            
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await playwright.stop()

if __name__ == "__main__":
    result = asyncio.run(test_comet_assistant())
    sys.exit(0 if result else 1)
