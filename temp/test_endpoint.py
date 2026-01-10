import httpx
import asyncio

async def test():
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "http://127.0.0.1:8000/inn-extraction/extract-batch",
            json={"domains": ["test.com"]}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")

asyncio.run(test())
