# Complete Environment Variables Reference

Complete list of all environment variables for backend and frontend deployment.

## Backend (FastAPI) - Railway

### Essential (Required)
```env
# Database - SET BY RAILWAY AUTOMATICALLY
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/rag_db

# LLM Provider - PICK AT LEAST ONE
GOOGLE_API_KEY=your-api-key              # Gemini (free tier)
XAI_API_KEY=your-api-key                 # Grok (free trial)
OPENAI_API_KEY=your-api-key              # ChatGPT (paid)
ANTHROPIC_API_KEY=your-api-key           # Claude (paid)

# Vector Database
PINECONE_API_KEY=your-api-key
PINECONE_INDEX_NAME=rag-index
```

### JWT & Security (Generate Strong Random Values)
```env
JWT_SECRET_KEY=<generate: python -c "import secrets; print(secrets.token_urlsafe(32))">
JWT_REFRESH_SECRET_KEY=<generate: python -c "import secrets; print(secrets.token_urlsafe(32))">
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS - UPDATE WITH YOUR VERCEL DOMAIN
CORS_ORIGINS=["https://your-domain.vercel.app", "http://localhost:3000"]
CORS_CREDENTIALS=true
CORS_METHODS=["*"]
CORS_HEADERS=["*"]
```

### Application Configuration
```env
APP_NAME=RAG System
APP_VERSION=1.0.0
DEBUG=false
API_PREFIX=/api/v1
```

### Logging
```env
LOG_LEVEL=INFO          # DEBUG in development, INFO in production
LOG_FORMAT=json
```

### Rate Limiting (In-Memory - No Redis Needed)
```env
RATE_LIMIT_ENABLED=true
RATE_LIMIT_STORAGE=memory
RATE_LIMIT_CHAT_REQUESTS=10
RATE_LIMIT_CHAT_WINDOW_MINUTES=1
RATE_LIMIT_UPLOAD_REQUESTS=2
RATE_LIMIT_UPLOAD_WINDOW_MINUTES=10
RATE_LIMIT_AUTH_REQUESTS=5
RATE_LIMIT_AUTH_WINDOW_MINUTES=1
```

### LLM Model Configuration
```env
# Google Gemini
GEMINI_MODEL=gemini-2.0-flash
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_TOKENS=1024

# xAI Grok
GROK_MODEL=grok-3
GROK_TEMPERATURE=0.7
GROK_MAX_TOKENS=1024

# OpenAI
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=1024

# Anthropic Claude
CLAUDE_MODEL=claude-3-5-sonnet-20241022
CLAUDE_TEMPERATURE=0.7
CLAUDE_MAX_TOKENS=1024
```

### Pinecone Configuration
```env
PINECONE_API_KEY=your-api-key
PINECONE_INDEX_NAME=rag-index
PINECONE_ENVIRONMENT=                   # Optional
PINECONE_USE_NAMESPACES=true
```

### Embedding Model (Automatic - No Setup Needed)
```env
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
EMBEDDING_BATCH_SIZE=32
EMBEDDING_CACHE_ENABLED=true
```

### Document Processing
```env
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_FILE_SIZE_MB=10
ALLOWED_FILE_TYPES=[".pdf", ".docx", ".txt", ".json"]
ENABLE_OCR=false
```

### Storage Paths
```env
UPLOAD_DIR=data/uploads
DATA_DIR=data
CACHE_DIR=data/embeddings_cache
LOGS_DIR=logs
```

### Search Configuration
```env
DEFAULT_TOP_K=5
MIN_RELEVANCE_SCORE=0.5
ENABLE_HYBRID_SEARCH=true              # BM25 + semantic search (50/50)
```

### Email Service (Optional - For Password Reset)
```env
RESEND_API_KEY=re_your-api-key         # Free: 100 emails/day
SMTP_FROM_EMAIL=noreply@yourdomain.com
SMTP_FROM_NAME=RAG App
FRONTEND_URL=https://your-domain.vercel.app
```

### Database Connection Pool
```env
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_ECHO=false                          # Set to true for SQL debugging
```

### Optional: Local Ollama
```env
USE_OLLAMA=false
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

## Frontend (Next.js) - Vercel

### Required (Must start with NEXT_PUBLIC_)
```env
NEXT_PUBLIC_API_URL=https://your-railway-app.railway.app/api/v1
```

### Optional
```env
NEXT_PUBLIC_JWT_ALGORITHM=HS256
NEXT_PUBLIC_ACCESS_TOKEN_EXPIRY_MINUTES=30
NEXT_PUBLIC_REFRESH_TOKEN_EXPIRY_DAYS=7
```

## How to Generate JWT Secrets

```bash
# Option 1: Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Option 2: Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"

# Option 3: OpenSSL
openssl rand -base64 32
```

## Railway Dashboard Setup

1. **Create PostgreSQL Plugin**
   - Railway automatically sets `DATABASE_URL`
   - No manual configuration needed

2. **Add Variables**
   - Go to Variables tab
   - Add all variables from "Essential (Required)" above
   - Add your API keys

3. **Deploy**
   - Connect GitHub repo
   - Auto-deploys on push to main

## Vercel Dashboard Setup

1. **Create Project**
   - Import from GitHub
   - Select frontend path: `frontend/rag-frontend`

2. **Add Environment Variables**
   - Settings → Environment Variables
   - Add `NEXT_PUBLIC_API_URL`
   - Must include `NEXT_PUBLIC_` prefix

3. **Deploy**
   - Auto-deploys on push

## API Keys to Generate

| Service | Where | Cost | Free Tier |
|---------|-------|------|-----------|
| Gemini | https://ai.google.dev | Free | 60 req/min, 2M/month |
| Grok | https://console.x.ai | Free | Trial credits |
| Pinecone | https://www.pinecone.io | Free | 1 index, 1M vectors |
| Resend | https://resend.com | Free | 100 emails/day |
| OpenAI | https://platform.openai.com | Paid | None |
| Claude | https://console.anthropic.com | Paid | None |

## Environment Variable Validation

Backend validates:
- At least one LLM provider configured
- Pinecone API key present
- JWT secrets are set
- Database URL available (Railway)
- All paths are writable

Frontend requires:
- NEXT_PUBLIC_API_URL points to valid backend
- Backend CORS includes frontend domain

## Security Best Practices

1. **Never commit secrets to GitHub**
   - Use `.env` only locally
   - Commit `.env.example` instead

2. **Rotate JWT secrets periodically**
   - Generate new values every 3-6 months

3. **Use strong random values**
   - Min 256 bits for JWT secrets
   - Use cryptographic random generators

4. **Limit CORS origins**
   - Only include your frontend domain
   - Remove localhost from production

5. **Keep API keys confidential**
   - Use Railway/Vercel secret management
   - Never log or expose keys

## Troubleshooting

**Backend won't start - "Missing DATABASE_URL"**
- Solution: Add PostgreSQL plugin to Railway

**"No LLM providers configured"**
- Solution: Add at least one of: GOOGLE_API_KEY, XAI_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY

**Frontend can't reach API**
- Solution: Check NEXT_PUBLIC_API_URL matches Railway URL
- Solution: Check backend CORS includes frontend domain

**Rate limiting not working**
- Solution: Set RATE_LIMIT_STORAGE=memory (default)
- Note: In-memory storage is per-process, not global

**Documents can't be uploaded**
- Solution: Check Pinecone API key is valid
- Solution: Check Pinecone index name matches PINECONE_INDEX_NAME

**Password reset email not sending**
- Solution: Set RESEND_API_KEY
- Solution: Verify sender domain in Resend dashboard
