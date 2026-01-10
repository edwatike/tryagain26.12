import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
ollama_dir = project_root / "ollama_inn_extractor"
if ollama_dir.exists() and str(ollama_dir) not in sys.path:
    sys.path.insert(0, str(ollama_dir))

from app.agents.interactive_inn_finder import InteractiveINNFinder
from app.ollama_client import OllamaClient

async def test_mc_ru():
    print("=" * 80)
    print("Testing Interactive INN Finder on mc.ru")
    print("=" * 80)
    print(f"\nStart time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Expected: Should find REAL company INN for mc.ru")
    print("Start URL: https://mc.ru\n")

    start_time = datetime.now()
    
    try:
        ollama_client = OllamaClient()
        finder = InteractiveINNFinder(
            chrome_cdp_url="http://127.0.0.1:9222",
            ollama_client=ollama_client,
            max_attempts=15
        )

        try:
            result = await finder.find_inn(
                domain="mc.ru",
                start_url="https://mc.ru"
            )

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            print("\n" + "=" * 80)
            print("RESULTS")
            print("=" * 80)
            print(f"Duration: {duration:.2f} seconds")
            print(f"Success: {result.get('success')}")
            print(f"INN: {result.get('inn')}")
            print(f"URL: {result.get('url')}")
            print(f"Attempts: {result.get('attempts')}")
            context = result.get('context') or ''
            if context:
                try:
                    print(f"Context: {context[:300]}...")
                except UnicodeEncodeError:
                    print(f"Context: [contains non-ASCII characters, length: {len(context)}]")
            else:
                print(f"Context: None")
            print(f"\nActions taken ({len(result.get('actions_taken', []))}):")
            for i, action in enumerate(result.get('actions_taken', []), 1):
                print(f"  {i}. {action}")

            if result.get('success') and result.get('inn'):
                # Check if INN is from tracking/metrics
                inn = result.get('inn', '')
                context_str = str(result.get('context', '')).lower()
                
                # Check for tracking indicators
                is_tracking = any(indicator in context_str for indicator in [
                    '_ym', 'yandex', 'metrika', 'tracking', 'analytics',
                    'google', 'gtag', 'ga_', 'session', 'cookie'
                ])
                
                if is_tracking:
                    print(f"\n[WARNING] Found INN might be from tracking/metrics: {inn}")
                    print(f"Context contains tracking indicators: {context_str[:200]}")
                    print("[FAILED] INN is likely NOT a company INN")
                    return 1
                else:
                    print(f"\n[SUCCESS] Found INN: {inn}!")
                    return 0
            else:
                print("\n[FAILED] INN not found")
                return 1

        finally:
            # finder.close() is no longer called to keep browser open
            await ollama_client.close()

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(test_mc_ru())
    sys.exit(exit_code)



