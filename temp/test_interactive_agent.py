"""Test script for interactive INN finder agent."""
import asyncio
import sys
import os
from pathlib import Path

# Add ollama_inn_extractor to path
project_root = Path(__file__).parent.parent
ollama_dir = project_root / "ollama_inn_extractor"
if ollama_dir.exists() and str(ollama_dir) not in sys.path:
    sys.path.insert(0, str(ollama_dir))

from app.agents.interactive_inn_finder import InteractiveINNFinder
from app.ollama_client import OllamaClient


async def test_maxidom():
    """Test interactive agent on maxidom.ru."""
    print("=" * 80)
    print("Testing Interactive INN Finder on maxidom.ru")
    print("=" * 80)
    print("\nExpected: Should find INN 7804064663")
    print("Expected path: Homepage -> 'О компании' -> 'Контакты' -> 'Реквизиты'\n")
    
    try:
        # Create Ollama client
        ollama_client = OllamaClient()
        
        # Create interactive finder
        finder = InteractiveINNFinder(
            chrome_cdp_url="http://127.0.0.1:9222",
            ollama_client=ollama_client,
            max_attempts=15
        )
        
        try:
            # Test on maxidom.ru
            result = await finder.find_inn(
                domain="maxidom.ru",
                start_url="https://www.maxidom.ru"
            )
            
            print("\n" + "=" * 80)
            print("RESULTS")
            print("=" * 80)
            print(f"Success: {result.get('success')}")
            print(f"INN: {result.get('inn')}")
            print(f"URL: {result.get('url')}")
            print(f"Attempts: {result.get('attempts')}")
            context = result.get('context') or ''
            if context:
                # Encode to avoid Unicode errors in Windows console
                try:
                    print(f"Context: {context[:200]}...")
                except UnicodeEncodeError:
                    print(f"Context: [contains non-ASCII characters, length: {len(context)}]")
            else:
                print(f"Context: None")
            print(f"\nActions taken ({len(result.get('actions_taken', []))}):")
            for i, action in enumerate(result.get('actions_taken', []), 1):
                print(f"  {i}. {action}")
            
            if result.get('success') and result.get('inn') == '7804064663':
                print("\n[SUCCESS] Found correct INN!")
                return 0
            elif result.get('success'):
                print(f"\n[WARNING] Found INN {result.get('inn')}, but expected 7804064663")
                return 1
            else:
                print("\n[FAILED] INN not found")
                return 1
                
        finally:
            await finder.close()
            await ollama_client.close()
            
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(test_maxidom())
    sys.exit(exit_code)

