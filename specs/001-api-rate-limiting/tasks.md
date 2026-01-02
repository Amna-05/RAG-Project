# Tasks: API Rate Limiting & Abuse Protection

**Input**: Design documents from `/specs/001-api-rate-limiting/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Included (SC-008 in spec requires integration tests for burst conditions)

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US5)
- Paths relative to repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add dependencies and create core rate limiting module

- [x] T001 Add `slowapi>=0.1.9` and `redis>=5.0.0` to pyproject.toml
- [x] T002 Run `uv sync` to install new dependencies
- [x] T003 [P] Add rate limit environment variables to .env.example (REDIS_URL, RATE_LIMIT_*)
- [x] T004 [P] Add rate limit settings section to src/rag/core/config.py with Pydantic Fields

**Acceptance**: `uv sync` succeeds, `from rag.core.config import get_settings; s = get_settings()` loads rate limit settings

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core rate limiting infrastructure that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Create src/rag/core/rate_limiter.py with SlowAPI limiter instance and storage configuration
- [x] T006 Add `get_remote_address()` key function for IP-based limiting in src/rag/core/rate_limiter.py
- [x] T007 Add `get_user_key()` key function for user-based limiting in src/rag/core/rate_limiter.py
- [x] T008 Add custom RateLimitExceeded exception handler with 429 response in src/rag/core/rate_limiter.py
- [x] T009 Register limiter state on FastAPI app in src/rag/main.py
- [x] T010 Add RateLimitExceeded exception handler to app in src/rag/main.py

**Acceptance**: App starts without error, limiter is accessible via `request.app.state.limiter`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Chat Rate Limiting (Priority: P1) 🎯 MVP

**Goal**: Authenticated users are limited to 10 chat requests per minute with clear feedback

**Independent Test**: Send 11 POST /api/v1/rag/chat requests in 1 minute → 11th returns 429 with Retry-After

### Tests for User Story 1

- [ ] T011 [P] [US1] Create tests/integration/test_rate_limits.py with test fixture for authenticated user
- [ ] T012 [P] [US1] Write test_chat_rate_limit_enforced() - 10 pass, 11th returns 429 in tests/integration/test_rate_limits.py
- [ ] T013 [P] [US1] Write test_chat_rate_limit_resets() - after window, requests succeed in tests/integration/test_rate_limits.py
- [ ] T014 [P] [US1] Write test_chat_response_has_rate_limit_headers() in tests/integration/test_rate_limits.py

### Implementation for User Story 1

- [x] T015 [US1] Import limiter and get_user_key in src/rag/api/v1/rag.py
- [x] T016 [US1] Add `@limiter.limit("10/minute", key_func=get_user_key)` decorator to POST /chat endpoint in src/rag/api/v1/rag.py
- [x] T017 [US1] Add X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset headers to chat response in src/rag/api/v1/rag.py
- [ ] T018 [US1] Run tests for US1: `pytest tests/integration/test_rate_limits.py -k chat`

**Checkpoint**: Chat rate limiting works independently - MVP complete!

---

## Phase 4: User Story 2 - Upload Rate Limiting (Priority: P1)

**Goal**: Authenticated users are limited to 2 document uploads per 10 minutes

**Independent Test**: Upload 3 documents in 10 minutes → 3rd returns 429

### Tests for User Story 2

- [ ] T019 [P] [US2] Write test_upload_rate_limit_enforced() - 2 pass, 3rd returns 429 in tests/integration/test_rate_limits.py
- [ ] T020 [P] [US2] Write test_upload_rate_limit_resets() - after 10min window, uploads succeed in tests/integration/test_rate_limits.py

### Implementation for User Story 2

- [x] T021 [US2] Add `@limiter.limit("2/10minutes", key_func=get_user_key)` decorator to POST /upload endpoint in src/rag/api/v1/rag.py
- [x] T022 [US2] Add rate limit headers to upload response in src/rag/api/v1/rag.py
- [ ] T023 [US2] Run tests for US2: `pytest tests/integration/test_rate_limits.py -k upload`

**Checkpoint**: Upload rate limiting works independently

---

## Phase 5: User Story 3 - Auth Endpoint Protection (Priority: P1)

**Goal**: Unauthenticated sources are limited to 5 auth attempts per minute (IP-based)

**Independent Test**: Send 6 POST /api/v1/auth/login requests from same IP → 6th returns 429

### Tests for User Story 3

- [ ] T024 [P] [US3] Write test_login_rate_limit_enforced() - 5 pass, 6th returns 429 in tests/integration/test_rate_limits.py
- [ ] T025 [P] [US3] Write test_register_rate_limit_enforced() in tests/integration/test_rate_limits.py
- [ ] T026 [P] [US3] Write test_auth_limit_is_per_ip_not_user() in tests/integration/test_rate_limits.py

### Implementation for User Story 3

- [x] T027 [US3] Import limiter and get_remote_address in src/rag/api/v1/auth.py
- [x] T028 [US3] Add `@limiter.limit("5/minute", key_func=get_remote_address)` to POST /login in src/rag/api/v1/auth.py
- [x] T029 [US3] Add `@limiter.limit("5/minute", key_func=get_remote_address)` to POST /register in src/rag/api/v1/auth.py
- [x] T030 [US3] Add `@limiter.limit("5/minute", key_func=get_remote_address)` to POST /refresh in src/rag/api/v1/auth.py
- [ ] T031 [US3] Run tests for US3: `pytest tests/integration/test_rate_limits.py -k auth`

**Checkpoint**: Auth endpoint protection works independently

---

## Phase 6: User Story 4 - Graceful Degradation (Priority: P2)

**Goal**: When Redis is unavailable, requests succeed with warning logs (fail-open)

**Independent Test**: Stop Redis, send request → succeeds, warning in logs

### Tests for User Story 4

- [ ] T032 [P] [US4] Write test_fail_open_when_redis_unavailable() in tests/integration/test_rate_limits.py
- [ ] T033 [P] [US4] Write test_rate_limiting_resumes_when_redis_recovers() in tests/integration/test_rate_limits.py

### Implementation for User Story 4

- [x] T034 [US4] Wrap Redis operations in try/except in src/rag/core/rate_limiter.py
- [x] T035 [US4] Add warning log on Redis connection failure in src/rag/core/rate_limiter.py
- [x] T036 [US4] Return allow-all fallback when Redis unavailable in src/rag/core/rate_limiter.py
- [ ] T037 [US4] Run tests for US4: `pytest tests/integration/test_rate_limits.py -k fail_open`

**Checkpoint**: Fail-open behavior works - system stays available

---

## Phase 7: User Story 5 - Operational Logging (Priority: P2)

**Goal**: All rate limit events are logged with structured JSON for observability

**Independent Test**: Trigger rate limit → log entry contains user_id, endpoint, timestamp, limit details

### Tests for User Story 5

- [ ] T038 [P] [US5] Write test_rate_limit_block_is_logged() in tests/unit/test_rate_limiting.py
- [ ] T039 [P] [US5] Write test_log_contains_required_fields() in tests/unit/test_rate_limiting.py

### Implementation for User Story 5

- [x] T040 [US5] Create structured log format for rate limit events in src/rag/core/rate_limiter.py
- [x] T041 [US5] Log on every rate limit block (event=rate_limit_blocked) in src/rag/core/rate_limiter.py
- [x] T042 [US5] Log on Redis failures (event=rate_limit_backend_error) in src/rag/core/rate_limiter.py
- [ ] T043 [US5] Run tests for US5: `pytest tests/unit/test_rate_limiting.py`

**Checkpoint**: Full observability for rate limiting events

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Frontend integration, documentation, and final validation

- [x] T044 [P] Update frontend axios interceptor to handle 429 in frontend/rag-frontend/src/lib/api/client.ts
- [x] T045 [P] Show user-friendly "Rate limit exceeded, retry in X seconds" toast in frontend
- [ ] T046 [P] Create tests/unit/test_rate_limiting.py with unit tests for key extraction functions
- [x] T047 [P] Add rate limiting section to CLAUDE.md documentation
- [x] T048 Verify excluded endpoints (/health, /docs, /redoc) are NOT rate limited
- [ ] T049 Run full test suite: `pytest tests/ -v`
- [ ] T050 Run quickstart.md validation steps manually

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup ──────────────────► No dependencies
    │
    ▼
Phase 2: Foundational ───────────► BLOCKS all user stories
    │
    ├──► Phase 3: US1 Chat (P1) ──────┐
    ├──► Phase 4: US2 Upload (P1) ────┤ Can run in PARALLEL
    ├──► Phase 5: US3 Auth (P1) ──────┤ after Phase 2
    ├──► Phase 6: US4 Fail-open (P2) ─┤
    └──► Phase 7: US5 Logging (P2) ───┘
                    │
                    ▼
            Phase 8: Polish ──────────► All stories complete
```

### User Story Dependencies

| Story | Depends On | Can Parallelize With |
|-------|------------|---------------------|
| US1 (Chat) | Phase 2 | US2, US3, US4, US5 |
| US2 (Upload) | Phase 2 | US1, US3, US4, US5 |
| US3 (Auth) | Phase 2 | US1, US2, US4, US5 |
| US4 (Fail-open) | Phase 2 | US1, US2, US3, US5 |
| US5 (Logging) | Phase 2 | US1, US2, US3, US4 |

### Within Each User Story

1. Tests FIRST (T011-T014, etc.) → should FAIL initially
2. Implementation (T015-T017, etc.)
3. Run story tests → should PASS
4. Checkpoint validation

---

## Parallel Execution Examples

### Phase 2 Parallelization

```bash
# These can run in parallel (different functions in same file):
Task T006: get_remote_address() function
Task T007: get_user_key() function
Task T008: Exception handler function
```

### User Story Parallelization (Multi-Developer)

```bash
# Developer A: User Story 1 (Chat)
T011-T018: Chat rate limiting

# Developer B: User Story 3 (Auth)
T024-T031: Auth protection

# Developer C: User Story 4 + 5 (Observability)
T032-T043: Fail-open + Logging
```

### Test Parallelization (Within Story)

```bash
# All US1 tests can run in parallel:
pytest tests/integration/test_rate_limits.py -k chat -n auto
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. ✅ Complete Phase 1: Setup
2. ✅ Complete Phase 2: Foundational
3. ✅ Complete Phase 3: User Story 1 (Chat)
4. **STOP and VALIDATE**: Test chat rate limiting independently
5. Deploy/demo if ready - **MVP complete with core value!**

### Incremental Delivery

| Increment | Stories | Value Delivered |
|-----------|---------|-----------------|
| MVP | US1 | Chat protected from abuse |
| +1 | US1 + US2 | Uploads also protected |
| +2 | US1 + US2 + US3 | Auth brute-force prevented |
| +3 | All P1 + US4 | Fail-open reliability |
| Complete | All | Full observability |

### Suggested Order (Solo Developer)

1. Phase 1 → Phase 2 (blocking)
2. Phase 3: US1 Chat (MVP) ✅
3. Phase 5: US3 Auth (security critical)
4. Phase 4: US2 Upload
5. Phase 6: US4 Fail-open
6. Phase 7: US5 Logging
7. Phase 8: Polish

---

## Summary

| Metric | Count |
|--------|-------|
| **Total Tasks** | 50 |
| **Setup Tasks** | 4 |
| **Foundational Tasks** | 6 |
| **US1 (Chat) Tasks** | 8 |
| **US2 (Upload) Tasks** | 5 |
| **US3 (Auth) Tasks** | 8 |
| **US4 (Fail-open) Tasks** | 6 |
| **US5 (Logging) Tasks** | 6 |
| **Polish Tasks** | 7 |
| **Parallel Opportunities** | 25 tasks marked [P] |

---

## Notes

- [P] tasks = different files or independent functions, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Verify tests fail before implementing (TDD approach)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
