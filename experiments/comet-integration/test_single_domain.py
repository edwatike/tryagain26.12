"""
ТЕСТ ОДНОГО ДОМЕНА COMET CDP
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
import argparse

try:
    from playwright.async_api import async_playwright, Playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
    pyautogui.FAILSAFE = False
except Exception:
    PYAUTOGUI_AVAILABLE = False

try:
    import pygetwindow as gw
    PYGETWINDOW_AVAILABLE = True
except Exception:
    PYGETWINDOW_AVAILABLE = False

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('single_domain_test.log', encoding='utf-8'),
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


async def dump_screenshot(page, tag: str) -> None:
    try:
        out_dir = Path("cdp_debug")
        out_dir.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        p = out_dir / f"{ts}_{tag}.png"
        # Some sidecar pages can hang on font loading; increase timeout.
        await page.screenshot(path=str(p), full_page=True, timeout=60000)
        logger.info(f"📸 Screenshot saved: {p}")
    except Exception as e:
        logger.warning(f"⚠️ Failed to take screenshot ({tag}): {e}")


def dump_desktop_screenshot(tag: str) -> None:
    """Capture the whole desktop so you can visually confirm the right sidecar panel."""
    if not PYAUTOGUI_AVAILABLE:
        return
    try:
        out_dir = Path("cdp_debug")
        out_dir.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        p = out_dir / f"{ts}_{tag}_desktop.png"
        img = pyautogui.screenshot()
        img.save(p)
        logger.info(f"🖥️ Desktop screenshot saved: {p}")
    except Exception as e:
        logger.warning(f"⚠️ Failed desktop screenshot ({tag}): {e}")


def try_open_assistant_ui(method: str) -> None:
    if not PYAUTOGUI_AVAILABLE:
        return
    try:
        # Ensure focus is in page content (not address bar)
        pyautogui.click(960, 540)
        time.sleep(0.2)
        # IMPORTANT: do NOT use Ctrl+J here; in Chromium it opens Downloads.
        # Also avoid toggling the assistant panel open/close by pressing the same hotkey twice.
        m = (method or "").lower()
        if m == "alt+a" or m == "alt_a":
            pyautogui.hotkey('alt', 'a')
            time.sleep(0.5)
        elif m in {"ctrl+shift+a", "ctrl_shift_a", "ctrl+shift+a"}:
            pyautogui.hotkey('ctrl', 'shift', 'a')
            time.sleep(0.5)
        else:
            # default: try Alt+A once
            pyautogui.hotkey('alt', 'a')
            time.sleep(0.5)
    except Exception:
        pass


async def find_assistant_input(page, viewport_height: int):
    """Heuristically find Comet assistant input, avoiding random site inputs."""
    candidates = []

    # Prefer specific selectors first
    preferred_selectors = [
        '[data-testid*="assistant" i] textarea',
        '[data-testid*="assistant" i] input',
        '[data-testid*="chat" i] textarea',
        '[data-testid*="chat" i] input',
        'textarea[placeholder*="ассист" i]',
        'textarea[placeholder*="ask" i]',
        'textarea[placeholder*="вопрос" i]',
        'textarea[placeholder*="prompt" i]',
        'input[placeholder*="ассист" i]',
        'input[placeholder*="ask" i]',
        'input[placeholder*="вопрос" i]',
        'input[placeholder*="prompt" i]',
    ]

    async def consider(el, selector_hint: str):
        try:
            if not await el.is_visible():
                return
            box = await el.bounding_box()
            if not box:
                return

            # Heuristic: assistant input is usually in some panel and not at the top of the page.
            # We accept lower half elements more readily.
            y_ok = box["y"] > viewport_height * 0.40

            placeholder = await el.get_attribute("placeholder")
            testid = await el.get_attribute("data-testid")
            aria = await el.get_attribute("aria-label")

            text = " ".join(
                [p for p in [placeholder, testid, aria] if p]
            ).lower()

            semantic_ok = any(k in text for k in ["assist", "ассист", "chat", "чат", "ask", "вопрос", "prompt"])

            score = 0
            if semantic_ok:
                score += 5
            if y_ok:
                score += 2
            # Slightly prefer textarea
            tag = await el.evaluate("e => e.tagName.toLowerCase()")
            if tag == "textarea":
                score += 1

            candidates.append((score, box, selector_hint, el, text))
        except Exception:
            return

    for sel in preferred_selectors:
        try:
            els = await page.query_selector_all(sel)
            for el in els:
                await consider(el, sel)
        except Exception:
            continue

    # Fallback: any visible textarea/input, but with stricter scoring
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


async def collect_sidecar_text_blocks(sidecar_page, input_el=None):
    """Collect visible text blocks in sidecar, excluding the input area."""
    try:
        input_box = None
        if input_el is not None:
            try:
                input_box = await input_el.bounding_box()
            except Exception:
                input_box = None

        input_y = input_box["y"] if input_box else None

        blocks = await sidecar_page.evaluate(
            """
            () => {
              const candidates = Array.from(document.querySelectorAll('article, [role="article"], [role="listitem"], div, p'));
              const out = [];

              function isVisible(el) {
                const style = window.getComputedStyle(el);
                if (!style) return false;
                if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return false;
                const rect = el.getBoundingClientRect();
                if (!rect || rect.width < 10 || rect.height < 10) return false;
                return true;
              }

              for (const el of candidates) {
                if (!isVisible(el)) continue;
                const txt = (el.innerText || '').trim();
                if (txt.length < 30) continue;
                const rect = el.getBoundingClientRect();
                out.push({
                  tag: el.tagName.toLowerCase(),
                  role: el.getAttribute('role') || '',
                  cls: el.className || '',
                  y: rect.y,
                  x: rect.x,
                  w: rect.width,
                  h: rect.height,
                  text: txt.slice(0, 500)
                });
              }

              // Sort by y then by size
              out.sort((a,b) => (a.y - b.y) || (b.h - a.h));
              // De-dup by text prefix
              const uniq = [];
              const seen = new Set();
              for (const it of out) {
                const key = it.text;
                if (seen.has(key)) continue;
                seen.add(key);
                uniq.push(it);
              }
              return uniq.slice(0, 200);
            }
            """
        )

        # Filter in python by input position if available
        if input_y is not None:
            blocks = [b for b in blocks if b.get("y", 1e9) < input_y + 5]

        return blocks
    except Exception:
        return []


async def dump_sidecar_snapshot(sidecar_page, tag: str, input_el=None):
    try:
        out_dir = Path("cdp_debug")
        out_dir.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        inputs = await sidecar_page.evaluate(
            """
            () => {
              function deepCollectInputs(root) {
                const out = [];
                const stack = [root];
                while (stack.length) {
                  const node = stack.pop();
                  if (!node) continue;
                  // shadow
                  if (node.shadowRoot) stack.push(node.shadowRoot);
                  // children
                  if (node.children) {
                    for (let i = node.children.length - 1; i >= 0; i--) {
                      stack.push(node.children[i]);
                    }
                  }
                  if (node.querySelectorAll) {
                    const found = node.querySelectorAll('textarea, input, [role="textbox"], [contenteditable]');
                    for (const el of found) out.push(el);
                  }
                }
                return out;
              }

              const els = deepCollectInputs(document);
              const out = [];
              for (const el of els) {
                const rect = el.getBoundingClientRect();
                if (!rect || rect.width < 10 || rect.height < 10) continue;
                out.push({
                  tag: el.tagName.toLowerCase(),
                  type: el.getAttribute('type') || '',
                  placeholder: el.getAttribute('placeholder') || '',
                  testid: el.getAttribute('data-testid') || '',
                  aria: el.getAttribute('aria-label') || '',
                  cls: el.className || '',
                  y: rect.y,
                  x: rect.x,
                  w: rect.width,
                  h: rect.height,
                });
              }
              out.sort((a,b) => a.y - b.y);
              return out.slice(0, 100);
            }
            """
        )

        blocks = await collect_sidecar_text_blocks(sidecar_page, input_el=input_el)
        payload = {
            "url": sidecar_page.url,
            "inputs": inputs,
            "blocks": blocks,
        }

        p = out_dir / f"{ts}_{tag}_sidecar_snapshot.json"
        p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"🧩 Sidecar snapshot saved: {p} (inputs={len(inputs)}, blocks={len(blocks)})")
    except Exception as e:
        logger.warning(f"⚠️ Failed to dump sidecar snapshot: {e}")


async def find_sidecar_page(browser, cdp_url: str) -> object:
    """Find Perplexity sidecar page opened by Ctrl+J (right panel)."""
    def is_sidecar_url(u: str) -> bool:
        if not u:
            return False
        u = u.lower()
        return (
            "perplexity.ai/sidecar" in u
            or u.startswith("chrome://sidebar")
        )

    # Try existing pages first (prefer perplexity sidecar over chrome://sidebar)
    perplexity_pages = []
    sidebar_pages = []
    for ctx in browser.contexts:
        for p in ctx.pages:
            try:
                u = (p.url or "").lower()
                if "perplexity.ai/sidecar" in u:
                    perplexity_pages.append(p)
                elif u.startswith("chrome://sidebar"):
                    sidebar_pages.append(p)
            except Exception:
                continue

    if perplexity_pages:
        return perplexity_pages[0]
    if sidebar_pages:
        return sidebar_pages[0]

    # If Playwright doesn't expose the page, try to locate the URL via CDP targets and open it.
    try:
        r = requests.get(f"{cdp_url}/json", timeout=5)
        targets = r.json() if r.status_code == 200 else []
        sidecar_target = None
        for t in targets:
            u = (t.get("url") or "").lower()
            if "perplexity.ai/sidecar" in u:
                sidecar_target = t
                break
        if sidecar_target:
            sidecar_url = sidecar_target.get("url")
            logger.info(f"🧭 Found sidecar target via CDP: {sidecar_url}")
            if sidecar_url and "perplexity.ai/sidecar" in sidecar_url and "copilot=" not in sidecar_url:
                sidecar_url = sidecar_url + ("?copilot=true" if "?" not in sidecar_url else "&copilot=true")
            # Open it explicitly
            ctx = browser.contexts[0] if browser.contexts else None
            if ctx is not None:
                p = await ctx.new_page()
                await p.goto(sidecar_url, timeout=30000)
                await p.wait_for_timeout(1000)
                return p
    except Exception as e:
        logger.warning(f"⚠️ Could not open sidecar via CDP targets: {e}")

    # Wait for a new page to appear
    deadline = time.time() + 10
    seen = set()
    for ctx in browser.contexts:
        for p in ctx.pages:
            try:
                seen.add(p)
            except Exception:
                continue

    while time.time() < deadline:
        await asyncio.sleep(0.5)
        for ctx in browser.contexts:
            for p in ctx.pages:
                if p in seen:
                    continue
                try:
                    if is_sidecar_url(p.url):
                        return p
                except Exception:
                    continue

    return None


async def find_sidecar_input(sidecar_page):
    """Find prompt input inside sidecar chat."""
    selectors = [
        'textarea[placeholder*="задайте" i]',
        'textarea[placeholder*="вопрос" i]',
        'textarea[placeholder*="ask" i]',
        '[role="textbox"]',
        '[contenteditable]',
        'textarea',
        'input'
    ]

    async def scan_page_like(obj):
        for sel in selectors:
            try:
                els = await obj.query_selector_all(sel)
                for el in els:
                    try:
                        # frames don't have is_visible; element handles do
                        if hasattr(el, "is_visible") and not await el.is_visible():
                            continue
                        box = await el.bounding_box()
                        if box and box.get("width", 0) > 100 and box.get("height", 0) >= 20:
                            return el
                    except Exception:
                        continue
            except Exception:
                continue
        return None

    # First, scan main document
    found = await scan_page_like(sidecar_page)
    if found:
        return found

    # Then, scan frames/iframes (sidecar UI may be inside an iframe)
    try:
        for frame in sidecar_page.frames:
            if frame == sidecar_page.main_frame:
                continue
            found = await scan_page_like(frame)
            if found:
                return found
    except Exception:
        pass

    # Heuristic via visible placeholder text in UI (often rendered as text in a container)
    try:
        hint = sidecar_page.locator('text=Задайте любой вопрос').first
        if await hint.count() > 0:
            hint_el = await hint.element_handle()
            if hint_el:
                handle = await hint_el.evaluate_handle(
                    """
                    (el) => {
                      function* walk(root) {
                        if (!root) return;
                        const stack = [root];
                        while (stack.length) {
                          const n = stack.pop();
                          if (!n) continue;
                          yield n;
                          // shadow
                          if (n.shadowRoot) stack.push(n.shadowRoot);
                          if (n.children) {
                            for (let i = n.children.length - 1; i >= 0; i--) stack.push(n.children[i]);
                          }
                        }
                      }

                      const container = el.closest('div') || el;
                      for (const n of walk(container)) {
                        if (!n.querySelectorAll) continue;
                        const inputs = n.querySelectorAll('textarea, input[type="text"], div[contenteditable="true"]');
                        for (const inp of inputs) {
                          const rect = inp.getBoundingClientRect();
                          if (rect && rect.width > 50 && rect.height > 20) return inp;
                        }
                      }
                      return null;
                    }
                    """
                )
                # if handle is element
                try:
                    tag = await handle.evaluate("e => e ? e.tagName.toLowerCase() : ''")
                    if tag:
                        return handle
                except Exception:
                    pass
    except Exception:
        pass

    # Deep shadow DOM search as final fallback
    try:
        handle = await sidecar_page.evaluate_handle(
            """
            () => {
              function* walk(root) {
                if (!root) return;
                const stack = [root];
                while (stack.length) {
                  const n = stack.pop();
                  if (!n) continue;
                  yield n;
                  if (n.shadowRoot) stack.push(n.shadowRoot);
                  if (n.children) {
                    for (let i = n.children.length - 1; i >= 0; i--) stack.push(n.children[i]);
                  }
                }
              }
              for (const n of walk(document)) {
                if (!n.querySelectorAll) continue;
                const inputs = n.querySelectorAll('textarea, input, [role="textbox"], [contenteditable]');
                for (const inp of inputs) {
                  const rect = inp.getBoundingClientRect();
                  if (rect && rect.width > 100 && rect.height > 20) return inp;
                }
              }
              return null;
            }
            """
        )
        try:
            tag = await handle.evaluate("e => e ? e.tagName.toLowerCase() : ''")
            if tag:
                return handle
        except Exception:
            pass
    except Exception:
        pass
    return None

async def test_single_domain(domain: str) -> dict:
    """Тест одного домена."""
    logger.info("🚀 ТЕСТ ОДНОГО ДОМЕНА COMET CDP")
    logger.info("="*50)

    result: dict = {
        "domain": domain,
        "status": "error",
        "inn": "",
        "email": "",
        "source_urls": [],
        "error": "",
        "raw_response": "",
    }
    
    if not PLAYWRIGHT_AVAILABLE:
        logger.error("❌ Playwright не установлен")
        result["error"] = "Playwright not installed"
        return result
    
    # Проверяем CDP - пытаемся подключиться через Playwright
    cdp_url = "http://127.0.0.1:9222"
    logger.info("🔍 Проверяю доступность CDP...")
    
    # Пробуем получить список targets (игнорируем статус код)
    try:
        response = requests.get(f"{cdp_url}/json", timeout=5)
        # Даже если статус 503, CDP может быть доступен для Playwright
        logger.info(f"📍 CDP ответил со статусом {response.status_code}")
    except Exception as e:
        logger.warning(f"⚠️ Не удалось проверить CDP через HTTP: {e}")
        logger.info("⏳ Попробую подключиться через Playwright напрямую...")
    
    # Подключаемся
    playwright = await async_playwright().start()
    browser = await playwright.chromium.connect_over_cdp(cdp_url)
    logger.info("✅ Подключено к Comet")
    
    try:
        logger.info(f"🌐 Тестирую домен: {domain}")
        
        # Используем существующий контекст CDP (важно для sidecar)
        context = browser.contexts[0] if browser.contexts else await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        # Открываем домен
        url = f"https://{domain}"
        logger.info(f"📍 Открываю: {url}")
        await page.goto(url, timeout=30000)
        await page.wait_for_timeout(3000)
        await dump_screenshot(page, f"{domain}_site_loaded")
        dump_desktop_screenshot(f"{domain}_site_loaded")
        
        def snapshot_cdp_targets(tag: str):
            try:
                r = requests.get(f"{cdp_url}/json", timeout=5)
                targets = r.json() if r.status_code == 200 else []
                out_dir = Path("cdp_debug")
                out_dir.mkdir(exist_ok=True)
                p = out_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{tag}_targets.json"
                p.write_text(json.dumps(targets, ensure_ascii=False, indent=2), encoding="utf-8")
                logger.info(f"🧭 CDP targets snapshot saved: {p} (count={len(targets)})")
                # Return lightweight signature list
                sig = [(t.get("type"), t.get("url"), t.get("title")) for t in targets]
                return sig
            except Exception as e:
                logger.warning(f"⚠️ Failed to snapshot CDP targets: {e}")
                return []

        # Открываем ассистента (UI) и СТРОГО проверяем, что он реально открыт
        before_targets = snapshot_cdp_targets("before_assistant_open")

        async def activate_comet_window() -> None:
            if not PYGETWINDOW_AVAILABLE:
                return
            try:
                wins = []
                for w in gw.getAllWindows():
                    if not w.title:
                        continue
                    if 'comet' in w.title.lower():
                        wins.append(w)
                if wins:
                    wins[0].activate()
                    await asyncio.sleep(0.5)
            except Exception:
                return

        sidecar_page = None
        assistant_input = None
        
        # CRITICAL FIX: Open sidecar directly via URL instead of hotkey
        # Hotkey opens chrome://sidebar which doesn't load UI properly
        # Direct URL works perfectly
        logger.info(f"🚀 Открываю ассистента напрямую через URL...")
        sidecar_url = "https://www.perplexity.ai/sidecar?copilot=true"
        
        try:
            sidecar_page = await context.new_page()
            await sidecar_page.goto(sidecar_url, timeout=30000)
            logger.info(f"✅ Sidecar открыт: {sidecar_url}")
        except Exception as e:
            logger.error(f"❌ Не удалось открыть sidecar: {e}")
            result["error"] = f"Failed to open sidecar: {e}"
            return result
        
        # Snapshot for evidence
        snapshot_cdp_targets(f"sidecar_opened_via_url")

        try:
            await sidecar_page.bring_to_front()
        except Exception:
            pass

        try:
            await sidecar_page.wait_for_selector('html[data-erp="sidecar"]', timeout=15000)
        except Exception:
            pass

        # CRITICAL: Wait for sidecar UI to fully load
        # The sidecar page loads in stages - first the container, then the interactive elements
        logger.info(f"⏳ Waiting for sidecar UI to fully load...")
        await sidecar_page.wait_for_timeout(3000)  # Give UI time to initialize
        
        # Wait for any textarea or contenteditable element to appear
        try:
            await sidecar_page.wait_for_selector('textarea, [contenteditable="true"], [role="textbox"]', timeout=10000)
            logger.info(f"✅ Interactive elements detected")
        except Exception as e:
            logger.warning(f"⚠️ No interactive elements found after 10s: {e}")

        await dump_screenshot(sidecar_page, f"{domain}_sidecar_opened")
        dump_desktop_screenshot(f"{domain}_sidecar_opened")

        assistant_input = await find_sidecar_input(sidecar_page)
        if not assistant_input:
            await dump_sidecar_snapshot(sidecar_page, f"input_not_found", input_el=None)
            await dump_screenshot(sidecar_page, f"{domain}_input_not_found")
            dump_desktop_screenshot(f"{domain}_input_not_found")
            logger.error("❌ Ассистент НЕ открылся: input не найден")
            result["error"] = "Assistant panel not opened (input not found)"
            return result

        # Success: assistant opened and input found
        await dump_sidecar_snapshot(sidecar_page, f"assistant_ready", input_el=assistant_input)
        logger.info(f"✅ Ассистент открыт и поле ввода найдено")

        if not sidecar_page or not assistant_input:
            logger.error("❌ Ассистент НЕ открылся: sidecar/input не найдены. См. cdp_debug/*assistant_attempt_* (desktop+sidecar snapshots).")
            result["error"] = "Assistant panel not opened (sidecar/input not found)"
            return result

        # Extra evidence: screenshot of domain page after assistant open
        await dump_screenshot(page, f"{domain}_after_assistant_open_site")
        dump_desktop_screenshot(f"{domain}_after_assistant_open_desktop")
        
        prompt = (
            "Найди на этом сайте ИНН компании (10-12 цифр) и адрес электронной почты. "
            "ОБЯЗАТЕЛЬНО проверь страницы: Контакты, Реквизиты, О компании, footer сайта. "
            "Ответ пришли СТРОГО в формате 4 строк (без лишнего текста). "
            "Формат: ИНН: <10-12 цифр или пусто>; Email: <email или пусто>; "
            "Источник1: <полная ссылка https://... где найден ИНН или email>; "
            "Источник2: <полная ссылка https://... где найден ИНН или email>. "
            "Если данных нет, оставь пусто и в источниках укажи 2 наиболее релевантные страницы сайта (https://...)."
        )
        followup_prompt = (
            "Дай ИТОГ строго в формате 4 строк, без пояснений и без markdown. "
            "Формат: ИНН: <10-12 цифр или пусто>; Email: <email или пусто>; "
            "Источник1: <https://...>; Источник2: <https://...>"
        )

        async def send_and_wait_once(text_to_send: str, tag_prefix: str) -> str:
            # IMPORTANT: Comet chat treats newline as Enter (send). Ensure prompt is a single message.
            safe_text = re.sub(r"[\r\n]+", " ", text_to_send).strip()
            logger.info(f"🤖 Ввожу промпт: {safe_text[:50]}...")

            # Sidecar can navigate to /sidecar/search/... which detaches old handles.
            # Re-acquire the input each time.
            try:
                await sidecar_page.bring_to_front()
            except Exception:
                pass

            input_handle = None
            for _ in range(5):
                input_handle = await find_sidecar_input(sidecar_page)
                if input_handle:
                    break
                await sidecar_page.wait_for_timeout(300)

            if not input_handle:
                await dump_sidecar_snapshot(sidecar_page, f"{tag_prefix}_input_not_found", input_el=None)
                await dump_debug_artifacts(sidecar_page, f"{tag_prefix}_input_not_found")
                return ""

            await dump_sidecar_snapshot(sidecar_page, f"{tag_prefix}_before_send", input_el=assistant_input)
            before_blocks = await collect_sidecar_text_blocks(sidecar_page, input_el=assistant_input)
            before_texts = [b.get("text", "") for b in before_blocks if b.get("text")]

            try:
                await input_handle.click()
                await sidecar_page.wait_for_timeout(50)
            except Exception:
                pass

            # Clear the input (works for both textarea and contenteditable)
            try:
                await sidecar_page.keyboard.press('Control+A')
                await sidecar_page.keyboard.press('Delete')
            except Exception:
                pass

            # Prefer setting value directly (avoids newline->Enter behavior), fallback to keyboard.
            try:
                await input_handle.fill(safe_text)
            except Exception:
                await sidecar_page.keyboard.insert_text(safe_text)
            await sidecar_page.wait_for_timeout(300)
            await dump_screenshot(sidecar_page, f"{domain}_{tag_prefix}_sidecar_prompt_typed")

            await sidecar_page.keyboard.press('Enter')
            logger.info("✅ Промпт отправлен")
            await dump_screenshot(sidecar_page, f"{domain}_{tag_prefix}_sidecar_after_send")

            logger.info("⏳ Жду финальный ответ ассистента (таймаут 120с)...")
            deadline = time.time() + 120
            last_joined = ""
            stable_ticks = 0
            last_filtered: list[str] = []
            while time.time() < deadline:
                await sidecar_page.wait_for_timeout(1000)
                after_blocks = await collect_sidecar_text_blocks(sidecar_page, input_el=assistant_input)
                after_texts = [b.get("text", "") for b in after_blocks if b.get("text")]
                new_texts = [t for t in after_texts if t not in before_texts]
                if not new_texts:
                    continue

                filtered: list[str] = []
                for t in new_texts:
                    s = (t or "").strip()
                    if not s:
                        continue
                    # Ignore pure prompt echo
                    if s == text_to_send.strip():
                        continue
                    # If block includes the prompt + more content, strip the first line
                    if s.startswith(text_to_send.strip()) and len(s) > len(text_to_send.strip()) + 5:
                        s = s[len(text_to_send.strip()):].lstrip("\n ")
                    if re.search(r"^(работает|ищу|подожд|думаю|собираю)\b", s, re.IGNORECASE):
                        continue
                    filtered.append(s)

                if not filtered:
                    stable_ticks = 0
                    continue

                joined = "\n".join(filtered)
                last_filtered = filtered

                # Check if response looks complete (has both INN and Email fields, or explicit "not found")
                has_inn_field = re.search(r"\bИНН\s*:\s*", joined, re.IGNORECASE)
                has_email_field = re.search(r"\bEmail\s*:\s*", joined, re.IGNORECASE)
                has_sources = re.search(r"\bИсточник[12]\s*:\s*https?://", joined, re.IGNORECASE)
                
                # Only return early if we have BOTH fields (even if empty) AND sources
                # This ensures assistant finished searching for both INN and Email
                if has_inn_field and has_email_field and has_sources:
                    # Wait a bit more to ensure no more content is coming
                    if joined == last_joined:
                        stable_ticks += 1
                    else:
                        last_joined = joined
                        stable_ticks = 0
                    
                    # Return after response is stable for 5 seconds (5 ticks)
                    if stable_ticks >= 5:
                        return joined
                else:
                    # Response not complete yet, reset stability counter
                    if joined == last_joined:
                        stable_ticks += 1
                    else:
                        last_joined = joined
                        stable_ticks = 0
                    
                    # If response is stable for 8 seconds but incomplete, return what we have
                    if stable_ticks >= 8:
                        return "\n".join(last_filtered)
            return ""

        response_text = await send_and_wait_once(prompt, "step1")
        if response_text and re.search(r"\b(загрузк|downloads|tab search)\b", response_text, re.IGNORECASE):
            logger.warning("⚠️ Похоже, ассистент отвечает не про домен (downloads/tab search). Перефокусирую домен и повторяю 1 раз...")
            try:
                await page.bring_to_front()
                await page.wait_for_timeout(500)
            except Exception:
                pass
            response_text = await send_and_wait_once(prompt, "step1_retry")

        # If response doesn't contain the required format, ask explicitly for a single-line final answer.
        if response_text and not (
            re.search(r"\bНайдено\s*:\s*(да|нет)\b", response_text, re.IGNORECASE)
            or "|" in response_text
            or re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", response_text)
            or re.search(r"\bИНН\b", response_text, re.IGNORECASE)
        ):
            logger.warning("⚠️ Ответ не в требуемом формате — отправляю уточняющий промпт для финальной строки...")
            response_text = await send_and_wait_once(followup_prompt, "step2")

        if not response_text:
            await dump_sidecar_snapshot(sidecar_page, "after_send_no_response", input_el=assistant_input)
            await dump_debug_artifacts(sidecar_page, "assistant_no_response")
            await dump_screenshot(sidecar_page, f"{domain}_sidecar_no_response")
            logger.error("❌ Ассистент не дал нового ответа (или селекторы ответа не найдены)")
            result["error"] = "No assistant response"
            return result

        await dump_sidecar_snapshot(sidecar_page, "after_send_with_response", input_el=assistant_input)
        await dump_screenshot(sidecar_page, f"{domain}_sidecar_with_response")
        
        logger.info(f"📋 Ответ ассистента: {response_text}")
        result["raw_response"] = response_text

        inn_match = re.search(r'(?:ИНН[:\s]*)(\d{10,12})', response_text, re.IGNORECASE)
        inn = inn_match.group(1) if inn_match else ""
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', response_text)
        email = email_match.group(0) if email_match else ""

        # Extract up to 2 source URLs
        raw_urls = re.findall(r'https?://[^\s\]\)\}"\'>]+', response_text)
        seen = set()
        urls = []
        for u in raw_urls:
            if u in seen:
                continue
            seen.add(u)
            urls.append(u)
            if len(urls) >= 2:
                break
        source_url_1 = urls[0] if len(urls) > 0 else ""
        source_url_2 = urls[1] if len(urls) > 1 else ""

        logger.info("📊 Результат:")
        logger.info(f"   Домен: {domain}")
        logger.info(f"   ИНН: {inn}")
        logger.info(f"   Email: {email}")
        logger.info(f"   Источник1: {source_url_1}")
        logger.info(f"   Источник2: {source_url_2}")

        result["inn"] = inn or ""
        result["email"] = email or ""
        result["source_urls"] = [u for u in [source_url_1, source_url_2] if u]
        result["status"] = "success" if (inn or email) else "not_found"

        if inn or email:
            logger.info("✅ УСПЕХ - Данные найдены в ответе ассистента!")
        else:
            logger.warning("⚠️ Ассистент ответил, но ИНН/email не найдены")
        
        # По умолчанию НЕ закрываем контекст/браузер, чтобы ты мог визуально увидеть, что панель не закрылась.
        if os.environ.get("COMET_TEST_CLOSE", "0") == "1":
            await context.close()
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        result["error"] = str(e)
    
    finally:
        if os.environ.get("COMET_TEST_CLOSE", "0") == "1":
            await browser.close()
        logger.info("🎉 ТЕСТ ЗАВЕРШЕН!")

    return result

async def main():
    """Главная функция."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", type=str, default=os.environ.get("COMET_DOMAIN", "metallsnab-nn.ru"))
    parser.add_argument("--json", action="store_true", help="Print JSON result to stdout")
    args = parser.parse_args()

    if args.json:
        try:
            # Ensure stdout remains clean JSON for subprocess parsing
            for h in list(logger.handlers):
                if isinstance(h, logging.StreamHandler) and getattr(h, "stream", None) is sys.stdout:
                    logger.removeHandler(h)
            logger.addHandler(logging.StreamHandler(sys.stderr))
        except Exception:
            pass

    res = await test_single_domain(args.domain)
    if args.json:
        sys.stdout.write(json.dumps(res, ensure_ascii=False))
        sys.stdout.flush()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⚠️ Тест прерван")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
