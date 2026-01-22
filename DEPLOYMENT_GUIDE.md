# Deployment Guide: Local Setup → Railway

Complete step-by-step guide to run the RAG project locally and deploy to Railway.app.

---

## Part 1: Local Development Setup

### Prerequisites
- Python 3.11+ installed
- PostgreSQL 16+ running locally
- Docker & Docker Compose (for containerized testing)
- Git
- Code editor (VS Code recommended)

### Step 1: Clone & Setup Python Environment

```bash
# Navigate to project directory
cd rag-project

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows (Command Prompt):
.venv\Scripts\activate

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# On macOS/Linux:
source .venv/bin/activate

# Install dependencies using uv
pip install uv
uv sync
```

### Step 2: Setup PostgreSQL Database

**Option A: Using Local PostgreSQL Installation**

```bash
# Start PostgreSQL service (Windows)
# If installed via PostgreSQL installer, it should auto-start

# Or if using WSL2:
sudo service postgresql start

# Create database and user
psql -U postgres -c "CREATE DATABASE rag_db;"
psql -U postgres -c "CREATE USER rag_user WITH PASSWORD 'secure_password_here';"
psql -U postgres -c "ALTER ROLE rag_user WITH CREATEDB;"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE rag_db TO rag_user;"
```

**Option B: Using Docker (Recommended)**

```bash
# Start PostgreSQL in Docker (one-time setup)
docker run -d \
  --name rag_postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=rag_db \
  -p 5432:5432 \
  postgres:16-alpine

# Verify it's running
docker ps | grep rag_postgres
```

### Step 3: Configure Environment Variables

```bash
# Copy example to .env
cp .env.example .env

# Edit .env with your values:
# Windows: code .env
# macOS/Linux: nano .env
```

**Minimal required configuration for local dev:**

```env
# Database (for local PostgreSQL)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/rag_db

# JWT (can use dev values, change in production)
JWT_SECRET_KEY=your-dev-secret-key-change-in-production
JWT_REFRESH_SECRET_KEY=your-dev-refresh-secret-key-change-in-production

# CORS (for local frontend)
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]

# LLM API Key (get from https://ai.google.dev)
GOOGLE_API_KEY=your-google-gemini-api-key

# Pinecone (get from https://www.pinecone.io)
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_INDEX_NAME=rag-project

# Rate Limiting (use memory in dev)
RATE_LIMIT_STORAGE=memory
RATE_LIMIT_ENABLED=true

# Optional: Resend for emails
RESEND_API_KEY=re_your_key
```

### Step 4: Run Database Migrations

```bash
# Activate venv first (if not already active)
.venv\Scripts\activate  # Windows

# Run migrations
alembic upgrade head

# Verify tables created
# psql -U postgres -d rag_db -c "\dt"
```

### Step 5: Start Backend Server

```bash
# Terminal 1: Backend
.venv\Scripts\activate
python run.py

# Expected output:
# INFO:     Uvicorn running on http://127.0.0.1:8000
# INFO:     Application startup complete
```

### Step 6: Start Frontend Server

```bash
# Terminal 2: Frontend
cd frontend/rag-frontend
npm install  # First time only
npm run dev

# Expected output:
# ▲ Next.js 15.1.4
# ✓ Ready in 1234ms
# ► Local: http://localhost:3000
```

### Step 7: Verify Everything Works

```bash
# Test backend health
curl http://localhost:8000/health

# Expected response: { "status": "healthy" }

# Visit frontend
# Open browser to http://localhost:3000
# Try: Register → Upload Document → Chat
```

---

## Part 2: Docker Local Testing

### Test with Docker Compose (Full Stack)

This simulates the production environment locally.

```bash
# Build all images (takes ~5-10 min first time)
docker-compose build

# Start all services
docker-compose up

# Expected services:
# ✓ postgres (port 5432)
# ✓ redis (port 6379)
# ✓ backend (port 8000)
# ✓ frontend (port 3000)

# Test health endpoints
curl http://localhost:8000/health
curl http://localhost:3000

# Stop all services
docker-compose down

# Stop and remove all data
docker-compose down -v
```

### Troubleshoot Docker Issues

```bash
# View logs for specific service
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres

# Follow logs in real-time
docker-compose logs -f backend

# Check service health
docker-compose ps

# Rebuild specific service
docker-compose up --build backend
```

---

## Part 3: Prepare for Railway Deployment

### Step 1: Create Railway Account & Project

```bash
# 1. Visit https://railway.app
# 2. Sign up (GitHub recommended)
# 3. Create new project
# 4. Select "Deploy from GitHub"
```

### Step 2: Prepare GitHub Repository

```bash
# Remove sensitive data from .env
# IMPORTANT: Never commit .env with API keys!

# Check git status
git status

# If .env is tracked, remove it
git rm --cached .env
echo ".env" >> .gitignore

# Commit changes
git add .gitignore
git commit -m "Remove .env from tracking"

# Push to GitHub
git push origin main
```

### Step 3: Generate Secure Secrets for Production

```bash
# Generate new JWT secrets (run this ONCE per deployment)
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('JWT_REFRESH_SECRET_KEY=' + secrets.token_urlsafe(32))"

# Example output:
# JWT_SECRET_KEY=A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8S9t0U1v2W3
# JWT_REFRESH_SECRET_KEY=X9y8Z7a6B5c4D3e2F1g0H1i2J3k4L5m6N7o8P9q0R1s2T3

# Save these securely (will add to Railway)
```

### Step 4: Create PostgreSQL Database on Railway

```bash
# In Railway dashboard:
# 1. Click "Create" → Add Service
# 2. Select "Postgres"
# 3. Select the created Postgres service
# 4. Go to "Variables" tab
# 5. Copy the DATABASE_URL value
# 6. Save for next step
```

### Step 5: Deploy Backend on Railway

```bash
# In Railway dashboard:
# 1. Click "Create" → Add Service
# 2. Select "GitHub Repo"
# 3. Authorize GitHub & select your repo
# 4. Select "rag-project" repo
# 5. Confirm deployment

# Configure environment variables:
# 1. Open deployed service
# 2. Go to "Variables" tab
# 3. Add all required variables:
```

**Railway Environment Variables to Add:**

```env
# Database (from PostgreSQL service)
DATABASE_URL=postgresql+asyncpg://...  # Copy from Postgres service

# JWT (use generated secrets from Step 3)
JWT_SECRET_KEY=<generated-secret-key>
JWT_REFRESH_SECRET_KEY=<generated-refresh-secret-key>

# LLM & Vector DB
GOOGLE_API_KEY=<your-google-api-key>
PINECONE_API_KEY=<your-pinecone-api-key>
PINECONE_INDEX_NAME=rag-project

# Email
RESEND_API_KEY=<your-resend-api-key>
SMTP_FROM_EMAIL=noreply@yourdomain.com
SMTP_FROM_NAME=RAG App

# CORS (update to your production domain)
CORS_ORIGINS=["https://your-frontend-url.railway.app", "https://yourdomain.com"]

# Rate Limiting (use memory since no Redis)
RATE_LIMIT_STORAGE=memory
RATE_LIMIT_ENABLED=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# App Settings
DEBUG=false
APP_NAME=RAG System
```

### Step 6: Deploy Frontend on Railway

```bash
# In Railway dashboard:
# 1. Click "Create" → Add Service
# 2. Select "GitHub Repo"
# 3. Select your repo again
# 4. Railway will auto-detect Next.js
# 5. Add environment variables:
```

**Frontend Environment Variables:**

```env
# Railway provides the backend URL automatically
# But you might need to set:
NEXT_PUBLIC_API_URL=https://your-backend.railway.app/api/v1
```

---

## Part 4: Verify Railway Deployment

### Check Deployment Status

```bash
# In Railway dashboard:
# 1. Click on Backend service
# 2. Go to "Logs" tab
# 3. Look for:
#    - "Application startup complete"
#    - No error messages

# 4. Go to "Deployments" tab
# 5. Check latest deployment status (should be "Success")
```

### Test Production Endpoints

```bash
# Get your Railway backend URL from dashboard
# Format: https://rag-project-production.railway.app

# Test health endpoint
curl https://rag-project-production.railway.app/health

# Test API docs
# Open in browser: https://rag-project-production.railway.app/docs
```

### Troubleshoot Production Issues

```bash
# View detailed logs
# In Dashboard → Service → Logs

# Check database connection
# In Dashboard → Postgres Service → Logs

# Check environment variables
# In Dashboard → Backend Service → Variables
# Verify all required variables are set
```

---

## Part 5: Continuous Deployment

After initial setup, Railway automatically redeploys on every push to main:

```bash
# Make code changes locally
git add .
git commit -m "Feature: Add new endpoint"

# Push to GitHub
git push origin main

# Railway automatically:
# 1. Detects the push
# 2. Rebuilds Docker image
# 3. Runs migrations (alembic upgrade head)
# 4. Deploys new version
# 5. Health checks pass before going live

# Monitor in Railway dashboard
# Services → Deployments → View logs
```

---

## Part 6: Monitoring & Maintenance

### Check Application Logs

```bash
# Backend logs (in Railway dashboard)
Services → Backend → Logs

# Check for:
# - ERROR messages (indicates failures)
# - Rate limit hits (normal under load)
# - Database connection issues
```

### Monitor Database

```bash
# In Railway dashboard:
# Services → PostgreSQL → Logs
# Check for connection errors or slow queries
```

### Scale Services (if needed)

```bash
# In Railway dashboard:
# Services → Backend → Settings
# Adjust:
# - RAM (increase if OOM errors)
# - CPU (increase if slow)
# - Replicas (add more instances behind load balancer)
```

---

## Troubleshooting Guide

### Issue: "Database connection refused"

**Local Fix:**
```bash
# Ensure PostgreSQL is running
docker ps | grep postgres

# Or restart PostgreSQL
docker start rag_postgres

# Check DATABASE_URL in .env
echo $DATABASE_URL
```

**Railway Fix:**
```bash
# Verify PostgreSQL service is running
# Check Variables tab → DATABASE_URL is correct
# Redeploy backend
```

### Issue: "Module not found" errors

```bash
# Local: Verify virtual environment is activated
which python  # Should show .venv path

# Or reinstall dependencies
uv sync

# Docker: Rebuild image
docker-compose build --no-cache
```

### Issue: Frontend can't reach backend

**Local:**
```bash
# Check CORS_ORIGINS in .env
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]

# Verify backend is running
curl http://localhost:8000/health
```

**Railway:**
```bash
# Update CORS_ORIGINS to include frontend domain
CORS_ORIGINS=["https://your-frontend.railway.app"]

# Redeploy backend
```

### Issue: Rate limiting blocks legitimate requests

```bash
# Check rate limit settings in .env
RATE_LIMIT_CHAT_REQUESTS=10        # requests per minute
RATE_LIMIT_CHAT_WINDOW_MINUTES=1

# Adjust limits if too strict
# For production, use Redis instead of memory storage
RATE_LIMIT_STORAGE=redis
REDIS_URL=redis://redis:6379/0
```

---

## Quick Reference Commands

### Local Development

```bash
# Start everything
.venv\Scripts\activate
python run.py  # Terminal 1: Backend
# Terminal 2:
cd frontend/rag-frontend && npm run dev  # Frontend

# Run tests
pytest tests/

# Database migrations
alembic upgrade head          # Apply
alembic downgrade -1          # Rollback one
alembic revision --autogenerate -m "description"
```

### Docker

```bash
# Full stack
docker-compose up -d
docker-compose down -v

# Individual service
docker-compose up -d postgres
docker-compose logs -f backend
```

### Git & Deployment

```bash
# Push to trigger Railway deployment
git add .
git commit -m "message"
git push origin main

# Check Railway logs
# Dashboard → Services → {name} → Logs
```

---

## Production Checklist

Before going live with real users:

- [ ] All API keys configured (Google, Pinecone, Resend)
- [ ] JWT secrets changed from defaults
- [ ] CORS_ORIGINS set to production domain
- [ ] Database backups configured
- [ ] Error logging configured
- [ ] Rate limits adjusted for expected load
- [ ] HTTPS enabled (Railway auto-enables)
- [ ] Health checks passing
- [ ] All environment variables set in Railway
- [ ] Tested full flow: Register → Upload → Chat

---

## Need Help?

- Railway Docs: https://docs.railway.app
- FastAPI Docs: https://fastapi.tiangolo.com
- PostgreSQL Docs: https://www.postgresql.org/docs
- Docker Docs: https://docs.docker.com
