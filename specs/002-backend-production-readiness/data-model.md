# Data Model: Backend Improvements & Production Readiness

**Feature**: 002-backend-production-readiness
**Date**: 2026-01-02

## Overview

This document defines the data entities introduced or modified for production readiness features.

---

## New Entities

### PasswordResetToken

Secure token for password reset workflow.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| user_id | UUID | FK -> User.id, NOT NULL | Owner of the token |
| token_hash | String(255) | NOT NULL, UNIQUE | SHA-256 hash of the token |
| expires_at | DateTime | NOT NULL | Expiration time (created_at + 1 hour) |
| used_at | DateTime | NULL | When token was used (NULL if unused) |
| created_at | DateTime | NOT NULL, DEFAULT NOW | Creation timestamp |

**Indexes**:
- `idx_password_reset_token_hash` on `token_hash` (lookup by token)
- `idx_password_reset_user_id` on `user_id` (find tokens by user)

**Constraints**:
- Token is invalidated when `used_at` is set
- Previous tokens for same user are invalidated when new token created
- Token expires after 1 hour (per clarification)

**State Transitions**:
```
[Created] --> [Used] (user resets password)
[Created] --> [Expired] (time > expires_at)
[Created] --> [Invalidated] (new token requested)
```

---

### RequestLog

Audit log for API requests.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| request_id | String(36) | NOT NULL, UNIQUE | Correlation ID |
| endpoint | String(255) | NOT NULL | API path |
| method | String(10) | NOT NULL | HTTP method |
| user_id | UUID | FK -> User.id, NULL | Authenticated user (NULL if anon) |
| ip_address | String(45) | NULL | Client IP (IPv4/IPv6) |
| status_code | Integer | NOT NULL | HTTP response code |
| duration_ms | Float | NOT NULL | Request duration in milliseconds |
| error_type | String(50) | NULL | Error category if failed |
| created_at | DateTime | NOT NULL, DEFAULT NOW | Request timestamp |

**Indexes**:
- `idx_request_log_created_at` on `created_at` (time-based queries)
- `idx_request_log_user_id` on `user_id` (user activity)
- `idx_request_log_status_code` on `status_code` (error analysis)

**Retention**: 30 days (per clarification), then auto-deleted

---

### SystemMetric

Simple counter/gauge for monitoring.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| metric_name | String(100) | NOT NULL | Metric identifier |
| metric_type | Enum | NOT NULL | counter, gauge, histogram |
| value | Float | NOT NULL | Current value |
| labels | JSON | NULL | Dimensional labels |
| recorded_at | DateTime | NOT NULL, DEFAULT NOW | Measurement time |

**Metric Names**:
- `rate_limit_exceeded_total` (counter) - 429 responses
- `upload_failed_total` (counter) - Failed uploads
- `chat_queries_total` (counter) - Chat requests
- `active_users` (gauge) - Currently active users

**Indexes**:
- `idx_metric_name_recorded` on `(metric_name, recorded_at)`

---

## Modified Entities

### Document (existing)

Add field for BM25 index support.

| New Field | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| bm25_indexed | Boolean | NOT NULL, DEFAULT FALSE | Whether BM25 index is built |

---

### DocumentChunk (existing)

No schema changes. BM25 scoring computed at query time from existing `content` field.

---

### User (existing)

No schema changes. Password reset uses new `PasswordResetToken` entity.

---

## Relationships

```
User (1) ----< (N) PasswordResetToken
User (1) ----< (N) RequestLog (optional)
User (1) ----< (N) Document
Document (1) ----< (N) DocumentChunk
```

---

## Migration Plan

### Migration 1: Add PasswordResetToken table
```sql
CREATE TABLE password_reset_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_password_reset_token_hash ON password_reset_tokens(token_hash);
CREATE INDEX idx_password_reset_user_id ON password_reset_tokens(user_id);
```

### Migration 2: Add RequestLog table
```sql
CREATE TABLE request_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id VARCHAR(36) NOT NULL UNIQUE,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    ip_address VARCHAR(45),
    status_code INTEGER NOT NULL,
    duration_ms FLOAT NOT NULL,
    error_type VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_request_log_created_at ON request_logs(created_at);
CREATE INDEX idx_request_log_user_id ON request_logs(user_id);
CREATE INDEX idx_request_log_status_code ON request_logs(status_code);
```

### Migration 3: Add SystemMetric table
```sql
CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name VARCHAR(100) NOT NULL,
    metric_type VARCHAR(20) NOT NULL,
    value FLOAT NOT NULL,
    labels JSONB,
    recorded_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_metric_name_recorded ON system_metrics(metric_name, recorded_at);
```

### Migration 4: Add bm25_indexed to documents
```sql
ALTER TABLE documents ADD COLUMN bm25_indexed BOOLEAN NOT NULL DEFAULT FALSE;
```

---

## Validation Rules

### PasswordResetToken
- Token must be cryptographically random (32 bytes)
- Hash stored, not plaintext token
- Only one active token per user at a time

### RequestLog
- IP address validated as IPv4 or IPv6
- Duration must be positive
- Endpoint path sanitized (no query params with sensitive data)

### SystemMetric
- Metric name alphanumeric with underscores only
- Value must be finite number
- Labels must be valid JSON object
