"""FastAPI application entry point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import traceback

from app.config import settings
from app.transport.routers import (
    health,
    moderator_suppliers,
    keywords,
    blacklist,
    parsing,
    parsing_runs,
    domains_queue,
    attachments,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    import logging
    # Настраиваем логирование - используем только stdout для совместимости с Windows/uvicorn
    # Не используем sys.stderr напрямую, чтобы избежать OSError на Windows
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        force=True
    )
    # Включаем логирование для uvicorn и starlette
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("starlette").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    
    # Логируем при старте приложения - безопасное логирование
    logger = logging.getLogger(__name__)
    try:
        logger.info("=== Logging configured ===")
        logger.info("=== APPLICATION STARTUP COMPLETE ===")
    except Exception:
        pass  # Если логирование не работает при старте, просто пропускаем
    
    yield
    # Shutdown


app = FastAPI(
    title="B2B Platform API",
    version="1.0.0",
    description="API for B2B Platform - supplier moderation and parsing system",
    lifespan=lifespan,
)

# Добавляем логирование при старте
import logging
_startup_logger = logging.getLogger(__name__)
try:
    _startup_logger.info("=== FastAPI app created ===")
    _startup_logger.info(f"=== CORS origins: {settings.cors_origins_list} ===")
except Exception:
    pass  # Безопасное логирование при старте

# Добавляем обработчик ошибок на уровне Starlette
from starlette.requests import Request as StarletteRequest

async def starlette_exception_handler(request: StarletteRequest, exc: Exception):
    """Starlette-level exception handler."""
    import logging
    import traceback
    logger = logging.getLogger(__name__)
    # Безопасное логирование - оборачиваем в try-except
    try:
        logger.error(f"=== STARLETTE EXCEPTION: {type(exc).__name__}: {exc} ===")
        logger.error(f"=== STARLETTE TRACEBACK:\n{traceback.format_exc()} ===")
    except Exception:
        pass  # Если логирование не работает, просто пропускаем
    
    error_detail = f"{type(exc).__name__}: {str(exc)}"
    if settings.ENV == "development":
        error_detail += f"\n{traceback.format_exc()}"
    
    response = JSONResponse(
        status_code=500,
        content={"detail": error_detail}
    )
    
    origin = request.headers.get("origin")
    if origin and origin in settings.cors_origins_list:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
    
    return response

# Добавляем обработчик на уровне Starlette
app.add_exception_handler(Exception, starlette_exception_handler)

# CORS Middleware - должен быть первым
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Middleware для обработки ошибок с CORS
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import json

class CORSExceptionMiddleware(BaseHTTPMiddleware):
    """Middleware для добавления CORS заголовков к ошибкам."""
    async def dispatch(self, request, call_next):
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            response = await call_next(request)
            # Убедимся, что CORS заголовки есть даже при ошибках
            origin = request.headers.get("origin")
            if origin and origin in settings.cors_origins_list:
                if "Access-Control-Allow-Origin" not in response.headers:
                    response.headers["Access-Control-Allow-Origin"] = origin
                    response.headers["Access-Control-Allow-Credentials"] = "true"
                    response.headers["Access-Control-Allow-Methods"] = "*"
                    response.headers["Access-Control-Allow-Headers"] = "*"
            return response
        except Exception as exc:
            import traceback
            # Безопасное логирование - оборачиваем в try-except
            try:
                logger.error(f"Exception in middleware: {type(exc).__name__}: {exc}", exc_info=True)
            except Exception:
                pass  # Если логирование не работает, просто пропускаем
            
            # Обработка исключений на уровне middleware
            
            error_detail = f"{type(exc).__name__}: {str(exc)}"
            if settings.ENV == "development":
                error_detail += f"\n{traceback.format_exc()}"
            
            response = JSONResponse(
                status_code=500,
                content={"detail": error_detail}
            )
            
            origin = request.headers.get("origin")
            if origin and origin in settings.cors_origins_list:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Methods"] = "*"
                response.headers["Access-Control-Allow-Headers"] = "*"
            
            return response

app.add_middleware(CORSExceptionMiddleware)


# Global exception handler for debugging - ДОЛЖНЫ быть ДО включения роутеров!
from fastapi.exceptions import HTTPException as FastAPIHTTPException

@app.exception_handler(FastAPIHTTPException)
async def http_exception_handler(request: Request, exc: FastAPIHTTPException):
    """HTTP exception handler with CORS headers."""
    response = JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )
    
    # Add CORS headers manually
    origin = request.headers.get("origin")
    if origin and origin in settings.cors_origins_list:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
    
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to log errors and return details with CORS headers."""
    import logging
    logger = logging.getLogger(__name__)
    # Безопасное логирование - оборачиваем в try-except
    try:
        logger.error(f"Global exception handler called: {type(exc).__name__}: {exc}", exc_info=True)
    except Exception:
        pass  # Если логирование не работает, просто пропускаем
    
    error_detail = f"{type(exc).__name__}: {str(exc)}"
    if settings.ENV == "development":
        error_detail += f"\n{traceback.format_exc()}"
    
    # Create response with CORS headers
    response = JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": error_detail}
    )
    
    # Add CORS headers manually
    origin = request.headers.get("origin")
    if origin and origin in settings.cors_origins_list:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
    
    return response


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "B2B Platform API",
        "version": "1.0.0",
        "description": "API for B2B Platform - supplier moderation and parsing system",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "suppliers": "/moderator/suppliers",
            "keywords": "/keywords",
            "blacklist": "/moderator/blacklist",
            "parsing": "/parsing",
            "parsing_runs": "/parsing/runs",
            "domains_queue": "/domains",
            "attachments": "/attachments",
        }
    }


# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(moderator_suppliers.router, prefix="/moderator", tags=["Suppliers"])
app.include_router(keywords.router, prefix="/keywords", tags=["Keywords"])
app.include_router(blacklist.router, prefix="/moderator", tags=["Blacklist"])
app.include_router(parsing.router, prefix="/parsing", tags=["Parsing"])
app.include_router(parsing_runs.router, prefix="/parsing", tags=["Parsing Runs"])
app.include_router(domains_queue.router, prefix="/domains", tags=["Domains Queue"])
app.include_router(attachments.router, prefix="/attachments", tags=["Attachments"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

