# Data Model: API Rate Limiting & Abuse Protection

**Feature**: 001-api-rate-limiting
**Date**: 2026-01-01

## Overview

Rate limiting uses **ephemeral storage** (Redis/in-memory) for counters, not persistent database tables. This document defines the logical data structures used.

## Entities

### 1. RateLimitConfig

Configuration for rate limits per endpoint category.

| Field | Type | Description |
|-------|------|-------------|
| `category` | string | Endpoint category: `chat`, `upload`, `auth` |
| `requests` | integer | Max requests allowed in window |
| `window_seconds` | integer | Time window duration in seconds |
| `scope` | enum | `per_user` or `per_ip` |

**Default Values**:
```
chat:   { requests: 10, window_seconds: 60, scope: per_user }
upload: { requests: 2, window_seconds: 600, scope: per_user }
auth:   { requests: 5, window_seconds: 60, scope: per_ip }
```

**Environment Variables**:
```
RATE_LIMIT_CHAT_REQUESTS=10
RATE_LIMIT_CHAT_WINDOW=60
RATE_LIMIT_UPLOAD_REQUESTS=2
RATE_LIMIT_UPLOAD_WINDOW=600
RATE_LIMIT_AUTH_REQUESTS=5
RATE_LIMIT_AUTH_WINDOW=60
```

---

### 2. RateLimitCounter (Redis Key)

Ephemeral counter stored in Redis for tracking request counts.

**Key Pattern**:
```
rate_limit:{scope}:{identifier}:{endpoint}:{window_start}
```

**Examples**:
```
rate_limit:user:550e8400-e29b-41d4-a716-446655440000:chat:1704110400
rate_limit:ip:192.168.1.100:login:1704110400
```

| Field | Type | Description |
|-------|------|-------------|
| `scope` | string | `user` or `ip` |
| `identifier` | string | User UUID or IP address |
| `endpoint` | string | Endpoint category: `chat`, `upload`, `login`, etc. |
| `window_start` | integer | Unix timestamp of window start |

**Value**: Integer counter (atomic INCR operations)

**TTL**: Window duration + 10 seconds (auto-cleanup)

---

### 3. RateLimitState

Response state returned to clients.

| Field | Type | Description |
|-------|------|-------------|
| `limit` | integer | Maximum requests allowed |
| `remaining` | integer | Requests remaining in window |
| `reset` | integer | Unix timestamp when window resets |
| `retry_after` | integer | Seconds until retry (only on 429) |

**Mapped to Headers**:
```
X-RateLimit-Limit: {limit}
X-RateLimit-Remaining: {remaining}
X-RateLimit-Reset: {reset}
Retry-After: {retry_after}  # Only on 429 response
```

---

### 4. RateLimitEvent (Log Entry)

Structured log entry for rate limit events.

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | datetime | Event time (ISO 8601) |
| `event_type` | enum | `allowed`, `blocked`, `backend_error` |
| `endpoint` | string | Request path |
| `user_id` | string | User UUID (if authenticated) |
| `ip_address` | string | Client IP |
| `request_count` | integer | Current count in window |
| `limit` | integer | Configured limit |
| `window_reset` | integer | Unix timestamp of reset |

**Log Format** (JSON):
```json
{
  "timestamp": "2026-01-01T12:00:00Z",
  "event_type": "blocked",
  "endpoint": "/api/v1/rag/chat",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "ip_address": "192.168.1.100",
  "request_count": 11,
  "limit": 10,
  "window_reset": 1704110460
}
```

---

## Relationships

```
┌─────────────────────┐
│  RateLimitConfig    │ (env vars / config.py)
│  - category         │
│  - requests         │
│  - window_seconds   │
│  - scope            │
└─────────┬───────────┘
          │ configures
          ▼
┌─────────────────────┐
│  RateLimitCounter   │ (Redis key-value)
│  - identifier       │ ◄─── user_id or ip_address
│  - endpoint         │
│  - count (value)    │
└─────────┬───────────┘
          │ produces
          ▼
┌─────────────────────┐
│  RateLimitState     │ (response headers)
│  - limit            │
│  - remaining        │
│  - reset            │
└─────────┬───────────┘
          │ logged as
          ▼
┌─────────────────────┐
│  RateLimitEvent     │ (structured log)
│  - event_type       │
│  - context          │
└─────────────────────┘
```

---

## State Transitions

```
Request Received
      │
      ▼
┌─────────────────┐
│ Extract Key     │ (user_id or IP)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Get Counter     │ (Redis INCR)
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
 count ≤    count >
 limit      limit
    │         │
    ▼         ▼
 ALLOWED   BLOCKED
    │         │
    ▼         ▼
 Set        Return
 Headers    HTTP 429
    │         │
    ▼         ▼
 Continue   Log Event
 to Handler (warning)
```

---

## No Database Tables Required

Rate limiting uses **Redis only** for counter storage:
- Counters are ephemeral (auto-expire with TTL)
- No need for database migrations
- No impact on existing User/Document models
- Audit trail via structured logging (not database)

**Future Enhancement** (v2):
If persistent audit logging is needed, could add:
```sql
CREATE TABLE rate_limit_events (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    endpoint VARCHAR(255),
    event_type VARCHAR(50),
    request_count INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```
