"""
NetGuard Pro - Main Application Entry Point

FastAPI application initialization with:
- Middleware configuration
- Router registration
- Event handlers (startup/shutdown)
- Exception handlers
- OpenAPI documentation
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.logging_config import setup_logging, audit_logger
from app.db.session import init_db_engine, check_connection, create_tables
from app.api.v1.router import api_router

# Configure logging
setup_logging(
    log_level=settings.logging.level,
    log_format=settings.logging.format,
    log_output=settings.logging.output,
    log_file_path=settings.logging.file_path,
    include_timestamp=settings.logging.include_timestamp,
    include_caller=settings.logging.include_caller,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager - handles startup and shutdown."""
    # Startup
    logger.info("Starting NetGuard Pro...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Version: {settings.version}")
    
    # Initialize database
    try:
        init_db_engine()
        db_ok = await check_connection()
        if db_ok:
            logger.info("Database connection established")
            if settings.is_development:
                await create_tables()
                logger.info("Database tables created/verified")
        else:
            logger.error("Database connection failed")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
    
    # Log startup complete
    audit_logger.security_event(
        event_type="system_startup",
        severity="info",
        source_ip="localhost",
        details={"version": settings.version},
    )
    logger.info("NetGuard Pro started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down NetGuard Pro...")
    audit_logger.security_event(
        event_type="system_shutdown",
        severity="info",
        source_ip="localhost",
    )
    logger.info("NetGuard Pro shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="""
## NetGuard Pro - Universal Internet Gateway

**NetGuard Pro** is a comprehensive server solution for controlling and managing 
internet access in corporate and educational networks.

### Features

- **Firewall & Security**: Next-generation firewall with flexible rules
- **Proxy Services**: HTTP/HTTPS/SOCKS proxy with SSL inspection
- **User Management**: AD integration, multiple authentication methods
- **Billing**: Flexible tariff plans, traffic accounting
- **Monitoring**: Real-time monitoring and detailed reporting
- **QoS**: Traffic shaping and prioritization
    """,
    version=settings.version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.server.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "validation_error", "detail": exc.errors()},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "internal_error", "message": "An internal error occurred"},
    )


# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Health check endpoint."""
    db_status = "unknown"
    redis_status = "unknown"
    
    try:
        db_ok = await check_connection()
        db_status = "healthy" if db_ok else "unhealthy"
    except Exception:
        db_status = "unreachable"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "version": settings.version,
        "environment": settings.environment,
        "services": {"database": db_status, "redis": redis_status},
    }


@app.get("/", tags=["Root"])
async def root() -> dict:
    """Root endpoint with basic info."""
    return {
        "name": settings.app_name,
        "version": settings.version,
        "description": "Universal Internet Gateway, Proxy Server, Firewall and Billing System",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.reload,
        workers=settings.server.workers if not settings.server.reload else 1,
    )
