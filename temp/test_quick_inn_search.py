import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
ollama_dir = project_root / "ollama_inn_extractor"
if ollama_dir.exists() and str(ollama_dir) not in sys.path:
    sys.path.insert(0, str(ollama_dir))

from app.agents.interactive_inn_finder import InteractiveINNFinder
from app.ollama_client import OllamaClient

async def test_quick():
    print("=" * 80)
    print("Quick test: Agent finds INN on ANY page of domain")
    print("=" * 80)
    
    try:
        ollama_client = OllamaClient(base_url="http://127.0.0.1:11434", model_name="qwen2.5:7b")
        finder = InteractiveINNFinder(
            chrome_cdp_url="http://127.0.0.1:9222",
            ollama_client=ollama_client,
            max_attempts=10
        )
        
        result = await finder.find_inn(
            domain="mc.ru",
            start_url="https://mc.ru",
            timeout=90
        )
        
        print("\n" + "=" * 80)
        print("RESULTS")
        print("=" * 80)
        print(f"Success: {result.get('success')}")
        print(f"INN: {result.get('inn')}")
        print(f"URL: {result.get('url')}")
        print(f"Attempts: {result.get('attempts')}")
        print(f"Actions: {len(result.get('actions_taken', []))}")
        if result.get('context'):
            print(f"Context: {result.get('context')[:200]}")
        
        if result.get('success'):
            print("\n[SUCCESS] Agent found INN!")
        else:
            print("\n[FAILED] Agent did not find INN")
        
        # Don't close browser
        await finder.close()
        await ollama_client.close()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_quick())

