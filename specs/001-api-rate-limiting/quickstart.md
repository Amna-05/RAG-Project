# Quickstart: API Rate Limiting Implementation

**Feature**: 001-api-rate-limiting
**Time Estimate**: ~4 hours

## Prerequisites

- Python 3.12+ environment
- Redis installed locally (or Docker)
- Existing RAG project cloned and working

## Quick Setup

### 1. Install Dependencies

```bash
# Add to pyproject.toml
uv add slowapi redis
```

### 2. Start Redis (Development)

```bash
# Using Docker
docker run -d --name redis-dev -p 6379:6379 redis:alpine

# Or install locally (Windows)
# Download from https://github.com/microsoftarchive/redis/releases
```

### 3. Add Environment Variables

```bash
# .env
REDIS_URL=redis://localhost:6379/0
RATE_LIMIT_ENABLED=true

# Optional: Override defaults
RATE_LIMIT_CHAT_REQUESTS=10
RATE_LIMIT_CHAT_WINDOW=60
RATE_LIMIT_UPLOAD_REQUESTS=2
RATE_LIMIT_UPLOAD_WINDOW=600
RATE_LIMIT_AUTH_REQUESTS=5
RATE_LIMIT_AUTH_WINDOW=60
```

### 4. Create Rate Limiter Module

Create `src/rag/core/rate_limiter.py`:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request
from starlette.responses import JSONResponse

from rag.core.config import get_settings

settings = get_settings()

def get_user_identifier(request: Request) -> str:
    """Extract user ID from JWT token or fall back to IP."""
    # Try to get user from request state (set by auth middleware)
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.id}"
    return f"ip:{get_remote_address(request)}"

# Initialize limiter
limiter = Limiter(
    key_func=get_user_identifier,
    storage_uri=settings.redis_url if settings.rate_limit_enabled else None,
    strategy="fixed-window",
)

def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Custom 429 response with Retry-After header."""
    return JSONResponse(
        status_code=429,
        content={
            "detail": f"Rate limit exceeded. {exc.detail}",
            "retry_after": int(exc.retry_after) if exc.retry_after else 60,
        },
        headers={
            "Retry-After": str(int(exc.retry_after) if exc.retry_after else 60),
            "X-RateLimit-Limit": str(exc.limit),
        },
    )
```

### 5. Register in main.py

```python
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from rag.core.rate_limiter import limiter, rate_limit_exceeded_handler

# Add to app setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
```

### 6. Apply to Endpoints

```python
# In src/rag/api/v1/rag.py
from rag.core.rate_limiter import limiter

@router.post("/chat")
@limiter.limit("10/minute")
async def chat(request: Request, ...):
    ...

@router.post("/upload")
@limiter.limit("2/10minutes")
async def upload(request: Request, ...):
    ...
```

```python
# In src/rag/api/v1/auth.py
from rag.core.rate_limiter import limiter

@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, ...):
    ...
```

## Testing

### Manual Test

```bash
# Send 11 requests rapidly (should get 429 on 11th)
for i in {1..11}; do
  curl -X POST http://localhost:8000/api/v1/rag/chat \
    -H "Cookie: access_token=YOUR_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"message": "test"}'
  echo ""
done
```

### Unit Test

```python
# tests/test_rate_limiting.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_rate_limit_exceeded():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Send requests up to limit
        for _ in range(10):
            response = await client.post("/api/v1/rag/chat", json={"message": "test"})
            assert response.status_code == 200

        # 11th request should be blocked
        response = await client.post("/api/v1/rag/chat", json={"message": "test"})
        assert response.status_code == 429
        assert "Retry-After" in response.headers
```

## Verification Checklist

- [ ] Redis is running and accessible
- [ ] Rate limit headers appear in responses
- [ ] 429 returned when limit exceeded
- [ ] Retry-After header is present in 429 response
- [ ] Limits reset after window expires
- [ ] App works when Redis is unavailable (fail-open)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Redis connection refused | Start Redis: `docker start redis-dev` |
| Limits not applied | Check `RATE_LIMIT_ENABLED=true` in .env |
| Always getting 429 | Check if Redis counter is stuck (restart Redis) |
| No headers in response | Ensure `@limiter.limit()` decorator is applied |

## Files Changed

| File | Change Type |
|------|-------------|
| `pyproject.toml` | Add slowapi, redis |
| `src/rag/core/config.py` | Add rate limit settings |
| `src/rag/core/rate_limiter.py` | New file |
| `src/rag/main.py` | Register limiter |
| `src/rag/api/v1/rag.py` | Add decorators |
| `src/rag/api/v1/auth.py` | Add decorators |
| `.env.example` | Add REDIS_URL |
