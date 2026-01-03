"""
Structured logging configuration using structlog.
File: src/rag/core/logging.py

Features:
- JSON structured logging
- Request correlation IDs
- Sensitive data filtering
- Performance timing
"""
import logging
import logging.config
import time
from typing import Any, Dict
from datetime import datetime

try:
    import structlog
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False

from rag.core.config import get_settings


# Sensitive fields to filter from logs
SENSITIVE_FIELDS = {
    'password', 'token', 'api_key', 'secret', 'authorization',
    'access_token', 'refresh_token', 'credit_card', 'ssn'
}


def filter_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Filter sensitive information from log data."""
    if not isinstance(data, dict):
        return data

    filtered = {}
    for key, value in data.items():
        # Check if key contains sensitive field names
        if any(sensitive in key.lower() for sensitive in SENSITIVE_FIELDS):
            filtered[key] = "[REDACTED]"
        elif isinstance(value, dict):
            filtered[key] = filter_sensitive_data(value)
        else:
            filtered[key] = value

    return filtered


def configure_logging():
    """Configure Python logging and structlog."""
    settings = get_settings()

    if not STRUCTLOG_AVAILABLE:
        # Fallback to standard logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            # Add correlation ID if present
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure Python logging to use structlog
    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.processors.JSONRenderer(),
            },
            "plain": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.dev.ConsoleRenderer(),
            },
        },
        "handlers": {
            "default": {
                "level": "DEBUG" if settings.debug else "INFO",
                "class": "logging.StreamHandler",
                "formatter": "json",
            },
            "console": {
                "level": "DEBUG" if settings.debug else "INFO",
                "class": "logging.StreamHandler",
                "formatter": "plain" if settings.debug else "json",
            },
        },
        "loggers": {
            "": {
                "handlers": ["default"],
                "level": "DEBUG" if settings.debug else "INFO",
                "propagate": True,
            },
            "rag": {
                "handlers": ["console"],
                "level": "DEBUG" if settings.debug else "INFO",
                "propagate": False,
            },
        },
    })


def get_logger(name: str):
    """Get a structured logger instance."""
    if STRUCTLOG_AVAILABLE:
        return structlog.get_logger(name)
    else:
        return logging.getLogger(name)


class LoggingMiddleware:
    """ASGI middleware for request/response logging."""

    def __init__(self, app):
        self.app = app
        self.logger = get_logger("rag.middleware.logging")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract request info
        request_id = self._get_request_id(scope)
        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "/")
        query_string = scope.get("query_string", b"").decode()

        # Start timing
        start_time = time.time()

        # Log request
        self.logger.info(
            "request_started",
            request_id=request_id,
            method=method,
            path=path,
            query_string=query_string,
            client=self._get_client(scope),
        )

        # Track response
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_code = message["status"]

                # Log response
                duration_ms = (time.time() - start_time) * 1000
                self.logger.info(
                    "request_completed",
                    request_id=request_id,
                    method=method,
                    path=path,
                    status_code=status_code,
                    duration_ms=f"{duration_ms:.2f}",
                )

            await send(message)

        await self.app(scope, receive, send_wrapper)

    @staticmethod
    def _get_request_id(scope) -> str:
        """Extract or generate request ID from headers."""
        headers = scope.get("headers", [])
        for header_name, header_value in headers:
            if header_name.lower() == b"x-request-id":
                return header_value.decode()

        # Generate new request ID if not present
        from uuid import uuid4
        return str(uuid4())

    @staticmethod
    def _get_client(scope) -> str:
        """Extract client IP from scope."""
        client = scope.get("client")
        if client:
            return client[0]
        return "unknown"


# Module-level logger
logger = get_logger(__name__)


# Initialize logging on import
try:
    configure_logging()
except Exception as e:
    print(f"Failed to configure structured logging: {e}")
    logging.basicConfig(level=logging.INFO)
