# ADR-003: Rate Limiting Algorithm

**Status**: Accepted
**Date**: 2026-01-01
**Feature**: 001-api-rate-limiting

## Context

Rate limiting algorithms vary in complexity and behavior at window boundaries. We need to choose between fixed-window, sliding-window, or token-bucket approaches.

## Decision

**Use fixed-window algorithm for initial implementation.**

## Rationale

| Factor | Fixed-Window | Sliding-Window | Token-Bucket |
|--------|--------------|----------------|--------------|
| Complexity | ✅ Simple | ⚠️ Medium | ❌ Complex |
| Redis calls | ✅ 1 per request | ⚠️ 2-3 per request | ⚠️ 2 per request |
| Boundary behavior | ⚠️ Burst possible | ✅ Smooth | ✅ Smooth |
| Debugging | ✅ Easy | ⚠️ Harder | ❌ Harder |

### Boundary Burst Scenario

With fixed-window (10 req/min):
- User sends 10 requests at 0:59
- Window resets at 1:00
- User sends 10 more at 1:01
- Result: 20 requests in 2 seconds (burst)

**Acceptable because**:
- Target scale is 5-50 users (low abuse risk)
- Spec explicitly defers sliding-window to v2
- Simpler to implement and debug initially

## Consequences

### Positive
- Single Redis INCR per request (fast)
- Easy to understand and explain limits
- SlowAPI default behavior (no custom code)

### Negative
- Users can burst at window boundaries
- May need to upgrade if abuse patterns emerge

### Future Migration Path
```python
# Current (fixed-window)
@limiter.limit("10/minute")

# Future (sliding-window) - SlowAPI supports both
limiter = Limiter(strategy="moving-window")
```

## References

- [Spec assumptions](../spec.md) - "Fixed-window acceptable for initial implementation"
- [research.md](../research.md) - Q3
