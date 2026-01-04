
# constitution.md

## 1. Product Vision

We are building a **multi-user, production-ready RAG APP** for small teams.

Core promise:
**“Upload documents, ask questions, and get reliable answers — without worrying about models, infrastructure, or failures.”**

Why:

* Small teams want private, searchable knowledge without ML complexity
* Reliability and usability matter more than cutting-edge novelty
* The system must be easy to fork, customize, and deploy for clients

---

## 2. System Scope

This system supports:

* Multiple users (JWT-based auth) http Only cookies 
* Multiple document formats (`.pdf`, `.doc/.docx`, `.txt`)
* Local file storage (initial phase)
* Vector search using Pinecone
* Multiple LLM providers with fallback
* Chat + history per user
* API-first backend
* SaaS-style frontend UI

Target scale:

* Small teams (5–50 users per tenant, even if tenancy is logical)

---

## 3. Architecture Patterns (Non-Negotiable)

### Backend Architecture

* FastAPI application
* Layered architecture only:

  ```
  router → service → repository → database
  ```
* No business logic in routers
* No database access outside repositories
* Dependency Injection everywhere

### Data Layer

* PostgreSQL as primary database
* SQLAlchemy ORM
* Alembic for migrations
* Explicit transaction boundaries

### AI / RAG Layer

* Document ingestion → chunking → embedding → vector storage
* Retrieval isolated as a service
* LLM calls isolated behind provider interfaces
* Model fallback handled at service layer
* separate Namespace per user in Pinecone
Why:
Consistency, testability, and safe AI behavior.

---

## 4. Technology Stack (Locked)

### Backend

* Python 3.12+
* FastAPI
* SQLAlchemy
* Alembic
* Pydantic
* JWT authentication

### AI / ML

* Sentence-Transformers (Hugging Face) for embeddings
* Pinecone for vector storage
* Multiple LLM providers (Groq / OpenAI / others)
* Provider-agnostic interface

### Frontend

* Next.js (App Router) >15+ version 
* TypeScript
* Tailwind CSS ,shadcn UI 
* Dark + Light theme support
* API-driven state

### Infrastructure

* Docker
* Docker Compose
* Railway (initial deployment)
* Local disk storage (for documents)

### Testing

* Pytest
* HTTPX for API tests
* Test containers or isolated test DB

---

## 5. Security Rules (Non-Negotiable)

* Passwords:

  * Hashed using bcrypt 
  * Never logged
* Authentication:

  * JWT access tokens (short-lived) >15 mins
  * Token validation on every protected endpoint
* Secrets:

  * No secrets in code
  * Environment variables only
* File uploads:

  * Validate file type
  * Enforce size limits > for now 10MB >goal to increase it 
  * Store with sanitized filenames
* Authorization:

  * Users can only access their own documents and chats

---

## 6. Reliability & Failure Handling

* LLM failures must not crash requests
* Model fallback must activate automatically
* Partial failures must return meaningful errors
* No silent failures

If AI fails:

* Return a clear error message
* Log failure with provider + reason
* Preserve system stability

## 6.1 API Rate Limiting & Abuse Protection

All externally exposed endpoints MUST be rate-limited.

Mandatory rules:

* Rate limiting is enforced per authenticated user
* For unauthenticated endpoints, rate limiting is per IP
* Exceeding limits MUST return HTTP 429 with a retry-after hint
* Rate limiting failures MUST NOT crash the system

Minimum required limits (initial defaults):

* Authentication endpoints: low burst tolerance
* File upload endpoints: strict limits
* Chat / LLM endpoints: strict limits due to cost

Failure behavior:

* If the rate-limiting backend (e.g., Redis) is unavailable, the system MUST fail 
* open but log a warning

## 7. Logging & Monitoring (Required)

### Logging

* Structured logging (JSON preferred)
* Log levels:

  * INFO: normal operations
  * WARNING: recoverable issues
  * ERROR: failures
* Never log:

  * Tokens
  * User content verbatim (unless debug mode)Additional rules:
* Every request MUST include a correlation/request ID
* Logs MUST include:
  * Endpoint name
  * User ID (if authenticated)
  * Error category (validation, auth, dependency, internal)
* AI provider failures MUST be logged with provider name and reason


## 7.1 Cost & Resource Safeguards (AI-Specific)

The system MUST enforce safeguards to prevent uncontrolled cost growth.

Mandatory limits:

* Maximum tokens per LLM request
* Maximum messages per conversation
* Maximum document size and chunk count

Behavior:

* Requests exceeding limits MUST fail gracefully
* Users MUST receive clear error messages
* No silent truncation of user input*

### Monitoring

* Health check endpoint (`/health`)
* Track:

  * API error rates
  * LLM provider failures
  * Document ingestion failures
* Prepared for future tools (Sentry, OpenTelemetry)

---

## 8. Testing & Quality Standards

### Backend Tests

* Unit tests:

  * Services
  * Repositories
  * Chunking logic
* Integration tests:

  * Auth flows
  * File upload
  * Chat endpoints
* Tests must be deterministic
* No real LLM calls in tests (mock providers)

### Quality Rules

* Type hints everywhere
* Clear error responses
* No endpoint considered “done” without tests
  
## 8.1 AI Determinism & Testing Boundaries

AI-dependent behavior MUST be explicitly categorized as:

* Deterministic (unit-testable)
* Probabilistic (mocked in tests)

Rules:
All LLM providers MUST be mocked in unit tests

* Integration tests with real providers are optional and explicitly marked
* Tests MUST NOT assert on exact LLM text output
* No flaky or non-deterministic tests are acceptable
  
## 8.2 Mandatory Test Coverage Rules

Every feature MUST include:

* At least one unit test
* At least one integration test (if external systems involved)

Critical flows that MUST have integration tests:

* Authentication
* File upload and deletion
* Document ingestion
* Chat request lifecycle


## 9. Configuration & Environment Rules

All configuration via environment variables:

Examples:

* `DATABASE_URL`
* `JWT_SECRET`
* `PINECONE_API_KEY`
* `LLM_PROVIDER_KEYS`
* `ENVIRONMENT=dev|prod`

Rules:

* `.env.example` must exist
* No default secrets
* Fail fast if required vars missing
Additional rules:
* Application MUST fail fast if required environment variables are missing
* `.env.example` MUST list all required variables
* No environment-specific logic hardcoded in application code


## 9.1 Data Lifecycle & Cleanup Guarantees

Data consistency MUST be maintained across storage layers.

Rules:
Deleting a document MUST:
 
* Remove the file from disk
* Remove vector embeddings
* Remove metadata references
* Partial failures MUST be detectable and recoverable
* Orphaned vectors or files MUST NOT exist

---

## 10. Docker & Deployment Rules

### Docker

* Single Dockerfile for backend
* Slim base image
* Non-root user
* Explicit dependency versions

### Docker Compose

* Services:

  * Backend
  * PostgreSQL
* Local dev parity with production

### Deployment

* Database migrations must run before app start
* Health check used for readiness
* Logs written to stdout/stderr


## 11. Frontend UI & UX Constitution

### UI Goals

* SaaS-quality look and feel
* Clean, minimal, professional
* Dark theme first, light theme supported
* Responsive design

### Required Frontend Features

* Landing page:

  * Product value
  * Features
  * Call-to-action
* Auth:

  * Login
  * Register
  * Logout
* Dashboard:

  * Document upload
  * Document list
  * Chat interface
* Chat UI:

  * Message history
  * Loading states
  * Error states
* Profile:

  * Model preference
  * Basic user settings

### UX Rules

* Always show loading indicators
* Always handle empty states
* Clear error messages
* No broken or dead UI paths

## 11.1 Frontend Reliability & UX Rules

Frontend MUST:

* Handle loading, empty, and error states for all views
* Prevent duplicate submissions
* Clearly surface backend errors to users
* Never assume backend success

Frontend MUST NOT:

* Encode business rules
* Trust unvalidated backend data


## 12. Redis Caching (Guidance)

Redis is **optional but recommended**.

Use Redis for:

* Auth token metadata
* Rate limiting
* Caching frequently accessed metadata
* Short-lived chat/session state

Do NOT use Redis for:

* Primary data storage
* Vector embeddings

Decision rule:

* Implement Redis **after** deployment if performance demands it


## 13. README.md Requirements

README must include:

* Project overview
* Architecture explanation
* Tech stack
* Environment setup
* Running locally (Docker + non-Docker)
* Testing instructions
* Deployment notes

README is part of the product.

## 14. Explicit Non-Goals

* Perfect LLM answers
* Real-time collaboration
* Multi-region deployment
* Kubernetes (for now)
* Enterprise-grade compliance (HIPAA, SOC2)


## 15. Decision Bias

When uncertain:

1. Prefer clarity over cleverness
2. Prefer reliability over optimization
3. Prefer shipping over polishing
4. Prefer explicit specs over assumptions


## 16. Enforcement

Any new feature or change must:

* Respect this constitution
* Declare deviations explicitly
* Be spec’d before implementation
Additional enforcement:
* No feature may be merged without:
  *Defined rate limits
  *Defined error behavior
  *Associated tests
 Deviations from this constitution MUST be documented explicitly
