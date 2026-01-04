# Quickstart: Backend Improvements & Production Readiness

**Feature**: 002-backend-production-readiness
**Date**: 2026-01-02

## Prerequisites

- Python 3.12+
- PostgreSQL 14+
- Node.js 18+ (for frontend)
- Docker & Docker Compose (optional)
- Resend account (for email)
- Pinecone account (for vectors)

## Environment Setup

### 1. Clone and Install

```bash
# Clone repository
git clone <repo-url>
cd rag-project

# Switch to feature branch
git checkout 002-backend-production-readiness

# Install backend dependencies
uv sync

# Install frontend dependencies
cd frontend/rag-frontend && npm install && cd ../..
```

### 2. Configure Environment

Copy and configure environment variables:

```bash
cp .env.example .env
```

Required variables for this feature:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/ragdb

# Authentication
JWT_SECRET_KEY=your-secret-key-min-32-chars
JWT_REFRESH_SECRET_KEY=your-refresh-secret-key

# Vector Store
PINECONE_API_KEY=your-pinecone-key
PINECONE_INDEX_NAME=rag-index

# AI Provider
GOOGLE_API_KEY=your-gemini-key
# Optional fallback
OPENAI_API_KEY=your-openai-key

# Email (NEW)
RESEND_API_KEY=re_your_resend_key
SMTP_FROM_EMAIL=noreply@yourdomain.com
SMTP_FROM_NAME=RAG App

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_STORAGE=memory  # or "redis"

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### 3. Database Setup

```bash
# Run migrations
alembic upgrade head
```

### 4. Run Development Server

```bash
# Backend (from project root)
python run.py

# Or with uvicorn directly
uvicorn rag.main:app --reload --host 127.0.0.1 --port 8000

# Frontend (in separate terminal)
cd frontend/rag-frontend
npm run dev
```

## Testing

### Run All Tests

```bash
# With coverage report
pytest

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Generate HTML coverage report
pytest --cov-report=html
```

### Test Coverage Target

Minimum 80% coverage required for:
- src/rag/documents.py (chunking)
- src/rag/embeddings.py
- src/rag/services/auth_service.py
- src/rag/services/search_service.py

## New Features in This Branch

### 1. Password Reset

Request reset:
```bash
curl -X POST http://localhost:8000/api/v1/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

Reset password:
```bash
curl -X POST http://localhost:8000/api/v1/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{"token": "...", "new_password": "NewPassword123!"}'
```

### 2. Hybrid Search

Chat endpoint now uses hybrid BM25 + semantic search:
```bash
curl -X POST http://localhost:8000/api/v1/rag/chat \
  -H "Content-Type: application/json" \
  -H "Cookie: access_token=..." \
  -d '{"question": "What is the main topic?"}'
```

### 3. Structured Logging

Logs are now JSON-formatted with request IDs:
```json
{
  "timestamp": "2026-01-02T10:30:00Z",
  "level": "INFO",
  "request_id": "abc-123",
  "endpoint": "/api/v1/rag/chat",
  "user_id": "user-uuid",
  "status_code": 200,
  "duration_ms": 150.5
}
```

## Docker Development

```bash
# Build and run
docker-compose up --build

# Run with specific service
docker-compose up backend

# View logs
docker-compose logs -f backend
```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## Troubleshooting

### Email not sending
1. Verify RESEND_API_KEY is set correctly
2. Check domain is verified in Resend dashboard
3. Review logs for email service errors

### Tests failing with coverage < 80%
1. Run `pytest --cov-report=term-missing` to see uncovered lines
2. Add tests for uncovered branches
3. Check `htmlcov/index.html` for visual report

### Rate limiting issues in development
Set `RATE_LIMIT_ENABLED=false` in .env for local testing
