"""
Main FastAPI application.
File: src/rag/main.py or src/main.py

PURPOSE:
- Entry point for the entire application
- Configures FastAPI app with all routes
- Sets up middleware, CORS, startup/shutdown events
- This is what uvicorn runs

HOW TO RUN:
    uvicorn rag.main:app --reload --host 0.0.0.0 --port 8000
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
import time

from rag.core.config import get_settings
from rag.core.database import init_db, close_db
from rag.core.rate_limiter import limiter, rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from rag.api.v1 import auth

# Import other routers as we create them
#from rag.api.v1 import documents, queries
# Add this import at the top:
from rag.api.v1 import rag as rag_router


settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format=settings.log_format
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events.
    
    STARTUP:
    - Initialize database connection
    - Create tables if not exist
    - Run any necessary migrations
    
    SHUTDOWN:
    - Close database connections
    - Cleanup resources
    """
    # Startup
    logger.info("🚀 Starting up RAG application...")
    
    try:
        # Initialize database
        await init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise
    
    # Add any other startup tasks here
    # - Initialize Redis connection
    # - Load ML models into memory
    # - etc.
    
    logger.info("✅ Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down application...")
    
    try:
        await close_db()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")
    
    logger.info("✅ Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Multi-user RAG system with authentication and document Q&A",
    lifespan=lifespan,
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
    openapi_url="/openapi.json",
)

# ============ Rate Limiting Setup ============
# Register limiter state on app (required by SlowAPI)
app.state.limiter = limiter

# Register rate limit exceeded exception handler
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)


# ============ CORS Middleware ============
# IMPORTANT: For cookie-based auth, credentials must be True
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # Frontend URLs
    allow_credentials=True,  # MUST be True for cookies to work
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)

# ============ Request Logging Middleware ============
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log all incoming requests with timing.
    
    LOGS:
    - Method, path, query params
    - Processing time
    - Status code
    """
    start_time = time.time()
    
    # Log request
    logger.info(
        f"→ {request.method} {request.url.path} "
        f"from {request.client.host if request.client else 'unknown'}"
    )
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log response
    logger.info(
        f"← {request.method} {request.url.path} "
        f"completed in {process_time:.3f}s with status {response.status_code}"
    )
    
    # Add custom header with processing time
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# ============ Exception Handlers ============

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle Pydantic validation errors.
    
    RETURNS: Clean error message instead of raw validation error
    """
    errors = exc.errors()
    error_messages = []
    
    for error in errors:
        field = " -> ".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        error_messages.append(f"{field}: {message}")
    
    logger.warning(f"Validation error on {request.url.path}: {error_messages}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": error_messages
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch-all exception handler.
    
    LOGS: Full error for debugging
    RETURNS: Generic error message (don't expose internals)
    """
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}: {exc}",
        exc_info=True
    )
    
    # In production, don't expose internal errors
    if settings.debug:
        detail = str(exc)
    else:
        detail = "An internal error occurred. Please try again later."
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": detail}
    )


# ============ Root Endpoints ============

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - API health check.
    
    RESPONSE:
    {
        "message": "RAG API is running",
        "version": "1.0.0",
        "docs": "/docs"
    }
    """
    return {
        "message": "RAG API is running",
        "version": settings.app_version,
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["Root"])
async def health_check():
    """
    Health check endpoint.
    
    USE CASE:
    - Docker health checks
    - Load balancer health checks
    - Monitoring systems
    
    RESPONSE:
    {
        "status": "healthy",
        "timestamp": "2025-10-18T10:30:00"
    }
    """
    from datetime import datetime
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.app_name,
        "version": settings.app_version
    }


# ============ Include API Routers ============

# Authentication routes
app.include_router(
    auth.router,
    prefix=settings.api_prefix,  # /api/v1
    tags=["Authentication"]
)

app.include_router(rag_router.router, 
                   prefix=settings.api_prefix)


#Document routes (create later)
#app.include_router(
#    documents.router,
#    prefix=settings.api_prefix,
#    tags=["Documents"]
#)
#
##Query routes (create later)
#app.include_router(
#    queries.router,
#    prefix=settings.api_prefix,
#    tags=["Queries"]
#)


# ============ Development Info ============

if __name__ == "__main__":
    import uvicorn
    
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                   RAG API Server                         ║
    ╚══════════════════════════════════════════════════════════╝
    
    🚀 Starting development server...
    📖 API Documentation: http://localhost:8000/docs
    📘 Alternative Docs: http://localhost:8000/redoc
    
    Environment: {'Development' if settings.debug else 'Production'}
    Database: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'configured'}
    
    Press CTRL+C to stop
    """)
    
    uvicorn.run(
        "rag.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,  # Auto-reload in debug mode
        log_level=settings.log_level.lower()
    )