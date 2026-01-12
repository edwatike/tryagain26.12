"""
Test direct input to Comet assistant using CDP commands
"""
import asyncio
import requests
import json
import time

async def test_direct_input():
    """Test sending input directly via CDP"""
    cdp_url = "http://127.0.0.1:9222"
    
    print("🚀 TESTING DIRECT CDP INPUT")
    print("="*60)
    
    # Get all targets
    response = requests.get(f"{cdp_url}/json")
    targets = response.json()
    
    print(f"\n📋 Found {len(targets)} CDP targets:")
    for i, t in enumerate(targets):
        print(f"   {i+1}. {t.get('type')}: {t.get('url')[:80]}")
    
    # Find sidebar target
    sidebar_target = None
    for t in targets:
        url = t.get('url', '')
        if 'chrome://sidebar' in url or 'perplexity.ai/sidecar' in url:
            sidebar_target = t
            print(f"\n✅ Found sidebar target: {url}")
            break
    
    if not sidebar_target:
        print(f"\n❌ Sidebar not found!")
        print(f"\n💡 MANUAL ACTION REQUIRED:")
        print(f"   1. Open Comet browser")
        print(f"   2. Press Alt+A or Ctrl+Shift+A to open assistant")
        print(f"   3. Make sure assistant panel is visible")
        print(f"   4. Run this script again")
        return False
    
    # Connect to sidebar via WebSocket
    ws_url = sidebar_target.get('webSocketDebuggerUrl')
    if not ws_url:
        print(f"❌ No WebSocket URL for sidebar")
        return False
    
    print(f"\n🔌 WebSocket URL: {ws_url}")
    
    # Use playwright to connect
    from playwright.async_api import async_playwright
    
    playwright = await async_playwright().start()
    try:
        browser = await playwright.chromium.connect_over_cdp(cdp_url)
        print(f"✅ Connected to CDP")
        
        context = browser.contexts[0] if browser.contexts else None
        if not context:
            print(f"❌ No context found")
            return False
        
        # Find sidebar page
        sidebar_page = None
        for page in context.pages:
            try:
                url = page.url
                if 'chrome://sidebar' in url or 'perplexity.ai/sidecar' in url:
                    sidebar_page = page
                    print(f"✅ Found sidebar page: {url}")
                    break
            except:
                continue
        
        if not sidebar_page:
            print(f"❌ Sidebar page not accessible")
            return False
        
        # Get page content
        await sidebar_page.bring_to_front()
        await sidebar_page.wait_for_timeout(1000)
        
        content = await sidebar_page.content()
        print(f"\n📄 Sidebar HTML length: {len(content)} chars")
        
        # Try to find any interactive element
        print(f"\n🔍 Looking for interactive elements...")
        
        # Evaluate JavaScript to find all inputs
        inputs_info = await sidebar_page.evaluate("""
            () => {
                const inputs = [];
                const allElements = document.querySelectorAll('*');
                
                for (const el of allElements) {
                    const tag = el.tagName.toLowerCase();
                    if (tag === 'textarea' || tag === 'input' || 
                        el.getAttribute('contenteditable') === 'true' ||
                        el.getAttribute('role') === 'textbox') {
                        
                        const rect = el.getBoundingClientRect();
                        inputs.push({
                            tag: tag,
                            type: el.getAttribute('type') || '',
                            placeholder: el.getAttribute('placeholder') || '',
                            contenteditable: el.getAttribute('contenteditable') || '',
                            role: el.getAttribute('role') || '',
                            visible: rect.width > 0 && rect.height > 0,
                            x: rect.x,
                            y: rect.y,
                            width: rect.width,
                            height: rect.height
                        });
                    }
                }
                
                return inputs;
            }
        """)
        
        print(f"   Found {len(inputs_info)} potential input elements:")
        for inp in inputs_info:
            print(f"      - {inp['tag']} (visible={inp['visible']}, size={inp['width']}x{inp['height']})")
        
        if not inputs_info:
            print(f"\n❌ NO INPUT ELEMENTS FOUND")
            print(f"\n💡 DIAGNOSIS:")
            print(f"   The Comet assistant sidebar is open, but has no input field.")
            print(f"   This means:")
            print(f"   1. Assistant might not be fully loaded")
            print(f"   2. Assistant might be in a different state (e.g., showing results)")
            print(f"   3. Input field might be in a shadow DOM or iframe")
            
            # Check for iframes
            frames = sidebar_page.frames
            print(f"\n🔍 Checking {len(frames)} frames...")
            for i, frame in enumerate(frames):
                try:
                    frame_url = frame.url
                    print(f"   Frame {i}: {frame_url}")
                    
                    # Try to find input in frame
                    frame_inputs = await frame.evaluate("""
                        () => {
                            const inputs = document.querySelectorAll('textarea, input, [contenteditable="true"], [role="textbox"]');
                            return inputs.length;
                        }
                    """)
                    if frame_inputs > 0:
                        print(f"      ✅ Found {frame_inputs} inputs in this frame!")
                except Exception as e:
                    print(f"      ❌ Error checking frame: {e}")
            
            return False
        
        # Try to click and type
        visible_inputs = [inp for inp in inputs_info if inp['visible']]
        if visible_inputs:
            inp = visible_inputs[0]
            print(f"\n✍️ Trying to use input at ({inp['x']}, {inp['y']})")
            
            try:
                await sidebar_page.mouse.click(inp['x'] + inp['width']//2, inp['y'] + inp['height']//2)
                await sidebar_page.wait_for_timeout(500)
                
                await sidebar_page.keyboard.type("Test message")
                await sidebar_page.wait_for_timeout(500)
                
                print(f"   ✅ Typed successfully!")
                return True
            except Exception as e:
                print(f"   ❌ Error: {e}")
                return False
        
        return False
        
    finally:
        await playwright.stop()

if __name__ == "__main__":
    result = asyncio.run(test_direct_input())
    import sys
    sys.exit(0 if result else 1)
