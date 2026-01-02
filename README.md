# RAG Document Intelligence Platform

A production-ready **Retrieval-Augmented Generation** system with multi-user authentication, real-time document processing, and AI-powered Q&A.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.119+-green.svg)
![Next.js](https://img.shields.io/badge/Next.js-15+-black.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

---

## Overview

Upload documents, ask questions in natural language, and get AI-generated answers with source citations. Built for multi-user environments with secure authentication and API rate limiting.

**Use Cases:**
- Enterprise knowledge bases
- Document Q&A systems
- Research paper analysis
- Educational platforms

---

## Features

| Feature | Description |
|---------|-------------|
| **Multi-User Auth** | JWT-based authentication with httpOnly cookies, auto-refresh tokens |
| **Document Processing** | PDF, DOCX, TXT, JSON with intelligent chunking (1000 chars, 200 overlap) |
| **Vector Search** | Pinecone integration with per-user namespace isolation |
| **AI Responses** | Google Gemini integration with source attribution |
| **Rate Limiting** | Configurable limits per endpoint (chat: 10/min, upload: 2/10min, auth: 5/min) |
| **Real-time Status** | Background processing with status tracking |
| **Chat History** | Persistent conversation sessions |

---

## Tech Stack

### Backend
| Technology | Purpose |
|------------|---------|
| FastAPI | Async REST API framework |
| PostgreSQL | User data, documents, chat history |
| SQLAlchemy | Async ORM with migrations (Alembic) |
| Pinecone | Vector similarity search |
| Sentence-Transformers | 384-dim embeddings (all-MiniLM-L6-v2) |
| Google Gemini | LLM for response generation |
| SlowAPI | Rate limiting with fail-open behavior |

### Frontend
| Technology | Purpose |
|------------|---------|
| Next.js 15 | React framework with App Router |
| TypeScript | Type-safe development |
| Tailwind CSS | Utility-first styling |
| Zustand | Lightweight state management |
| Axios | HTTP client with interceptors |

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Pinecone account (free tier works)
- Google AI API key

### 1. Clone & Setup Backend

```bash
git clone https://github.com/yourusername/rag-project.git
cd rag-project

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run database migrations
alembic upgrade head

# Start backend server
uvicorn rag.main:app --reload --port 8000
```

### 2. Setup Frontend

```bash
cd frontend/rag-frontend

npm install
npm run dev
```

### 3. Access the App

- **Frontend:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## Environment Configuration

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/rag_db

# Authentication
JWT_SECRET_KEY=your-secret-key
JWT_REFRESH_SECRET_KEY=your-refresh-secret

# Vector Database
PINECONE_API_KEY=your-pinecone-key
PINECONE_INDEX_NAME=rag-index

# LLM
GOOGLE_API_KEY=your-google-api-key

# Rate Limiting (optional)
RATE_LIMIT_STORAGE=memory
RATE_LIMIT_ENABLED=true
```

---

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Create account |
| POST | `/api/v1/auth/login` | Login (sets cookies) |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/logout` | Logout |
| GET | `/api/v1/auth/me` | Get current user |

### Documents & Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/rag/upload` | Upload document |
| GET | `/api/v1/rag/documents` | List user documents |
| DELETE | `/api/v1/rag/documents/{id}` | Delete document |
| POST | `/api/v1/rag/chat` | Ask question |
| GET | `/api/v1/rag/chat/history/{session}` | Get chat history |

---

## Project Structure

```
rag-project/
├── src/rag/                    # Backend
│   ├── api/v1/                 # API routes
│   │   ├── auth.py             # Auth endpoints
│   │   └── rag.py              # Document & chat endpoints
│   ├── core/                   # Core modules
│   │   ├── config.py           # Settings
│   │   ├── database.py         # Async PostgreSQL
│   │   ├── security.py         # JWT & hashing
│   │   └── rate_limiter.py     # Rate limiting
│   ├── services/               # Business logic
│   ├── models/                 # SQLAlchemy models
│   ├── schemas/                # Pydantic schemas
│   └── main.py                 # FastAPI app
├── frontend/rag-frontend/      # Next.js frontend
│   └── src/
│       ├── app/                # Pages (App Router)
│       ├── components/         # React components
│       └── lib/                # API client, hooks, store
├── tests/                      # Test suite
├── alembic/                    # Database migrations
└── specs/                      # Feature specifications
```

---

## Security Features

- **httpOnly Cookies:** Tokens never exposed to JavaScript
- **Rate Limiting:** Prevents abuse with configurable limits
- **Per-User Isolation:** Each user has separate Pinecone namespace
- **Password Hashing:** bcrypt with secure defaults
- **CORS Protection:** Configurable origins

---

## Rate Limits

| Endpoint | Limit | Key |
|----------|-------|-----|
| Chat | 10 requests/minute | User ID |
| Upload | 2 uploads/10 minutes | User ID |
| Login/Register | 5 attempts/minute | IP Address |

Returns `HTTP 429` with `Retry-After` header when exceeded.

---

## Development

```bash
# Run tests
pytest tests/ -v

# Run specific test
pytest tests/integration/test_rate_limits.py -v

# Database migration
alembic revision --autogenerate -m "description"
alembic upgrade head
```

---

## Deployment

### Railway / Render
1. Connect GitHub repository
2. Set environment variables
3. Add PostgreSQL addon
4. Deploy

### Docker (Coming Soon)
```bash
docker-compose up -d
```

---

## License

MIT License - see [LICENSE](LICENSE) file.

---

## Author

**Amna Akram**

- GitHub: [@Amna-05](https://github.com/Amna-05)
- Email: amnaaa963@gmail.com
