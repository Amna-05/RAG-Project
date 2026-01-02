# Research: API Rate Limiting & Abuse Protection

**Feature**: 001-api-rate-limiting
**Date**: 2026-01-01
**Status**: Complete

## Research Questions

### Q1: Which rate limiting library for FastAPI?

**Decision**: SlowAPI

**Rationale**:
- Purpose-built for FastAPI/Starlette (adapted from flask-limiter)
- Decorator syntax integrates cleanly: `@limiter.limit("30/minute")`
- Supports Redis + in-memory backends
- 30-50% lower overhead than custom middleware
- Production-proven in high-traffic APIs
- Active maintenance and community support

**Alternatives Considered**:

| Library | Rejected Because |
|---------|------------------|
| Custom middleware | More code to maintain, less battle-tested |
| fastapi-limiter | Less mature, fewer features |
| limits (bare) | Lower-level, requires more integration work |

**Sources**:
- [SlowAPI GitHub](https://github.com/laurentS/slowapi)
- [FastAPI Rate Limiting Best Practices](https://dev.turmansolutions.ai/2025/07/11/rate-limiting-strategies-in-fastapi-protecting-your-api-from-abuse/)
- [API Rate Limiting at Scale](https://python.plainenglish.io/api-rate-limiting-and-abuse-prevention-at-scale-best-practices-with-fastapi-b5d31d690208)

---

### Q2: Storage backend for rate limit counters?

**Decision**: Redis (primary) + In-memory (fallback/dev)

**Rationale**:
- Redis enables consistent limits across multiple server instances
- Atomic counter operations prevent race conditions
- Constitution already recommends Redis for rate limiting (Section 12)
- In-memory fallback for local development
- Fail-open behavior when Redis unavailable (per constitution)

**Configuration**:
```
Production: Redis (shared counters across instances)
Development: In-memory dictionary (simple, no dependencies)
Fallback: Fail-open + log warning
```

**Sources**:
- [Implementing Rate Limiter with FastAPI and Redis](https://bryananthonio.com/blog/implementing-rate-limiter-fastapi-redis/)
- [Python Rate Limiting for APIs](https://www.techbuddies.io/2025/12/13/python-rate-limiting-for-apis-implementing-robust-throttling-in-fastapi/)

---

### Q3: Fixed-window vs sliding-window algorithm?

**Decision**: Fixed-window (initial), sliding-window optional (v2)

**Rationale**:
- Fixed-window is simpler to implement and debug
- Acceptable burstiness for initial launch (5-50 users per spec)
- Sliding-window adds complexity without proportional benefit at this scale
- Constitution accepts basic fixed-window limits (Section 6.1)
- Can upgrade to sliding-window if abuse patterns emerge

**Trade-offs**:

| Algorithm | Pros | Cons |
|-----------|------|------|
| Fixed-window | Simple, low overhead, easy to explain | Burst at window boundaries |
| Sliding-window | Smooth traffic, no boundary bursts | More complex, higher Redis calls |

---

### Q4: Implementation pattern (middleware vs dependency)?

**Decision**: Hybrid approach

**Rationale**:
- **Middleware**: Global IP-based limits for unauthenticated endpoints
- **Dependency**: User-specific limits for authenticated endpoints
- Aligns with existing project patterns (deps.py dependencies, main.py middleware)
- Middleware intercepts before business logic (FR-008)

**Architecture**:
```python
# Middleware layer (main.py)
@app.middleware("http")
async def rate_limit_middleware(request, call_next):
    # IP-based limits for /auth/* endpoints
    # Skip for docs, health, CORS preflight

# Dependency layer (deps.py)
async def check_rate_limit(user: User = Depends(get_current_user)):
    # User-specific limits for /rag/* endpoints
    # Chat: 10/minute, Upload: 2/10-minutes
```

---

### Q5: How to handle rate limit state persistence?

**Decision**: Redis primary + database audit logging

**Rationale**:
- Redis for real-time counter state (fast, ephemeral)
- Database for audit logging of rate limit events (persistent, queryable)
- No need for dedicated RateLimitLog table initially
- Use structured logging with filters for operational queries

---

### Q6: Response headers for rate limit status?

**Decision**: Include standard headers

**Headers to implement**:
```
X-RateLimit-Limit: 10        # Max requests in window
X-RateLimit-Remaining: 7     # Requests left in window
X-RateLimit-Reset: 1704110400  # Unix timestamp when window resets
Retry-After: 45              # Seconds until retry (on 429 only)
```

**Rationale**:
- Industry standard (GitHub, Twitter, Stripe use these)
- Enables frontend to show remaining allowance
- Helps API consumers build retry logic

---

### Q7: Which endpoints to rate limit?

**Decision**: Three categories with different limits

| Category | Endpoints | Default Limit | Scope |
|----------|-----------|---------------|-------|
| Chat/LLM | `/rag/chat` | 10/minute | Per user |
| Upload | `/rag/upload` | 2/10-minutes | Per user |
| Auth | `/auth/login`, `/auth/register`, `/auth/refresh` | 5/minute | Per IP |

**Excluded**:
- `/health` - System monitoring
- `/docs`, `/redoc`, `/openapi.json` - Documentation
- Admin endpoints (future) - Superuser bypass

---

## Integration Points

### Files to Modify

| File | Changes |
|------|---------|
| `src/rag/core/config.py` | Add rate limit settings section |
| `src/rag/main.py` | Add SlowAPI limiter, middleware |
| `src/rag/api/deps.py` | Add rate limit dependency |
| `src/rag/api/v1/rag.py` | Apply `@limiter.limit()` decorators |
| `src/rag/api/v1/auth.py` | Apply IP-based limits |
| `pyproject.toml` | Add `slowapi`, `redis` dependencies |
| `.env.example` | Add rate limit config variables |

### New Files to Create

| File | Purpose |
|------|---------|
| `src/rag/core/rate_limiter.py` | SlowAPI setup, key functions |
| `tests/test_rate_limiting.py` | Unit tests for rate limiting |
| `tests/integration/test_rate_limits.py` | Integration tests under burst |

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Redis unavailable in production | Fail-open with warning logs |
| Clock skew across instances | Use Redis server time, not local |
| Race conditions on concurrent requests | Redis atomic INCR operations |
| False positives (legitimate bursts) | Generous initial limits, monitoring |

---

## Dependencies to Add

```toml
# pyproject.toml
slowapi = "^0.1.9"
redis = "^5.0.0"
```
