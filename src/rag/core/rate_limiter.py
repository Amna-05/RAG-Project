"""
Rate limiting module for the RAG API.
File: src/rag/core/rate_limiter.py

Uses SlowAPI with Redis backend (production) or in-memory (development).
Implements fail-open behavior when Redis is unavailable.
"""
import logging
from typing import Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address as slowapi_get_remote_address

from rag.core.config import get_settings

logger = logging.getLogger(__name__)


def _get_storage_uri() -> Optional[str]:
    """Get the storage URI based on configuration.

    Returns:
        Redis URL for production, None for in-memory storage.
    """
    settings = get_settings()
    if settings.rate_limit_storage == "redis":
        return settings.redis_url
    return None  # Use in-memory storage


def get_remote_address(request: Request) -> str:
    """Extract client IP address for IP-based rate limiting.

    Used for unauthenticated endpoints (auth routes).
    Handles X-Forwarded-For header for proxied requests.

    Args:
        request: FastAPI request object

    Returns:
        Client IP address as string
    """
    # Check for forwarded header (behind proxy/load balancer)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take the first IP in the chain (original client)
        return forwarded.split(",")[0].strip()

    # Fall back to direct client IP
    if request.client and request.client.host:
        return request.client.host

    return "unknown"


def get_user_key(request: Request) -> str:
    """Extract user ID for user-based rate limiting.

    Used for authenticated endpoints (chat, upload).
    Falls back to IP-based limiting if user not available.

    Args:
        request: FastAPI request object

    Returns:
        User-based key (user:{id}) or IP-based key as fallback
    """
    # Check if user is attached to request state (set by auth dependency)
    if hasattr(request.state, "user") and request.state.user:
        user = request.state.user
        if hasattr(user, "id"):
            return f"user:{user.id}"

    # Fallback to IP-based limiting
    logger.warning(
        "User not found in request state, falling back to IP-based limiting",
        extra={"endpoint": request.url.path}
    )
    return get_remote_address(request)


def _create_limiter() -> Limiter:
    """Create and configure the SlowAPI limiter instance.

    Implements fail-open behavior: if Redis is unavailable,
    falls back to in-memory storage with warning log.

    Returns:
        Configured Limiter instance
    """
    settings = get_settings()
    storage_uri = _get_storage_uri()
    actual_storage = settings.rate_limit_storage

    # Try Redis connection if configured
    if storage_uri:
        try:
            # Test Redis connection
            import redis
            r = redis.from_url(storage_uri, socket_connect_timeout=2)
            r.ping()
            logger.info(
                "Redis connection successful for rate limiting",
                extra={"event": "rate_limit_backend_connected", "storage": "redis"}
            )
        except Exception as e:
            # Fail-open: fall back to in-memory storage
            logger.warning(
                "Redis unavailable for rate limiting, falling back to in-memory storage",
                extra={
                    "event": "rate_limit_backend_error",
                    "error": str(e),
                    "fallback": "memory"
                }
            )
            storage_uri = None  # Use in-memory
            actual_storage = "memory (fallback)"

    limiter = Limiter(
        key_func=get_remote_address,  # Default key function
        storage_uri=storage_uri,
        strategy="fixed-window",  # As per ADR-003
        enabled=settings.rate_limit_enabled,
    )

    logger.info(
        "Rate limiter initialized",
        extra={
            "event": "rate_limiter_initialized",
            "storage": actual_storage,
            "enabled": settings.rate_limit_enabled,
        }
    )

    return limiter


# Global limiter instance
limiter = _create_limiter()


async def rate_limit_exceeded_handler(
    request: Request,
    exc: RateLimitExceeded
) -> JSONResponse:
    """Custom exception handler for rate limit exceeded errors.

    Returns HTTP 429 with Retry-After header and structured error response.
    Logs the rate limit event for observability.

    Args:
        request: FastAPI request object
        exc: RateLimitExceeded exception from SlowAPI

    Returns:
        JSONResponse with 429 status and rate limit details
    """
    # Extract retry-after from exception
    retry_after = getattr(exc, "retry_after", 60)

    # Log the rate limit event (structured logging for observability)
    log_data = {
        "event": "rate_limit_blocked",
        "endpoint": request.url.path,
        "method": request.method,
        "ip": get_remote_address(request),
        "retry_after": retry_after,
    }

    # Add user info if available
    if hasattr(request.state, "user") and request.state.user:
        log_data["user_id"] = str(request.state.user.id)

    logger.warning("Rate limit exceeded", extra=log_data)

    # Build response with rate limit headers
    response = JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Please try again later.",
            "retry_after": retry_after,
            "error_code": "RATE_LIMIT_EXCEEDED",
        },
        headers={
            "Retry-After": str(retry_after),
            "X-RateLimit-Limit": str(getattr(exc, "limit", "unknown")),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(retry_after),
        }
    )

    return response


def add_rate_limit_headers(
    response: Response,
    limit: int,
    remaining: int,
    reset: int
) -> Response:
    """Add rate limit status headers to a response.

    Args:
        response: FastAPI response object
        limit: Maximum requests allowed in window
        remaining: Requests remaining in current window
        reset: Seconds until window resets

    Returns:
        Response with rate limit headers added
    """
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(reset)
    return response
