"""Test script to check if subprocess can run Comet script."""
import asyncio
import json
import sys

async def test_comet():
    script_path = r"D:\tryagain\experiments\comet-integration\test_single_domain.py"
    domain = "russteels.ru"
    
    print(f"Running Comet script: {script_path}")
    print(f"Domain: {domain}")
    print(f"Python: {sys.executable}")
    print("")
    
    try:
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            script_path,
            "--domain", domain,
            "--json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        print("Process started, waiting for completion...")
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=180)
        
        stdout_str = stdout.decode('utf-8')
        stderr_str = stderr.decode('utf-8')
        
        print(f"\nstdout length: {len(stdout_str)} chars")
        print(f"stderr length: {len(stderr_str)} chars")
        
        if stderr_str:
            print(f"\nstderr (first 500 chars):\n{stderr_str[:500]}")
        
        # Find JSON in stdout
        lines = stdout_str.strip().split('\n')
        json_line = lines[-1] if lines else ""
        
        print(f"\nLast line (JSON):\n{json_line[:500]}")
        
        # Parse JSON
        result = json.loads(json_line)
        print(f"\nParsed result:")
        print(f"  Domain: {result.get('domain')}")
        print(f"  Status: {result.get('status')}")
        print(f"  INN: {result.get('inn')}")
        print(f"  Email: {result.get('email')}")
        
        if result.get('status') == 'success' and (result.get('inn') or result.get('email')):
            print(f"\n✅ SUCCESS! Comet found data!")
        else:
            print(f"\n❌ FAILED! Comet returned error or no data")
            
    except asyncio.TimeoutError:
        print("\n❌ TIMEOUT after 180 seconds")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_comet())
