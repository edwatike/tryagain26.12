"""
Startup script for parser service API with correct event loop policy for Windows
"""
import asyncio
import sys

# CRITICAL: Set event loop policy BEFORE any imports
# This must be the very first thing to avoid NotImplementedError on Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

if __name__ == "__main__":
    from api import app
    
    # Try Hypercorn first (better Windows support), fallback to uvicorn
    try:
        from hypercorn.asyncio import serve
        from hypercorn.config import Config
        
        config = Config()
        config.bind = ["127.0.0.1:9003"]
        config.loglevel = "info"
        
        # Use asyncio.run() which respects the policy set above
        asyncio.run(serve(app, config))
    except ImportError:
        # Fallback to uvicorn if Hypercorn is not available
        import uvicorn
        
        async def run_server():
            config = uvicorn.Config(
                app=app,
                host="127.0.0.1",
                port=9003,
                log_level="info",
                access_log=True
            )
            server = uvicorn.Server(config)
            await server.serve()
        
        asyncio.run(run_server())

