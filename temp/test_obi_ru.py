"""Test script for interactive INN finder agent on obi.ru."""
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


async def test_obi_ru():
    """Test interactive agent on obi.ru."""
    print("=" * 80)
    print("Testing Interactive INN Finder on obi.ru")
    print("=" * 80)
    print("\nURL: https://obi.ru/strojmaterialy/suhie-stroitelnye-smesi/cement-i-sypuchie-materialy")
    print("Expected: Should find INN for OBI\n")
    
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
            # Test on obi.ru - start from homepage
            result = await finder.find_inn(
                domain="obi.ru",
                start_url="https://www.obi.ru"
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
                try:
                    print(f"Context: {context[:200]}...")
                except UnicodeEncodeError:
                    print(f"Context: [contains non-ASCII characters, length: {len(context)}]")
            else:
                print(f"Context: None")
            print(f"\nActions taken ({len(result.get('actions_taken', []))}):")
            for i, action in enumerate(result.get('actions_taken', []), 1):
                print(f"  {i}. {action}")
            
            if result.get('success') and result.get('inn'):
                print(f"\n[SUCCESS] Found INN: {result.get('inn')}!")
                return 0
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
    exit_code = asyncio.run(test_obi_ru())
    sys.exit(exit_code)



