"""Entry point for Parser Service API."""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=9003,
        reload=True,
        log_level="info"
    )

