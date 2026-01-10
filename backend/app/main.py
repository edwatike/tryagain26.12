"""FastAPI application entry point."""
import sys
import os

# CRITICAL: Ensure backend directory is in Python path for uvicorn reload mode
# When uvicorn runs with reload=True and import string, it spawns a new process
# that needs to have the correct Python path to import modules
# This is a safety measure in case PYTHONPATH is not set correctly
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

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
    checko,
    comet,
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

# CRITICAL: Verify app is created correctly
import logging
_app_verify_logger = logging.getLogger(__name__)
try:
    _app_verify_logger.info("=== FastAPI app instance created ===")
    _app_verify_logger.info(f"=== App instance ID: {id(app)} ===")
except Exception:
    pass  # Safe logging

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
        
        # DEBUG: Log all requests to /parsing/runs/*/logs
        if "/parsing/runs" in str(request.url.path) and "/logs" in str(request.url.path):
            logger.info(f"[DEBUG MIDDLEWARE] Request to: {request.method} {request.url.path}")
            logger.info(f"[DEBUG MIDDLEWARE] Request scope path: {request.scope.get('path', 'N/A')}")
            logger.info(f"[DEBUG MIDDLEWARE] Request scope method: {request.scope.get('method', 'N/A')}")
        
        # DEBUG: Log INN extraction requests
        if "/inn-extraction" in str(request.url.path):
            logger.info(f"[DEBUG MIDDLEWARE] INN extraction request: {request.method} {request.url.path}")
            logger.info(f"[DEBUG MIDDLEWARE] Available routes: {[r.path for r in app.routes if hasattr(r, 'path')][:10]}")
        
        try:
            response = await call_next(request)
            
            # DEBUG: Log response for /parsing/runs/*/logs
            if "/parsing/runs" in str(request.url.path) and "/logs" in str(request.url.path):
                logger.info(f"[DEBUG MIDDLEWARE] Response status: {response.status_code}")
                logger.info(f"[DEBUG MIDDLEWARE] Response headers: {dict(response.headers)}")
            
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

@app.get("/debug/routes")
async def debug_routes():
    """Debug endpoint to check route registration."""
    from fastapi.routing import APIRoute
    routes_info = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            if '/parsing/runs' in route.path and 'logs' in route.path:
                routes_info.append({
                    "path": route.path,
                    "methods": list(route.methods),
                    "name": getattr(route, 'name', None),
                    "endpoint": route.endpoint.__name__ if hasattr(route, 'endpoint') else None
                })
    return {"logs_routes": routes_info, "total_routes": len(app.routes)}

@app.get("/debug/all-routes")
async def debug_all_routes():
    """Debug endpoint to check all registered routes."""
    from fastapi.routing import APIRoute
    routes_info = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            routes_info.append({
                "path": route.path,
                "methods": list(route.methods),
                "name": getattr(route, 'name', None),
                "endpoint": route.endpoint.__name__ if hasattr(route, 'endpoint') else None
            })
    # Filter INN extraction routes
    inn_routes = [r for r in routes_info if 'inn' in r['path'].lower()]
    return {
        "total_routes": len(routes_info),
        "inn_routes": inn_routes,
        "all_routes": routes_info
    }


# Include routers
import logging
_router_logger = logging.getLogger(__name__)

try:
    _router_logger.info("=== Registering routers ===")
    app.include_router(health.router, tags=["Health"])
    app.include_router(moderator_suppliers.router, prefix="/moderator", tags=["Suppliers"])
    app.include_router(keywords.router, prefix="/keywords", tags=["Keywords"])
    app.include_router(blacklist.router, prefix="/moderator", tags=["Blacklist"])
    app.include_router(parsing_runs.router, prefix="/parsing", tags=["Parsing Runs"])
    app.include_router(parsing.router, prefix="/parsing", tags=["Parsing"])
    app.include_router(domains_queue.router, prefix="/domains", tags=["Domains Queue"])
    app.include_router(attachments.router, prefix="/attachments", tags=["Attachments"])
    app.include_router(checko.router, prefix="/moderator", tags=["Checko"])
    _router_logger.info("=== Registering comet router ===")
    app.include_router(comet.router, prefix="/comet", tags=["Comet Extraction"])
    _router_logger.info("=== All routers registered successfully ===")
    # Log registered routes for debugging
    from fastapi.routing import APIRoute
    comet_routes = [r for r in app.routes if isinstance(r, APIRoute) and '/comet' in r.path]
    _router_logger.info(f"=== Comet routes: {[r.path for r in comet_routes]} ===")
    _router_logger.info(f"=== Total routes after registration: {len([r for r in app.routes if isinstance(r, APIRoute)])} ===")
    _router_logger.info(f"=== App instance ID after router registration: {id(app)} ===")
except Exception as e:
    _router_logger.error(f"=== ERROR registering routers: {e} ===", exc_info=True)
    raise

# CRITICAL: Final verification after all routers are registered
try:
    from fastapi.routing import APIRoute
    final_routes = [r for r in app.routes if isinstance(r, APIRoute)]
    final_inn_routes = [r for r in final_routes if '/inn-extraction' in r.path]
    _router_logger.info(f"=== FINAL VERIFICATION: Total routes: {len(final_routes)}, INN routes: {len(final_inn_routes)} ===")
    if not final_inn_routes:
        _router_logger.error("=== CRITICAL: INN extraction routes NOT found after registration! ===")
    else:
        _router_logger.info(f"=== SUCCESS: INN extraction routes found: {[r.path for r in final_inn_routes]} ===")
except Exception as e:
    _router_logger.error(f"=== ERROR in final verification: {e} ===", exc_info=True)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

