# Research: Backend Improvements & Production Readiness

**Feature**: 002-backend-production-readiness
**Date**: 2026-01-02

## 1. BM25 Library Selection

### Decision: rank-bm25

### Rationale
- Pure Python implementation, no external dependencies
- Well-maintained with 1.5k+ GitHub stars
- Simple API for scoring queries against corpus
- Supports pre-tokenized input (integrates well with existing chunking)
- Lightweight (~50KB) vs alternatives like Whoosh (~2MB)

### Alternatives Considered

| Library | Pros | Cons | Decision |
|---------|------|------|----------|
| **rank-bm25** | Simple, lightweight, pure Python | No persistence | SELECTED |
| **Whoosh** | Full-text search, indexing | Heavy, overkill for hybrid | Rejected |
| **Elasticsearch** | Production-grade, scalable | Separate service, complexity | Rejected |
| **gensim** | BM25 included, NLP features | Large dependency | Rejected |

### Implementation Notes
- Use BM25Okapi variant for best results
- Pre-compute BM25 index per user namespace
- Tokenize with simple whitespace split (consistent with chunking)

---

## 2. Hybrid Search Scoring Algorithm

### Decision: Weighted Linear Combination (50/50)

### Rationale
- Simple, interpretable, tunable
- Equal weighting as starting point (per clarification)
- Normalize both scores to [0, 1] before combining
- Can adjust weights based on retrieval quality feedback

### Algorithm
1. Normalize BM25 scores using min-max scaling across results
2. Semantic scores (cosine similarity) already in [0, 1]
3. Combine: final_score = 0.5 * bm25_norm + 0.5 * semantic_score

### Retrieval Flow
1. User query received
2. Generate query embedding (sentence-transformers)
3. Fetch top-K candidates from Pinecone (semantic)
4. Compute BM25 scores against candidate chunks
5. Combine scores with 50/50 weighting
6. Re-rank and return top 5

---

## 3. Resend SMTP Configuration

### Decision: Resend API with SMTP Fallback

### Rationale
- Resend provides REST API (simpler) and SMTP interface
- High deliverability with proper SPF/DKIM setup
- Free tier: 100 emails/day (sufficient for small teams)
- Python SDK available: resend package

### Configuration Variables
- RESEND_API_KEY: API key from Resend dashboard
- SMTP_FROM_EMAIL: Verified sender email
- SMTP_FROM_NAME: Display name for sender

### Deliverability Checklist
- Verify domain in Resend dashboard
- Add SPF record to DNS
- Add DKIM record to DNS
- Test with major providers (Gmail, Outlook, Yahoo)

---

## 4. Structured Logging Patterns

### Decision: Python logging with JSON formatter + structlog

### Rationale
- Built-in logging module for compatibility
- structlog for structured JSON output
- Request correlation IDs for tracing
- Sensitive data filtering

### Log Levels
- **INFO**: Normal operations (request completed, document uploaded)
- **WARNING**: Recoverable issues (rate limit hit, cache miss)
- **ERROR**: Failures (LLM error, email failed, DB error)

### Key Features
- Request ID middleware for correlation
- Automatic field redaction for sensitive data
- JSON output for log aggregation
- User ID tracking for authenticated requests

---

## 5. Test Coverage Tooling

### Decision: pytest-cov with 80% target

### Rationale
- pytest-cov integrates with pytest seamlessly
- Branch coverage for thorough testing
- HTML reports for visualization
- CI/CD integration via XML output

### Test Structure
- tests/unit/ - Unit tests for isolated components
- tests/integration/ - End-to-end flow tests
- tests/conftest.py - Shared fixtures and mocks
- tests/mocks/ - Mock implementations for external services

### Running Tests
- pytest (all tests with coverage)
- pytest tests/unit/ (unit tests only)
- pytest --cov-report=html (generate HTML report)

---

## Dependencies to Add

New packages for pyproject.toml:
- rank-bm25 ^0.2.2 (BM25 scoring)
- resend ^0.7.0 (email service)
- structlog ^24.1.0 (structured logging)
- pytest-cov >=4.1.0 (coverage reporting)
- pytest-asyncio >=0.23.0 (async test support)

---

## Summary

| Research Topic | Decision | Confidence |
|----------------|----------|------------|
| BM25 Library | rank-bm25 | High |
| Hybrid Scoring | 50/50 weighted linear | Medium (tunable) |
| Email Service | Resend API | High |
| Logging | structlog + JSON | High |
| Test Coverage | pytest-cov, 80% target | High |

All research items resolved. Ready for Phase 1 design.
