"""Integration tests for server startup and basic functionality."""
import pytest
import sys
from pathlib import Path

# Добавляем путь к backend в sys.path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))


def test_app_import():
    """Test that app can be imported without errors."""
    try:
        from app.main import app
        assert app is not None
        assert app.title == "B2B Platform API"
    except Exception as e:
        pytest.fail(f"Failed to import app: {e}")


def test_app_creation():
    """Test that FastAPI app is created correctly."""
    from app.main import app
    
    assert app.title == "B2B Platform API"
    assert app.version == "1.0.0"
    assert app.description is not None


def test_health_endpoint_exists():
    """Test that health endpoint is registered."""
    from app.main import app
    
    # Проверяем, что health endpoint зарегистрирован
    routes = [route.path for route in app.routes]
    assert "/health" in routes or any("/health" in str(route.path) for route in app.routes)


@pytest.mark.asyncio
async def test_health_endpoint_response():
    """Test health endpoint returns correct response."""
    from httpx import AsyncClient
    from app.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root endpoint returns API information."""
    from httpx import AsyncClient
    from app.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["name"] == "B2B Platform API"


def test_cors_middleware_configured():
    """Test that CORS middleware is configured."""
    from app.main import app
    
    # Проверяем наличие CORS middleware
    middleware_classes = [type(m).__name__ for m in app.user_middleware]
    assert "CORSMiddleware" in middleware_classes or any("CORS" in m for m in middleware_classes)


def test_exception_handlers_configured():
    """Test that exception handlers are configured."""
    from app.main import app
    
    # Проверяем наличие обработчиков исключений
    assert len(app.exception_handlers) > 0


