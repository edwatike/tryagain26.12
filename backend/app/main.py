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
    import sys
    # Настраиваем логирование для всех уровней
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.StreamHandler(sys.stderr)
        ],
        force=True
    )
    # Включаем логирование для uvicorn и starlette
    logging.getLogger("uvicorn").setLevel(logging.DEBUG)
    logging.getLogger("uvicorn.access").setLevel(logging.DEBUG)
    logging.getLogger("starlette").setLevel(logging.DEBUG)
    logging.getLogger("fastapi").setLevel(logging.DEBUG)
    print("=== Logging configured ===", file=sys.stderr, flush=True)
    yield
    # Shutdown


app = FastAPI(
    title="B2B Platform API",
    version="1.0.0",
    description="API for B2B Platform - supplier moderation and parsing system",
    lifespan=lifespan,
)

# Добавляем логирование при старте
print("=== FastAPI app created ===")
print(f"=== CORS origins: {settings.cors_origins_list} ===")

# Добавляем обработчик ошибок на уровне Starlette
from starlette.requests import Request as StarletteRequest

async def starlette_exception_handler(request: StarletteRequest, exc: Exception):
    """Starlette-level exception handler."""
    import sys
    import traceback
    print(f"=== STARLETTE EXCEPTION: {type(exc).__name__}: {exc} ===", file=sys.stderr, flush=True)
    print(f"=== STARLETTE TRACEBACK:\n{traceback.format_exc()} ===", file=sys.stderr, flush=True)
    
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
        import sys
        import logging
        logger = logging.getLogger(__name__)
        
        # Логируем ВСЕ запросы через logger (должно быть видно в uvicorn логах)
        logger.critical(f"=== MIDDLEWARE: Request to {request.url.path} ===")
        logger.error(f"=== MIDDLEWARE: Request to {request.url.path} ===")
        print(f"=== MIDDLEWARE: Request to {request.url.path} ===", file=sys.stderr, flush=True)
        print(f"=== MIDDLEWARE: Request to {request.url.path} ===", file=sys.stdout, flush=True)
        
        try:
            response = await call_next(request)
            logger.critical(f"=== MIDDLEWARE: Response status: {response.status_code} ===")
            print(f"=== MIDDLEWARE: Response status: {response.status_code} ===", file=sys.stderr, flush=True)
            # Убедимся, что CORS заголовки есть даже при ошибках
            origin = request.headers.get("origin")
            print(f"=== MIDDLEWARE: Origin: {origin} ===", file=sys.stderr, flush=True)
            if origin and origin in settings.cors_origins_list:
                if "Access-Control-Allow-Origin" not in response.headers:
                    response.headers["Access-Control-Allow-Origin"] = origin
                    response.headers["Access-Control-Allow-Credentials"] = "true"
                    response.headers["Access-Control-Allow-Methods"] = "*"
                    response.headers["Access-Control-Allow-Headers"] = "*"
                    print(f"=== MIDDLEWARE: Added CORS headers ===", file=sys.stderr, flush=True)
            print(f"=== MIDDLEWARE: Returning response ===", file=sys.stderr, flush=True)
            return response
        except Exception as exc:
            import traceback
            logger.critical(f"=== MIDDLEWARE EXCEPTION: {type(exc).__name__}: {exc} ===")
            logger.critical(f"=== MIDDLEWARE TRACEBACK:\n{traceback.format_exc()} ===")
            print(f"=== MIDDLEWARE EXCEPTION: {type(exc).__name__}: {exc} ===", file=sys.stderr, flush=True)
            print(f"=== MIDDLEWARE TRACEBACK:\n{traceback.format_exc()} ===", file=sys.stderr, flush=True)
            
            # Обработка исключений на уровне middleware
            logger.error(f"Exception in middleware: {type(exc).__name__}: {exc}", exc_info=True)
            
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
    logger.error(f"Global exception handler called: {type(exc).__name__}: {exc}", exc_info=True)
    
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

