"""
FIX: Activate Comet Assistant programmatically
Try to enable assistant through CDP/Extension API
"""
import asyncio
import requests
import json

async def fix_comet_assistant():
    """Try to activate Comet assistant"""
    from playwright.async_api import async_playwright
    
    print("🔧 FIXING COMET ASSISTANT ACTIVATION")
    print("="*70)
    
    cdp_url = "http://127.0.0.1:9222"
    
    # Check CDP targets
    print("\n1️⃣ Проверяю CDP targets...")
    response = requests.get(f"{cdp_url}/json")
    targets = response.json()
    
    print(f"   Найдено targets: {len(targets)}")
    
    # Look for Perplexity extension
    perplexity_targets = [t for t in targets if 'perplexity' in t.get('url', '').lower() or 'perplexity' in t.get('title', '').lower()]
    print(f"   Perplexity targets: {len(perplexity_targets)}")
    
    for t in perplexity_targets:
        print(f"      - {t.get('type')}: {t.get('url')[:80]}")
    
    # Try to open sidecar directly
    print("\n2️⃣ Пытаюсь открыть sidecar напрямую...")
    
    playwright = await async_playwright().start()
    try:
        browser = await playwright.chromium.connect_over_cdp(cdp_url)
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        
        # Try to navigate to sidecar URL directly
        sidecar_url = "https://www.perplexity.ai/sidecar?copilot=true"
        print(f"   Открываю: {sidecar_url}")
        
        page = await context.new_page()
        await page.goto(sidecar_url, timeout=30000)
        await page.wait_for_timeout(5000)
        
        print("   ✅ Sidecar открыт напрямую")
        
        # Check for input field
        print("\n3️⃣ Проверяю поле ввода...")
        inputs = await page.evaluate("""
            () => {
                const inputs = document.querySelectorAll('textarea, [contenteditable="true"], [role="textbox"]');
                return Array.from(inputs).map(el => ({
                    tag: el.tagName.toLowerCase(),
                    visible: el.getBoundingClientRect().width > 0,
                    width: el.getBoundingClientRect().width,
                    height: el.getBoundingClientRect().height,
                    placeholder: el.getAttribute('placeholder') || ''
                }));
            }
        """)
        
        print(f"   Найдено элементов: {len(inputs)}")
        visible = [inp for inp in inputs if inp['visible']]
        print(f"   Видимых: {len(visible)}")
        
        if visible:
            print("\n✅ ✅ ✅ SUCCESS! Sidecar работает при прямом открытии!")
            print("\n💡 РЕШЕНИЕ: Использовать прямой URL вместо hotkey")
            return True
        else:
            print("\n❌ Даже при прямом открытии нет input field")
            print("\n💡 ПРОБЛЕМА: Perplexity sidecar не работает в этом браузере")
            print("   Возможные причины:")
            print("   1. Расширение Perplexity не установлено")
            print("   2. Расширение отключено")
            print("   3. Нет подписки на Perplexity")
            print("   4. Браузер не поддерживает sidecar")
            return False
            
    finally:
        await playwright.stop()

if __name__ == "__main__":
    import sys
    result = asyncio.run(fix_comet_assistant())
    sys.exit(0 if result else 1)
