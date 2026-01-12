"""
MANUAL COMET TEST - Find working solution for assistant activation
"""
import asyncio
import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'experiments', 'comet-integration'))

async def test_comet_manual():
    """Test Comet manually to find working solution"""
    from playwright.async_api import async_playwright
    import time
    
    print("🚀 MANUAL COMET TEST")
    print("="*60)
    
    # Connect to Comet CDP
    cdp_url = "http://127.0.0.1:9222"
    playwright = await async_playwright().start()
    
    try:
        browser = await playwright.chromium.connect_over_cdp(cdp_url)
        print(f"✅ Connected to Comet CDP")
        
        # Get existing context
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        
        # Create new page
        page = await context.new_page()
        
        # Navigate to test domain
        domain = "elektro.ru"
        url = f"https://{domain}"
        print(f"\n📍 Opening: {url}")
        await page.goto(url, timeout=30000)
        await page.wait_for_timeout(3000)
        print(f"✅ Page loaded")
        
        # Try to open assistant with keyboard shortcut
        print(f"\n🎯 Trying to open Comet assistant...")
        print(f"   Method 1: Alt+A")
        await page.keyboard.press('Alt+A')
        await page.wait_for_timeout(2000)
        
        # Check if sidecar opened
        pages_count = len(context.pages)
        print(f"   Pages count: {pages_count}")
        
        # Look for sidecar page
        sidecar_page = None
        for p in context.pages:
            try:
                u = p.url.lower()
                if 'perplexity.ai/sidecar' in u or 'chrome://sidebar' in u:
                    sidecar_page = p
                    print(f"   ✅ Found sidecar: {p.url}")
                    break
            except:
                continue
        
        if not sidecar_page:
            print(f"   ❌ Sidecar not found, trying Method 2: Ctrl+Shift+A")
            await page.keyboard.press('Control+Shift+A')
            await page.wait_for_timeout(2000)
            
            for p in context.pages:
                try:
                    u = p.url.lower()
                    if 'perplexity.ai/sidecar' in u or 'chrome://sidebar' in u:
                        sidecar_page = p
                        print(f"   ✅ Found sidecar: {p.url}")
                        break
                except:
                    continue
        
        if not sidecar_page:
            print(f"\n❌ FAILED: Sidecar did not open")
            print(f"\n💡 SOLUTION NEEDED:")
            print(f"   1. Check if Comet browser has assistant enabled")
            print(f"   2. Try manual activation in Comet browser")
            print(f"   3. Check Comet settings for assistant hotkey")
            return False
        
        # Try to find input field
        print(f"\n🔍 Looking for input field in sidecar...")
        await sidecar_page.bring_to_front()
        await sidecar_page.wait_for_timeout(2000)
        
        # Try different selectors
        selectors = [
            'textarea[placeholder*="задайте" i]',
            'textarea[placeholder*="вопрос" i]',
            'textarea',
            'input[type="text"]',
            '[role="textbox"]',
            '[contenteditable="true"]'
        ]
        
        input_found = None
        for sel in selectors:
            try:
                els = await sidecar_page.query_selector_all(sel)
                for el in els:
                    try:
                        if await el.is_visible():
                            box = await el.bounding_box()
                            if box and box.get('width', 0) > 50:
                                input_found = el
                                print(f"   ✅ Found input: {sel}")
                                break
                    except:
                        continue
                if input_found:
                    break
            except:
                continue
        
        if not input_found:
            print(f"   ❌ Input field not found")
            
            # Dump page content for analysis
            content = await sidecar_page.content()
            print(f"\n📄 Sidecar HTML length: {len(content)} chars")
            
            # Try to click on the placeholder text area
            print(f"\n💡 Trying alternative: Click on placeholder area")
            try:
                # Click in the center of sidecar
                viewport = sidecar_page.viewport_size
                if viewport:
                    x = viewport['width'] // 2
                    y = viewport['height'] - 100  # Near bottom where input usually is
                    print(f"   Clicking at ({x}, {y})")
                    await sidecar_page.mouse.click(x, y)
                    await sidecar_page.wait_for_timeout(1000)
                    
                    # Try typing directly
                    print(f"   Typing test message...")
                    await sidecar_page.keyboard.type("test")
                    await sidecar_page.wait_for_timeout(500)
                    
                    # Check if text appeared
                    content_after = await sidecar_page.content()
                    if 'test' in content_after.lower():
                        print(f"   ✅ Direct typing works!")
                        return True
                    else:
                        print(f"   ❌ Direct typing failed")
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            return False
        
        # Try to use the input
        print(f"\n✍️ Testing input field...")
        try:
            await input_found.click()
            await sidecar_page.wait_for_timeout(500)
            await input_found.fill("Find INN and email on this website")
            await sidecar_page.wait_for_timeout(500)
            print(f"   ✅ Input works!")
            
            # Press Enter
            await sidecar_page.keyboard.press('Enter')
            print(f"   ✅ Prompt sent!")
            
            # Wait for response
            print(f"\n⏳ Waiting for response (10 seconds)...")
            await sidecar_page.wait_for_timeout(10000)
            
            # Check for response
            content = await sidecar_page.content()
            if len(content) > 5000:  # Response should add content
                print(f"   ✅ Response received!")
                return True
            else:
                print(f"   ⚠️ No response yet")
                return False
                
        except Exception as e:
            print(f"   ❌ Error using input: {e}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await playwright.stop()

if __name__ == "__main__":
    result = asyncio.run(test_comet_manual())
    sys.exit(0 if result else 1)
