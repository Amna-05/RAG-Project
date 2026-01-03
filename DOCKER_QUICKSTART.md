# Docker Local Development Guide

This guide explains how to run the RAG system locally using Docker.

## Prerequisites

- Docker Desktop installed ([get Docker](https://www.docker.com/products/docker-desktop))
- Docker Compose v2+
- `.env` file configured with API keys (see [Configuration](#configuration) below)

## Quick Start

### 1. Start All Services

```bash
# Start PostgreSQL, Redis, and FastAPI backend
docker-compose up -d
```

**What starts:**
- PostgreSQL database on `localhost:5432`
- Redis cache on `localhost:6379`
- FastAPI backend on `http://localhost:8000`

### 2. Verify Services Are Running

```bash
# Check all containers are healthy
docker-compose ps

# View backend logs
docker-compose logs -f backend

# Check database connection
docker-compose exec postgres psql -U postgres -d rag_db -c "SELECT 1;"

# Check Redis connection
docker-compose exec redis redis-cli ping
```

### 3. Access API

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### 4. Run Database Migrations

Migrations run automatically on startup, but you can run them manually:

```bash
# Apply all migrations
docker-compose exec backend alembic upgrade head

# Check current migration version
docker-compose exec backend alembic current
```

## Configuration

### Create .env File

Copy `.env.example` and configure with your API keys:

```bash
cp .env.example .env
```

**Essential Variables:**

```env
# At least ONE LLM provider is required
GOOGLE_API_KEY=your-gemini-api-key        # Free tier available
XAI_API_KEY=your-grok-api-key            # Free trial available
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-claude-api-key

# Vector Database (required for search)
PINECONE_API_KEY=your-pinecone-api-key

# Email Service (optional, for password reset)
RESEND_API_KEY=your-resend-api-key

# Frontend URL (for password reset links)
FRONTEND_URL=http://localhost:3000
```

**Free Tier Providers:**
- **Google Gemini**: Free tier available at https://ai.google.dev
- **xAI Grok**: Free trial available at https://console.x.ai
- **Pinecone**: Free tier available at https://www.pinecone.io

## Common Commands

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f postgres
docker-compose logs -f redis
```

### Stop Services

```bash
# Stop all (keep data)
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

### Rebuild Image

```bash
# Rebuild after code changes
docker-compose build backend

# Rebuild and restart
docker-compose up -d --build backend
```

### Run Commands in Container

```bash
# Run pytest
docker-compose exec backend pytest tests/

# Run a single test
docker-compose exec backend pytest tests/integration/test_email_and_logging.py

# Access Python shell
docker-compose exec backend python

# Access PostgreSQL CLI
docker-compose exec postgres psql -U postgres -d rag_db

# Access Redis CLI
docker-compose exec redis redis-cli
```

### Database Commands

```bash
# Connect to database
docker-compose exec postgres psql -U postgres -d rag_db

# Create a new migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Rollback last migration
docker-compose exec backend alembic downgrade -1

# Check migration history
docker-compose exec backend alembic history
```

## Troubleshooting

### Services Won't Start

```bash
# Check for port conflicts
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :8000  # Backend

# View detailed error logs
docker-compose logs backend

# Restart everything from scratch
docker-compose down -v
docker-compose up -d
```

### Database Connection Error

```bash
# Wait for PostgreSQL to be ready
docker-compose up postgres
# Wait 10 seconds, then:
docker-compose up -d

# Check database is initialized
docker-compose exec postgres psql -U postgres -d rag_db -c "\dt"
```

### Redis Connection Error

```bash
# Check Redis is running
docker-compose exec redis redis-cli ping
# Should respond: PONG

# Restart Redis
docker-compose restart redis
```

### Backend Won't Start

```bash
# Check logs for specific error
docker-compose logs backend

# Verify database is ready
docker-compose exec postgres pg_isready -U postgres

# Verify environment variables are loaded
docker-compose exec backend env | grep DATABASE_URL
```

### Out of Memory

Docker containers have limited memory by default. Increase in Docker Desktop settings:
- Docker Desktop → Settings → Resources → Memory (increase to 4GB+)

## Production Considerations

This `docker-compose.yml` is configured for **local development only**:

- Default credentials (change in production)
- Health checks disabled for speed
- Logging is verbose
- Database and cache data persisted in volumes

For production, see [DEPLOYMENT.md](DEPLOYMENT.md)

## Next Steps

1. **Test the API**: Use Swagger UI at http://localhost:8000/docs
2. **Upload documents**: Test the `/api/v1/rag/upload` endpoint
3. **Query documents**: Test the `/api/v1/rag/chat` endpoint
4. **Check logs**: View JSON logs with `docker-compose logs -f backend`

## FAQ

**Q: Can I use a local LLM instead of cloud providers?**
A: Yes! Set `USE_OLLAMA=true` and ensure Ollama is running. Add it to docker-compose.yml if needed.

**Q: How do I persist data between container restarts?**
A: Docker volumes handle this automatically. PostgreSQL data in `postgres_data` and Redis data in `redis_data`.

**Q: Can I run just the database without the backend?**
A: Yes! `docker-compose up postgres redis` runs just those services.

**Q: How do I debug issues inside containers?**
A: Use `docker-compose exec backend python -m pdb <script>` or add breakpoints and use `docker-compose logs -f`.
