"""Human behavior simulation for anti-detection."""
import asyncio
import random
import logging
import time
from playwright.async_api import Page

logger = logging.getLogger(__name__)


async def random_delay(min_ms: int = 1000, max_ms: int = 3000):
    """Random delay to simulate human behavior."""
    delay = random.randint(min_ms, max_ms) / 1000.0
    await asyncio.sleep(delay)


async def human_pause(a: float = 1.5, b: float = 4.5):
    """Human-like pause with random delay."""
    await asyncio.sleep(random.uniform(a, b))


async def human_like_scroll(page: Page):
    """Simulate human-like scrolling."""
    actions = [
        lambda: page.mouse.wheel(0, random.randint(200, 600)),
        lambda: page.mouse.wheel(0, random.randint(-300, -100)),
        lambda: page.mouse.wheel(0, random.randint(50, 150)),
    ]
    for _ in range(random.randint(1, 3)):
        await actions[random.randint(0, len(actions) - 1)]()
        await human_pause(0.4, 1.2)


async def human_like_mouse_movement(page: Page):
    """Simulate random mouse movements."""
    x = random.randint(100, 900)
    y = random.randint(100, 700)
    for _ in range(random.randint(2, 6)):
        xr = x + random.randint(-30, 30)
        yr = y + random.randint(-30, 30)
        await page.mouse.move(xr, yr, steps=random.randint(6, 22))
        await human_pause(0.2, 0.6)


async def very_human_behavior(page: Page):
    """Very human-like behavior with mouse movement and scrolling."""
    await human_pause()
    await human_like_mouse_movement(page)
    await human_pause(0.5, 2)
    await human_like_scroll(page)
    await human_pause(1, 3)


async def light_human_behavior(page: Page):
    """Light human-like behavior (just scrolling)."""
    await human_pause(0.5, 1.5)
    await human_like_scroll(page)
    await human_pause(0.5, 1.2)


async def wait_for_captcha(page: Page, engine_name: str):
    """Wait for CAPTCHA to be solved, with window management."""
    captcha_detected = False
    max_wait_time = 300  # Maximum 5 minutes to solve CAPTCHA
    start_time = time.time()
    
    while True:
        # Check timeout
        if time.time() - start_time > max_wait_time:
            logger.warning(f"{engine_name}: CAPTCHA wait timeout ({max_wait_time}s)")
            break
            
        url = page.url.lower()
        # Check for various CAPTCHA indicators
        if ("captcha" in url or "showcaptcha" in url or 
            "/sorry" in url or "sorry/index" in url or
            "unusual traffic" in url.lower()):
            if not captcha_detected:
                # Maximize browser window when captcha is detected
                try:
                    await page.set_viewport_size({"width": 1920, "height": 1080})
                    await page.bring_to_front()
                    await page.evaluate("() => { window.focus(); }")
                except:
                    pass
                
                # Force window activation via PowerShell (Windows only)
                try:
                    import os
                    import sys
                    if sys.platform == 'win32':
                        ps_cmd = '''
                        $w = Get-Process chrome | Where {$_.MainWindowTitle -ne ""} | Select -First 1;
                        if ($w) {
                            $sig = '[DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h); [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);';
                            $t = Add-Type -MemberDefinition $sig -Name Win32 -Namespace Native -PassThru;
                            $t::ShowWindow($w.MainWindowHandle, 3); # SW_MAXIMIZE
                            $t::SetForegroundWindow($w.MainWindowHandle);
                        }
                        '''
                        os.system(f'powershell -WindowStyle Hidden -Command "{ps_cmd}"')
                except:
                    pass
                
                captcha_detected = True
                logger.warning(f"{engine_name}: Капча обнаружена!")
                logger.warning("=" * 60)
                logger.warning(f"{engine_name}: КАПЧА ОБНАРУЖЕНА!")
                logger.warning("=" * 60)
                # Sound signals - use logger instead of print to avoid encoding issues
                try:
                    import sys
                    if sys.platform == 'win32':
                        import winsound
                        for _ in range(3):
                            winsound.Beep(1000, 200)
                except:
                    pass
            
            await asyncio.sleep(2)
        else:
            if captcha_detected:
                # Restore small window size after captcha is solved
                try:
                    await page.set_viewport_size({"width": 800, "height": 600})
                except:
                    pass
                logger.info(f"[OK] {engine_name}: Капча решена! Продолжаем...")
            break

