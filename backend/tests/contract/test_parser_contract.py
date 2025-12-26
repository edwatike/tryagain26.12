"""Contract tests for Parser Service integration."""
import pytest
from app.adapters.parser_client import ParserClient


@pytest.mark.asyncio
async def test_parser_client_health_check():
    """Test Parser Service health check contract."""
    # This is a placeholder - actual contract tests would verify
    # the expected API contract with Parser Service
    client = ParserClient("http://localhost:9003")
    # In real tests, this would check the actual service
    # health = await client.health_check()
    # assert health["status"] in ["ok", "unhealthy"]
    await client.close()

