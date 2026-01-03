# Deployment Guide - Railway (Backend) & Vercel (Frontend)

Complete guide to deploy RAG system to production.

## Backend Environment Variables - Railway

### Database
- `DATABASE_URL`: Set automatically by Railway PostgreSQL plugin

### API Configuration  
- `APP_NAME`: RAG System
- `DEBUG`: false
- `LOG_LEVEL`: INFO
- `LOG_FORMAT`: json
- `API_PREFIX`: /api/v1

### JWT Authentication
- `JWT_SECRET_KEY`: Generate strong random 256-bit string
- `JWT_REFRESH_SECRET_KEY`: Generate strong random 256-bit string
- `JWT_ALGORITHM`: HS256
- `ACCESS_TOKEN_EXPIRE_MINUTES`: 30
- `REFRESH_TOKEN_EXPIRE_DAYS`: 7

### CORS & Security
- `CORS_ORIGINS`: ["https://your-vercel-domain.com", "http://localhost:3000"]
- `CORS_CREDENTIALS`: true
- `CORS_METHODS`: ["*"]
- `CORS_HEADERS`: ["*"]

### Rate Limiting (Memory-based - no Redis needed)
- `RATE_LIMIT_ENABLED`: true
- `RATE_LIMIT_STORAGE`: memory
- `RATE_LIMIT_CHAT_REQUESTS`: 10
- `RATE_LIMIT_CHAT_WINDOW_MINUTES`: 1
- `RATE_LIMIT_UPLOAD_REQUESTS`: 2
- `RATE_LIMIT_UPLOAD_WINDOW_MINUTES`: 10
- `RATE_LIMIT_AUTH_REQUESTS`: 5
- `RATE_LIMIT_AUTH_WINDOW_MINUTES`: 1

### LLM Providers (Choose At Least ONE)

**Option 1: Google Gemini (Recommended - Free Tier)**
- `GOOGLE_API_KEY`: Get from https://ai.google.dev
- `GEMINI_MODEL`: gemini-2.0-flash
- `GEMINI_TEMPERATURE`: 0.7
- `GEMINI_MAX_TOKENS`: 1024

**Option 2: xAI Grok (Free Trial)**
- `XAI_API_KEY`: Get from https://console.x.ai
- `GROK_MODEL`: grok-3
- `GROK_TEMPERATURE`: 0.7
- `GROK_MAX_TOKENS`: 1024

**Option 3: OpenAI (Paid)**
- `OPENAI_API_KEY`: Get from https://platform.openai.com
- `OPENAI_MODEL`: gpt-4o-mini
- `OPENAI_TEMPERATURE`: 0.7
- `OPENAI_MAX_TOKENS`: 1024

**Option 4: Anthropic Claude (Paid)**
- `ANTHROPIC_API_KEY`: Get from https://console.anthropic.com
- `CLAUDE_MODEL`: claude-3-5-sonnet-20241022
- `CLAUDE_TEMPERATURE`: 0.7
- `CLAUDE_MAX_TOKENS`: 1024

### Vector Database (REQUIRED)
- `PINECONE_API_KEY`: Get from https://www.pinecone.io
- `PINECONE_INDEX_NAME`: rag-index
- `PINECONE_ENVIRONMENT`: (optional)
- `PINECONE_USE_NAMESPACES`: true

### Embeddings Model (Auto-downloaded, no config needed)
- Uses: sentence-transformers/all-MiniLM-L6-v2
- Dimension: 384
- Runs locally in container (~30MB)

### Email Service (Optional - for password reset)
- `RESEND_API_KEY`: Get from https://resend.com (100 free emails/day)
- `SMTP_FROM_EMAIL`: noreply@yourdomain.com
- `SMTP_FROM_NAME`: RAG App
- `FRONTEND_URL`: https://your-vercel-domain.com

### Logging
- `LOG_LEVEL`: INFO (set to DEBUG for development)
- `LOG_FORMAT`: json

## Frontend Environment Variables - Vercel

Add in Vercel dashboard (Settings → Environment Variables):

```env
NEXT_PUBLIC_API_URL=https://your-railway-app.railway.app/api/v1
NEXT_PUBLIC_JWT_ALGORITHM=HS256
NEXT_PUBLIC_ACCESS_TOKEN_EXPIRY_MINUTES=30
NEXT_PUBLIC_REFRESH_TOKEN_EXPIRY_DAYS=7
```

**⚠️ Important**: Frontend variables MUST start with `NEXT_PUBLIC_` to be accessible in browser.

## Deployment Steps

### 1. Railway Backend Setup

```bash
npm install -g @railway/cli
railway login
railway init
railway add          # Add PostgreSQL
```

### 2. Set Backend Environment Variables

In Railway dashboard:
- Copy all variables from "Backend Environment Variables" section above
- Generate random JWT secrets
- Add your API keys (Gemini OR Grok OR others)
- Add Pinecone API key

### 3. Deploy Backend

```bash
git push origin main    # Railway auto-deploys from GitHub
# OR
railway up              # Deploy with CLI
```

### 4. Get Railway URL
```bash
railway variables list  # Find RAILWAY_PUBLIC_DOMAIN
# Your API: https://[your-railway-app].railway.app
```

### 5. Create Vercel Project

- Go to https://vercel.com
- Import from GitHub → Select rag-project repo
- Select frontend path: `frontend/rag-frontend`
- Deploy

### 6. Set Frontend Environment Variables

In Vercel → Settings → Environment Variables:
```env
NEXT_PUBLIC_API_URL=https://your-railway-app.railway.app/api/v1
```

### 7. Update Backend CORS

In Railway dashboard, update:
```env
CORS_ORIGINS=["https://your-vercel-domain.vercel.app"]
```

## Service Setup Guides

### Pinecone Vector Database
1. Sign up: https://www.pinecone.io (free tier)
2. Create index:
   - Name: `rag-index`
   - Dimension: `384`
   - Metric: `cosine`
3. Copy API key

### Google Gemini (Free Tier)
1. Visit: https://ai.google.dev
2. Click "Get API Key"
3. Create new key
4. Free: 60 calls/min, 2M calls/month

### xAI Grok (Free Trial)
1. Visit: https://console.x.ai
2. Sign up
3. Generate API key
4. Includes initial free credits

### Resend Email (Optional)
1. Sign up: https://resend.com (free)
2. Verify sender email or domain
3. Copy API key
4. Free: 100 emails/day

## Cost Breakdown

| Service | Free Tier | Paid |
|---------|-----------|------|
| Railway App | - | ~$5/month |
| PostgreSQL | - | $9/month |
| Vercel | Full | Included |
| Pinecone | Free tier | Free |
| Gemini | 60req/min | Free |
| **Total** | - | ~$14/month |

**No Redis needed** - uses in-memory rate limiting (better for Railway costs)

## Verification Checklist

- [ ] Backend health check: `curl https://your-api/health`
- [ ] API docs: `https://your-api/docs`
- [ ] Frontend loads without errors
- [ ] Login/register works
- [ ] Can upload documents
- [ ] Can query documents
- [ ] Email sends password reset (if configured)
- [ ] JSON logs in Railway dashboard

## Troubleshooting

**Backend won't start:**
- Check DATABASE_URL is set
- Check all required LLM API keys
- Check logs: `railway logs`

**API connection fails:**
- Verify NEXT_PUBLIC_API_URL matches Railway URL
- Check CORS includes Vercel domain
- Test API: `curl https://your-api/health`

**LLM not generating answers:**
- Verify API key is correct
- Check provider has credits/quota
- Check rate limits

**Email not sending:**
- Verify RESEND_API_KEY
- Check sender domain verified
- Check Resend account has credits

**Database connection error:**
- Railway PostgreSQL plugin auto-creates DATABASE_URL
- Verify it's set: `railway variables list | grep DATABASE_URL`
