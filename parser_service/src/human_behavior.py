"""Human behavior simulation for anti-detection."""
import asyncio
import random


async def random_delay(min_ms: int = 1000, max_ms: int = 3000):
    """Random delay to simulate human behavior."""
    delay = random.randint(min_ms, max_ms) / 1000.0
    await asyncio.sleep(delay)


async def human_like_scroll(page):
    """Simulate human-like scrolling."""
    viewport_height = await page.evaluate("window.innerHeight")
    scroll_height = await page.evaluate("document.body.scrollHeight")
    
    current_position = 0
    while current_position < scroll_height:
        scroll_amount = random.randint(300, 800)
        current_position += scroll_amount
        await page.evaluate(f"window.scrollTo(0, {current_position})")
        await random_delay(500, 1500)
        
        if current_position >= scroll_height:
            break


async def human_like_mouse_movement(page):
    """Simulate random mouse movements."""
    # Simple mouse movement simulation
    for _ in range(random.randint(2, 5)):
        x = random.randint(100, 800)
        y = random.randint(100, 600)
        await page.mouse.move(x, y)
        await random_delay(200, 500)

