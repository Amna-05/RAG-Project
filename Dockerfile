# Multi-stage build for Python FastAPI backend
# Stage 1: Builder
FROM python:3.12-slim as builder

WORKDIR /build

# Install system dependencies for building wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY pyproject.toml uv.lock ./

# Install uv package manager
RUN pip install --no-cache-dir uv

# Create wheels
RUN uv pip compile pyproject.toml --output-file requirements.txt && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt


# Stage 2: Runtime
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 appuser

# Copy wheels from builder
COPY --from=builder /build/wheels /wheels
COPY --from=builder /build/requirements.txt .

# Install wheels
RUN pip install --no-cache-dir --no-index --find-links /wheels -r requirements.txt && \
    rm -rf /wheels requirements.txt

# Copy application code directly to /app (not in src subdirectory)
COPY --chown=appuser:appuser src/rag/ rag/
COPY --chown=appuser:appuser alembic/ alembic/
COPY --chown=appuser:appuser alembic.ini .
COPY --chown=appuser:appuser .env.example .env

# Create necessary directories
RUN mkdir -p data/uploads data/embeddings_cache logs && \
    chown -R appuser:appuser data logs

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Expose port
EXPOSE 8000

# Set Python to run in unbuffered mode for real-time logging
ENV PYTHONUNBUFFERED=1

# Start Uvicorn (rag module is now directly in /app)
CMD ["uvicorn", "rag.main:app", "--host", "0.0.0.0", "--port", "8000"]
