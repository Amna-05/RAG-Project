# Tasks: Backend Improvements & Production Readiness

**Input**: Design documents from /specs/002-backend-production-readiness/
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Included (FR-021 requires 80% test coverage)

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: [ID] [P?] [Story] Description

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, etc.)
- Paths use existing structure: src/rag/, tests/

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add new dependencies and update project configuration

- [x] T001 Add rank-bm25, resend, structlog dependencies to pyproject.toml
- [x] T002 [P] Add pytest-cov, pytest-asyncio to test dependencies in pyproject.toml
- [x] T003 Run uv sync to install new dependencies
- [x] T004 [P] Update .env.example with RESEND_API_KEY, SMTP_FROM_EMAIL, SMTP_FROM_NAME

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Database migrations and core infrastructure

- [x] T005 Create Alembic migration for PasswordResetToken table in alembic/versions/
- [x] T006 [P] Create Alembic migration for RequestLog table in alembic/versions/
- [x] T007 [P] Create Alembic migration for SystemMetric table in alembic/versions/
- [x] T008 [P] Create Alembic migration to add bm25_indexed column to documents table
- [ ] T009 Run alembic upgrade head to apply all migrations
- [x] T010 [P] Create PasswordResetToken model in src/rag/models/password_reset.py
- [x] T011 [P] Create RequestLog model in src/rag/models/request_log.py
- [x] T012 [P] Create SystemMetric model in src/rag/models/system_metric.py
- [x] T013 Update Document model to add bm25_indexed field in src/rag/models/document.py
- [x] T014 [P] Create Pydantic schemas for password reset in src/rag/schemas/password_reset.py
- [x] T015 [P] Create Pydantic schemas for logging/metrics in src/rag/schemas/logging.py
- [x] T016 [P] Create test fixtures and mocks in tests/conftest.py
- [x] T017 [P] Create Pinecone mock in tests/mocks/pinecone_mock.py
- [x] T018 [P] Create LLM provider mock in tests/mocks/llm_mock.py
- [x] T019 [P] Create email service mock in tests/mocks/email_mock.py

**Checkpoint**: Foundation ready - user story implementation can begin

---

## Phase 3: User Story 1 - Document Upload and Retrieval (Priority: P1)

**Goal**: Implement hybrid BM25 + semantic search with configurable chunking

**Independent Test**: Upload a document, query it, verify hybrid search returns relevant chunks

### Tests for User Story 1

- [x] T020 [P] [US1] Create unit tests for chunking logic in tests/unit/test_chunking.py
- [x] T021 [P] [US1] Create unit tests for BM25 scoring in tests/unit/test_search.py
- [ ] T022 [P] [US1] Create unit tests for embedding generation in tests/unit/test_embeddings.py
- [ ] T023 [US1] Create integration test for upload-process-retrieve in tests/integration/test_upload_pipeline.py

### Implementation for User Story 1

- [ ] T024 [US1] Update chunking logic with configurable size/overlap in src/rag/documents.py
- [ ] T025 [US1] Ensure deterministic chunking in src/rag/documents.py
- [x] T026 [US1] Create SearchService with BM25 + semantic hybrid in src/rag/services/search_service.py
- [x] T027 [US1] Implement 50/50 weighted scoring in src/rag/services/search_service.py
- [x] T028 [US1] Update RAG service to use hybrid search in src/rag/services/rag_service.py
- [ ] T029 [US1] Update chat endpoint for top 5 hybrid-ranked chunks in src/rag/api/v1/rag.py
- [ ] T030 [US1] Add user-friendly message for empty results in src/rag/api/v1/rag.py

**Checkpoint**: Hybrid search working

---
## Phase 4: User Story 2 - Password Reset (Priority: P1)

**Goal**: Implement secure password reset flow via email

**Independent Test**: Request reset -> receive email -> click link -> set new password -> login works

### Tests for User Story 2

- [ ] T031 [P] [US2] Create unit tests for token generation/validation in tests/unit/test_password_reset.py
- [ ] T032 [P] [US2] Create unit tests for email service in tests/unit/test_email_service.py
- [ ] T033 [US2] Create integration test for full reset flow in tests/integration/test_password_reset_flow.py

### Implementation for User Story 2

- [ ] T034 [US2] Create EmailService with Resend integration in src/rag/services/email_service.py
- [ ] T035 [US2] Create password reset email template in src/rag/templates/password_reset_email.html
- [ ] T036 [US2] Create PasswordResetService in src/rag/services/password_reset_service.py
- [ ] T037 [US2] Implement token generation (32 bytes, SHA-256 hash) in src/rag/services/password_reset_service.py
- [ ] T038 [US2] Implement token validation (1-hour expiry check) in src/rag/services/password_reset_service.py
- [ ] T039 [US2] Invalidate previous tokens when new one requested in src/rag/services/password_reset_service.py
- [ ] T040 [US2] Create forgot-password endpoint in src/rag/api/v1/auth.py
- [ ] T041 [US2] Create reset-password endpoint in src/rag/api/v1/auth.py
- [ ] T042 [US2] Create verify-reset-token endpoint in src/rag/api/v1/auth.py
- [ ] T043 [US2] Add rate limiting (3/hour) to password reset endpoints in src/rag/api/v1/auth.py

**Checkpoint**: Password reset flow complete

---

## Phase 5: User Story 3 - Structured Logging & Metrics (Priority: P2)

**Goal**: Implement JSON structured logging with request correlation

**Independent Test**: Make API request -> verify JSON log entry with request_id, user_id, duration

### Tests for User Story 3

- [ ] T044 [P] [US3] Create unit tests for log formatting in tests/unit/test_logging.py
- [ ] T045 [P] [US3] Create unit tests for sensitive data filtering in tests/unit/test_logging.py
- [ ] T046 [US3] Create integration test for request logging in tests/integration/test_request_logging.py

### Implementation for User Story 3

- [ ] T047 [US3] Create structured logging setup with structlog in src/rag/core/logging.py
- [ ] T048 [US3] Implement JSON formatter with configurable output in src/rag/core/logging.py
- [ ] T049 [US3] Implement sensitive data filtering (passwords, tokens) in src/rag/core/logging.py
- [ ] T050 [US3] Create request ID middleware in src/rag/middleware/request_id.py
- [ ] T051 [US3] Create logging middleware in src/rag/middleware/logging.py
- [ ] T052 [US3] Add request logging to database (RequestLog model) in src/rag/middleware/logging.py
- [ ] T053 [US3] Create MetricsService for counter/gauge tracking in src/rag/services/metrics_service.py
- [ ] T054 [US3] Implement 30-day log retention cleanup in src/rag/services/metrics_service.py
- [ ] T055 [US3] Add logging configuration to settings in src/rag/core/config.py
- [ ] T056 [US3] Integrate logging into main.py lifespan in src/rag/main.py

**Checkpoint**: Structured logging operational

---

## Phase 6: User Story 4 - Graceful Degradation (Priority: P2)

**Goal**: Implement fallback behavior for external service failures

**Independent Test**: Disable primary LLM -> verify fallback activates -> user gets response

### Tests for User Story 4

- [ ] T057 [P] [US4] Create unit tests for LLM fallback logic in tests/unit/test_llm_fallback.py
- [ ] T058 [US4] Create integration test for degradation scenarios in tests/integration/test_graceful_degradation.py

### Implementation for User Story 4

- [ ] T059 [US4] Implement retry-once logic in LLM service in src/rag/services/llm_service.py
- [ ] T060 [US4] Implement fallback to alternative provider in src/rag/services/llm_service.py
- [ ] T061 [US4] Add error logging for LLM failures in src/rag/services/llm_service.py

**Checkpoint**: Graceful degradation working

---

## Phase 7: User Story 5 - Test Coverage (Priority: P2)

**Goal**: Achieve 80% test coverage on critical modules

**Independent Test**: Run pytest --cov -> verify 80%+ on documents.py, embeddings.py, auth_service.py, search_service.py

### Tests for User Story 5

- [ ] T062 [P] [US5] Add edge case tests for documents.py in tests/unit/test_documents.py
- [ ] T063 [P] [US5] Add edge case tests for embeddings.py in tests/unit/test_embeddings.py
- [ ] T064 [P] [US5] Add edge case tests for auth_service.py in tests/unit/test_auth_service.py
- [ ] T065 [P] [US5] Add edge case tests for search_service.py in tests/unit/test_search_service.py
- [ ] T066 [US5] Configure pytest-cov with coverage thresholds in pyproject.toml
- [ ] T067 [US5] Add coverage reporting to pytest configuration in pyproject.toml
- [ ] T068 [US5] Verify 80% coverage achieved, add missing tests if needed

**Checkpoint**: 80% test coverage achieved

---

## Phase 8: User Story 6 - Docker Deployment (Priority: P3)

**Goal**: Create production-ready Docker configuration

**Independent Test**: docker-compose up -> health check passes -> API responds

### Implementation for User Story 6

- [ ] T069 [US6] Update Dockerfile with multi-stage build in Dockerfile
- [ ] T070 [US6] Configure non-root user in Dockerfile
- [ ] T071 [US6] Update docker-compose.yml with production settings in docker-compose.yml
- [ ] T072 [US6] Add health check endpoint configuration in src/rag/main.py
- [ ] T073 [US6] Create Railway deployment configuration in railway.toml
- [ ] T074 [US6] Document deployment process in specs/002-backend-production-readiness/quickstart.md

**Checkpoint**: Docker deployment ready

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final integration, documentation, and cleanup

- [ ] T075 Update main.py to wire all new services in src/rag/main.py
- [ ] T076 Update API router to include new endpoints in src/rag/api/v1/__init__.py
- [ ] T077 Run full test suite and verify all tests pass
- [ ] T078 Run coverage report and verify 80% threshold met
- [ ] T079 Update CLAUDE.md with new features and endpoints

**Checkpoint**: Feature complete and production-ready

---

## Dependencies & Execution Order

Phase 1 (Setup) and Phase 2 (Foundational) must complete first.
After Phase 2, US1-US5 can be implemented in any order or in parallel.
Phase 8 (Docker) depends on implementation being complete.
Phase 9 (Polish) runs last.

**User Story Independence**: After Phase 2, US1-US5 can be implemented in any order or in parallel by different developers. US6 (Docker) depends on implementation being complete.

---

## Summary

| Phase | User Story | Tasks | Parallel | Description |
|-------|------------|-------|----------|-------------|
| 1 | Setup | 4 | 2 | Dependencies and configuration |
| 2 | Foundational | 15 | 12 | Migrations, models, schemas, mocks |
| 3 | US1 | 11 | 3 | Hybrid BM25 + semantic search |
| 4 | US2 | 13 | 2 | Password reset via email |
| 5 | US3 | 13 | 2 | Structured logging & metrics |
| 6 | US4 | 5 | 1 | Graceful degradation |
| 7 | US5 | 7 | 4 | 80% test coverage |
| 8 | US6 | 6 | 0 | Docker deployment |
| 9 | Polish | 5 | 0 | Final integration |
| **Total** | | **79** | **26** | |

**MVP Scope**: Phase 1 + Phase 2 + Phase 3 (US1: Hybrid Search) = 30 tasks

**Suggested Implementation Order**:
1. Complete Setup and Foundational phases first
2. Start with US1 (Hybrid Search) - highest user value
3. Add US2 (Password Reset) - security critical
4. Add US3 (Logging) - operational visibility
5. Complete remaining stories as capacity allows
