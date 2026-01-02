# Implementation Plan: API Rate Limiting & Abuse Protection

**Branch**: `001-api-rate-limiting` | **Date**: 2026-01-01 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-api-rate-limiting/spec.md`

## Summary

Implement API rate limiting to prevent abuse, protect system stability, and control LLM costs. Uses SlowAPI library with Redis backend for distributed counter storage, falling back to in-memory for development. Applies per-user limits to authenticated endpoints (chat, upload) and per-IP limits to unauthenticated endpoints (auth). Returns HTTP 429 with Retry-After header when limits exceeded.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: FastAPI, SlowAPI, Redis, Pydantic
**Storage**: Redis (rate limit counters) + PostgreSQL (audit logging)
**Testing**: pytest, pytest-asyncio, HTTPX
**Target Platform**: Linux server (Docker), Railway deployment
**Project Type**: Web application (FastAPI backend + Next.js frontend)
**Performance Goals**: 1000 concurrent users, <100ms rate limit check overhead
**Constraints**: <100ms p95 for rate limit middleware, fail-open on Redis failure
**Scale/Scope**: 5-50 users per tenant (constitution target)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Rule | Status | Implementation Notes |
|-------------------|--------|---------------------|
| **6.1** Rate limiting per user/IP | ✅ PASS | SlowAPI with user ID and IP extractors |
| **6.1** HTTP 429 with Retry-After | ✅ PASS | SlowAPI default + custom headers |
| **6.1** Fail-open on backend failure | ✅ PASS | Try/except with warning log |
| **7** Structured logging | ✅ PASS | Log all rate limit events with context |
| **7** Correlation/request ID | ⚠️ TODO | Add request ID to rate limit logs |
| **9** Config via env vars | ✅ PASS | Settings class with env var loading |
| **8.2** Unit + integration tests | ✅ PASS | pytest tests for burst conditions |
| **3** No business logic in routers | ✅ PASS | Rate limit logic in middleware/deps |
| **12** Redis for rate limiting | ✅ PASS | Redis primary, memory fallback |

**Gate Result**: ✅ PASS - All constitution requirements addressed

## Architectural Decisions

See [adrs/](./adrs/) for detailed decision records:
- **ADR-001**: SlowAPI as rate limiting library
- **ADR-002**: Redis primary + in-memory fallback storage
- **ADR-003**: Fixed-window algorithm (sliding-window in v2)
- **ADR-004**: Hybrid pattern (middleware + decorators)

## Project Structure

### Documentation (this feature)

```text
specs/001-api-rate-limiting/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 research findings
├── data-model.md        # Phase 1 data model
├── quickstart.md        # Phase 1 developer quickstart
├── contracts/           # Phase 1 API contracts
│   └── rate-limit-responses.yaml
├── adrs/                # Architectural Decision Records
│   ├── 001-rate-limiting-library.md
│   ├── 002-storage-backend.md
│   ├── 003-algorithm-choice.md
│   └── 004-implementation-pattern.md
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
src/rag/
├── core/
│   ├── config.py          # MODIFY: Add rate limit settings
│   ├── rate_limiter.py    # NEW: SlowAPI setup, key extractors
│   └── database.py        # (existing)
├── api/
│   ├── deps.py            # MODIFY: Add rate limit dependency
│   └── v1/
│       ├── auth.py        # MODIFY: Apply @limiter.limit decorators
│       └── rag.py         # MODIFY: Apply @limiter.limit decorators
├── main.py                # MODIFY: Add limiter middleware
└── models/                # (no changes)

tests/
├── test_rate_limiting.py       # NEW: Unit tests
└── integration/
    └── test_rate_limits.py     # NEW: Integration tests

frontend/rag-frontend/src/
└── lib/api/client.ts      # MODIFY: Handle 429 responses gracefully
```

**Structure Decision**: Backend-only changes with minimal frontend update. Rate limiting is implemented as middleware + dependency injection following existing patterns. No new models required - uses Redis for ephemeral counters.

---

## Implementation Phases

### Phase 1: Core Infrastructure (Blocking)

**Dependencies**: None (first phase)
**Parallel Work**: None

| Task | File | Description | FR |
|------|------|-------------|-----|
| 1.1 | `pyproject.toml` | Add `slowapi` and `redis` dependencies | - |
| 1.2 | `src/rag/core/config.py` | Add rate limit settings section with env var loading | FR-006 |
| 1.3 | `src/rag/core/rate_limiter.py` | Create limiter instance, key extraction functions | FR-003, FR-004 |
| 1.4 | `.env.example` | Add `REDIS_URL` and rate limit config vars | FR-006 |

**Acceptance**: `uv sync` succeeds, settings load without error

---

### Phase 2: Apply Rate Limits to Endpoints (Blocking)

**Dependencies**: Phase 1 complete
**Parallel Work**: 2.1-2.2 can run in parallel with 2.3-2.4

| Task | File | Description | FR |
|------|------|-------------|-----|
| 2.1 | `src/rag/main.py` | Register limiter state and exception handler | FR-001 |
| 2.2 | `src/rag/api/v1/auth.py` | Add `@limiter.limit("5/minute")` to login, register, refresh (IP-based) | FR-004, FR-005 |
| 2.3 | `src/rag/api/v1/rag.py` | Add `@limiter.limit("10/minute")` to chat, `@limiter.limit("2/10minutes")` to upload (user-based) | FR-003, FR-005 |
| 2.4 | `src/rag/api/v1/rag.py` | Add rate limit response headers (X-RateLimit-*) | FR-002, FR-011 |

**Excluded Endpoints** (FR-012, FR-014):
- `/health` - No decorator
- `/docs`, `/redoc`, `/openapi.json` - No decorator
- Any admin endpoints - No decorator

**Acceptance**: 429 returned on 11th chat request within 1 minute

---

### Phase 3: Error Handling & Logging (Blocking)

**Dependencies**: Phase 2 complete
**Parallel Work**: 3.1 and 3.2 can run in parallel

| Task | File | Description | FR |
|------|------|-------------|-----|
| 3.1 | `src/rag/core/rate_limiter.py` | Implement fail-open: wrap Redis calls in try/except, log warning on failure | FR-010 |
| 3.2 | `src/rag/core/rate_limiter.py` | Add structured logging for all rate limit events (allowed, blocked, error) | FR-009 |
| 3.3 | `frontend/.../client.ts` | Handle 429 response: show user-friendly message with retry time | FR-002 |

**Log Format** (FR-009):
```json
{
  "event": "rate_limit_blocked",
  "endpoint": "/api/v1/rag/chat",
  "user_id": "uuid",
  "ip": "192.168.1.1",
  "limit": 10,
  "window": "1 minute",
  "retry_after": 45
}
```

**Acceptance**:
- App runs normally when Redis is stopped
- Log entries visible for blocked requests

---

### Phase 4: Testing (Blocking)

**Dependencies**: Phase 3 complete
**Parallel Work**: 4.1 and 4.2 can run in parallel

| Task | File | Description | FR |
|------|------|-------------|-----|
| 4.1 | `tests/test_rate_limiting.py` | Unit tests: key extraction, config loading, limit calculation | FR-013 |
| 4.2 | `tests/integration/test_rate_limits.py` | Integration tests: burst conditions, 429 response, header validation | FR-001, FR-002 |
| 4.3 | `tests/integration/test_rate_limits.py` | Fail-open test: simulate Redis failure, verify requests succeed | FR-010 |

**Test Scenarios**:
1. 10 requests → all pass, 11th → 429
2. Wait for window reset → request passes
3. Stop Redis → requests pass with warning log
4. Concurrent requests → all count correctly

**Acceptance**: All tests pass, coverage >80% for rate_limiter.py

---

## Dependency Graph

```
Phase 1: Core Infrastructure
    │
    ▼
Phase 2: Apply Rate Limits ──┬── 2.1-2.2 (main.py, auth.py)
    │                        └── 2.3-2.4 (rag.py) [PARALLEL]
    ▼
Phase 3: Error Handling ─────┬── 3.1 (fail-open)
    │                        ├── 3.2 (logging) [PARALLEL]
    │                        └── 3.3 (frontend)
    ▼
Phase 4: Testing ────────────┬── 4.1 (unit) [PARALLEL]
                             └── 4.2-4.3 (integration)
```

---

## Requirement Traceability Matrix

| FR | Description | Phase | Task(s) |
|----|-------------|-------|---------|
| FR-001 | Reject with 429 | 2 | 2.1 |
| FR-002 | Retry-After header | 2, 3 | 2.4, 3.3 |
| FR-003 | Per-user tracking | 1, 2 | 1.3, 2.3 |
| FR-004 | Per-IP tracking | 1, 2 | 1.3, 2.2 |
| FR-005 | Apply to chat/upload/auth | 2 | 2.2, 2.3 |
| FR-006 | Configurable via env | 1 | 1.2, 1.4 |
| FR-007 | Fixed-window algorithm | 1 | 1.3 (SlowAPI default) |
| FR-008 | Intercept before handler | 2 | 2.1 (decorator runs first) |
| FR-009 | Log all events | 3 | 3.2 |
| FR-010 | Fail-open | 3 | 3.1 |
| FR-011 | Status headers | 2 | 2.4 |
| FR-012 | Exclude health/admin | 2 | (no decorator = excluded) |
| FR-013 | Handle concurrency | 4 | 4.1 (Redis atomic INCR) |
| FR-014 | Exclude docs endpoints | 2 | (no decorator = excluded) |

---

## Complexity Tracking

> No constitution violations requiring justification.

| Aspect | Complexity Level | Justification |
|--------|------------------|---------------|
| New dependency (SlowAPI) | Low | Battle-tested library, FastAPI-native |
| Redis requirement | Medium | Optional for dev (memory fallback) |
| Middleware addition | Low | Follows existing middleware pattern |
