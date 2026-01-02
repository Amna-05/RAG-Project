# ADR-004: Implementation Pattern (Middleware vs Dependency)

**Status**: Accepted
**Date**: 2026-01-01
**Feature**: 001-api-rate-limiting

## Context

Rate limiting can be implemented as:
1. **Middleware**: Global, runs on every request
2. **Dependency**: Per-endpoint, explicit in function signature
3. **Hybrid**: Combine both approaches

## Decision

**Use hybrid approach: Middleware for IP-based + Decorators for user-based limits.**

## Rationale

| Approach | IP-Based (Auth) | User-Based (RAG) | Exclusions |
|----------|-----------------|------------------|------------|
| Middleware only | ✅ Works | ❌ No user context | ⚠️ Path matching |
| Dependency only | ⚠️ Boilerplate | ✅ Has user | ✅ Just don't add |
| **Hybrid** | ✅ Middleware | ✅ Decorators | ✅ Best of both |

### Why Hybrid?

1. **Auth endpoints** (login, register): Need IP-based limiting before authentication
2. **RAG endpoints** (chat, upload): Need user-based limiting after authentication
3. **Exclusions** (health, docs): Don't apply decorators

## Implementation

```python
# main.py - Global exception handler (not middleware filter)
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# auth.py - IP-based via decorator
@router.post("/login")
@limiter.limit("5/minute", key_func=get_remote_address)
async def login(request: Request): ...

# rag.py - User-based via decorator
@router.post("/chat")
@limiter.limit("10/minute", key_func=get_user_key)
async def chat(request: Request, user: User = Depends(get_current_user)): ...

# Excluded - No decorator
@router.get("/health")
async def health(): ...  # No @limiter.limit = no rate limiting
```

## Consequences

### Positive
- Clear separation: IP vs user limits
- Explicit per-endpoint control
- Easy to exclude endpoints (just don't decorate)
- Follows existing project patterns

### Negative
- Must remember to add decorators
- Two key extraction functions to maintain

### Key Functions

```python
def get_remote_address(request: Request) -> str:
    """For unauthenticated endpoints (auth)."""
    return request.client.host or "unknown"

def get_user_key(request: Request) -> str:
    """For authenticated endpoints (rag)."""
    if hasattr(request.state, "user"):
        return f"user:{request.state.user.id}"
    return get_remote_address(request)
```

## References

- [research.md](../research.md) - Q4
- [Constitution Section 3](../../.specify/memory/constitution.md) - No business logic in routers
