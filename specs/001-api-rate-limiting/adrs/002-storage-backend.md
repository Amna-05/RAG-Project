# ADR-002: Rate Limit Storage Backend

**Status**: Accepted
**Date**: 2026-01-01
**Feature**: 001-api-rate-limiting

## Context

Rate limit counters need persistent storage across requests. For distributed deployments, counters must be shared across server instances.

## Decision

**Use Redis as primary storage with in-memory fallback for development.**

## Rationale

| Factor | Redis | PostgreSQL | In-Memory Only |
|--------|-------|------------|----------------|
| Speed | ✅ <1ms | ⚠️ 5-10ms | ✅ <0.1ms |
| Distributed | ✅ Yes | ✅ Yes | ❌ No |
| Atomic ops | ✅ INCR | ⚠️ Locks needed | ⚠️ Race conditions |
| TTL support | ✅ Native | ❌ Manual cleanup | ✅ Native |
| Complexity | ⚠️ New service | ✅ Existing | ✅ None |

## Consequences

### Positive
- Consistent counters across all API instances
- Atomic INCR prevents race conditions
- Auto-cleanup via TTL (no orphaned data)
- Aligns with constitution recommendation (Section 12)

### Negative
- New infrastructure dependency (Redis)
- Must handle Redis unavailability

### Mitigation
- Fail-open when Redis unavailable (per constitution 6.1)
- In-memory fallback for local development
- Log warnings on Redis failures

## Configuration

```bash
# Production
REDIS_URL=redis://redis:6379/0
RATE_LIMIT_STORAGE=redis

# Development
RATE_LIMIT_STORAGE=memory
```

## References

- [Constitution Section 12](../../.specify/memory/constitution.md) - Redis guidance
- [research.md](../research.md) - Q2
