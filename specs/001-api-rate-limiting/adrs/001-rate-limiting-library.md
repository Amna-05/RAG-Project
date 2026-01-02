# ADR-001: Rate Limiting Library Selection

**Status**: Accepted
**Date**: 2026-01-01
**Feature**: 001-api-rate-limiting

## Context

We need to implement rate limiting for FastAPI endpoints to prevent abuse and control costs. Several options exist for Python/FastAPI rate limiting.

## Decision

**Use SlowAPI** as the rate limiting library.

## Rationale

| Factor | SlowAPI | Custom Middleware | fastapi-limiter |
|--------|---------|-------------------|-----------------|
| FastAPI-native | ✅ Yes | ✅ Yes | ✅ Yes |
| Redis support | ✅ Built-in | ❌ Manual | ✅ Built-in |
| Decorator syntax | ✅ Clean | ❌ N/A | ✅ Clean |
| Battle-tested | ✅ High | ❌ New code | ⚠️ Less mature |
| Maintenance | ✅ Active | ❌ Team burden | ⚠️ Less active |
| Performance overhead | 30-50% lower | Variable | Similar |

## Consequences

### Positive
- Clean decorator-based API: `@limiter.limit("10/minute")`
- Built-in Redis + memory backends
- Standard response headers included
- Well-documented with examples

### Negative
- External dependency to maintain
- Must follow SlowAPI patterns (not fully custom)

### Risks
- Library abandonment → Fork or migrate
- Breaking changes → Pin version in pyproject.toml

## Alternatives Considered

1. **Custom middleware**: More control but higher maintenance burden
2. **fastapi-limiter**: Less mature, fewer features
3. **limits (bare)**: Lower-level, requires more integration

## References

- [SlowAPI GitHub](https://github.com/laurentS/slowapi)
- [research.md](../research.md) - Q1
