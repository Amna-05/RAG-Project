# Implementation Plan: Backend Improvements & Production Readiness

**Branch**: `002-backend-production-readiness` | **Date**: 2026-01-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-backend-production-readiness/spec.md`

## Summary

Enhance the RAG backend for production deployment with improved document retrieval (hybrid BM25 + semantic search), password reset via email (Resend SMTP), structured logging/monitoring, comprehensive test coverage (80%), and containerized deployment. Focus on reliability, testability, and operational readiness over UI polish.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: FastAPI, SQLAlchemy, Alembic, Pydantic, SlowAPI, sentence-transformers, rank-bm25
**Storage**: PostgreSQL (primary), Pinecone (vectors), Local disk (files)
**Testing**: pytest, pytest-cov, HTTPX, pytest-asyncio
**Target Platform**: Linux server (Docker), Railway deployment
**Project Type**: Web application (backend API + Next.js frontend)
**Performance Goals**: 1000 concurrent users, <30s document processing for 10MB files
**Constraints**: <2 min password reset email delivery, 99% uptime, 30-day log retention
**Scale/Scope**: 5-50 users per logical tenant, 10MB max file size

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Rule | Status | Notes |
|------|--------|-------|
| §3 Architecture: Layered | PASS | Existing architecture follows pattern |
| §3 Architecture: No business logic in routers | PASS | All logic in services |
| §3 Architecture: DI everywhere | PASS | FastAPI Depends() used |
| §4 Stack: Python 3.12+, FastAPI, SQLAlchemy | PASS | Matches locked stack |
| §4 AI/ML: Sentence-Transformers, Pinecone | PASS | Current implementation |
| §5 Security: JWT httpOnly, bcrypt | PASS | Already implemented |
| §5 Security: No secrets in code | PASS | Config via .env |
| §5 Security: File validation, size limits | PASS | 10MB limit, type validation |
| §6 Reliability: LLM fallback | PASS | FR-018 defines retry+fallback |
| §6.1 Rate Limiting | PASS | Already implemented |
| §7 Logging: Structured JSON | PASS | FR-012 through FR-016 |
| §8 Testing: Unit + integration | PASS | FR-021 through FR-024 |
| §9 Config: .env.example | PASS | FR-026 |
| §10 Docker: Slim image, non-root | PASS | FR-025 |

**Gate Result**: ALL CHECKS PASS - Proceed to Phase 0

## Project Structure

### Documentation (this feature)

specs/002-backend-production-readiness/
- spec.md - Feature specification
- plan.md - This file
- research.md - Phase 0 output
- data-model.md - Phase 1 output
- quickstart.md - Phase 1 output
- contracts/ - Phase 1 output (OpenAPI)
- tasks.md - Phase 2 output

### Source Code (repository root)

src/rag/
- api/deps.py - DI: get_current_user, rate limiters
- api/v1/auth.py - Auth endpoints + password reset
- api/v1/rag.py - Upload, documents, chat endpoints
- core/config.py - Settings from env vars
- core/database.py - Async SQLAlchemy
- core/security.py - JWT, password hashing
- core/logging.py - NEW: Structured logging setup
- services/auth_service.py - Auth logic
- services/email_service.py - NEW: Resend SMTP integration
- services/rag_service.py - Document orchestration
- services/document_service.py - Document CRUD
- services/search_service.py - NEW: Hybrid search (BM25 + semantic)
- services/llm_service.py - LLM with retry/fallback
- crud/ - Repository layer
- models/ - SQLAlchemy models
- schemas/ - Pydantic schemas
- documents.py - Text extraction + chunking
- embeddings.py - Sentence-transformers
- vectorstore.py - Pinecone operations

tests/
- unit/ - Unit tests
- integration/ - Integration tests
- conftest.py - Fixtures, mocks

**Structure Decision**: Web application pattern - backend API (src/rag/) + frontend (frontend/rag-frontend/).

## Complexity Tracking

No constitution violations requiring justification. All patterns align with existing architecture.

## Phase 0: Research Summary

See research.md for detailed findings on:
1. BM25 library selection (rank-bm25)
2. Hybrid search scoring algorithm
3. Resend SMTP configuration
4. Structured logging patterns
5. Test coverage tooling

## Phase 1: Design Artifacts

- data-model.md - Entity definitions
- contracts/ - OpenAPI specifications
- quickstart.md - Developer setup guide
