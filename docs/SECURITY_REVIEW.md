# NU_AI_CHAT_BOT — Web Application & Architecture Security Review

**Audit Date:** 2026-10-18  
**Scope:** Backend APIs (`backend/api/`), Database Stores (`db/`), Token Service (`token_service/`), UI Interfaces (`static/`), and Deployment Boundaries.  
**Classification:** Internal Technical Architecture Document

---

## 1. Executive Summary

A comprehensive source-code and architectural security review was conducted on the National University of Bangladesh AI Assistant (`NU_AI_CHAT_BOT`). The system architecture was evaluated against the OWASP Top 10 API Security Risks, Institutional Student Privacy standards, and Role-Based Access Control (RBAC) mandates.

---

## 2. Threat Model & RBAC Boundaries

The system enforces three distinct trust tiers:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Public Student & Guest Tier (Zero Trust)                 │
│    - Accessible Endpoints: /chat, /widget, /api/v1/chat     │
│    - Allowed Actions: Academic Q&A, Token Tracking, Notices │
│    - Restricted: Zero access to Admin APIs or DB files      │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│ 2. Department Solver Tier (Least Privilege)                 │
│    - Role: Solvers (Accounts Desk, ICT Team, etc.)          │
│    - Allowed Actions: Solve or Send Back to Admin only       │
│    - Restricted: CANNOT reassign tokens; CANNOT see other   │
│      department desks; CANNOT access System Maintenance     │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│ 3. Super Admin Tier (Full Governance)                       │
│    - Access: /admin workspace with Bearer Token / Session   │
│    - Allowed Actions: Token re-assignment, User management, │
│      Sync & Maintain, Soft-delete / Restore, System Backup   │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Security Domains Evaluated

### 3.1 Authentication & Credential Storage
- **Admin & Solver Auth:** Password verification utilizes standard salted SHA-256 / PBKDF2 hashing via `token_service/service.py`. Plaintext passwords are never stored in `nu_tokens.db`.
- **API Keys & Secrets:** External credentials (e.g., `GEMINI_API_KEY`) are managed via environment variables (`.env`) loaded at startup through Pydantic `BaseSettings`. Keys are strictly excluded from client responses and Git tracking.

### 3.2 Role-Based Access Control (RBAC) Enforcement
- Solvers are strictly scoped by `department_id` / `solver_id`.
- The solver endpoint enforces that solvers can only view tokens assigned to their desk and restricts actions to `Solve` or `Send Back to Admin (Not Solved)`. Solvers are barred from mutating status to `CLOSED` or reassigning to arbitrary departments.
- Trash bin recovery and permanent deletion are exclusively restricted to Super Admin privileges.

### 3.3 SQL Injection & Data Sanitization
- All database interactions in `db/sql_store.py`, `token_service/service.py`, and `backend/core/database.py` use strictly parameterized queries (`?` placeholders for SQLite / `%s` for PostgreSQL adapters).
- User input models are validated through Pydantic schemas (`ChatRequest`, `TokenCreateRequest`), rejecting malformed JSON payloads.

### 3.4 Rate Limiting & Abuse Prevention
- The API is equipped with `InMemoryRateLimiter`, configurable via the `RATE_LIMIT_PER_MINUTE` environment variable (default: 120 rpm).
- Both `/api/chat` and `/api/v1/chat` extract client IPs with `X-Forwarded-For` header support, ensuring fair rate limiting behind campus proxies while preventing denial-of-service from automated query scrapers.

### 3.5 Student Privacy & PII Masking
- Solved cases indexed into ChromaDB for similarity searching (`NU_SIMILARITY_SERVICE`) are anonymized prior to vector embedding. Student names, personal phone numbers, and registration IDs are stripped, preserving only problem-resolution archetypes.

### 3.6 Backup & File Security
- The system backup service (`/api/v1/admin/backup`) writes timestamped ZIP archives containing database state. Path traversal vulnerabilities (`../../`) are blocked by validating destination filenames and using strict directory sandboxing under `data/backups/`.

---

## 4. Residual Risks & Production Recommendations

| Risk Area | Severity | Current Mitigation | Production Action Required |
|---|:---:|---|---|
| In-Memory Rate Limiter | Low | IP-based sliding window in memory | In multi-instance cluster, switch to Redis distributed rate limiter. |
| Transport Layer Security | Medium | Local HTTP during development | Front with Nginx reverse proxy enforcing TLS 1.3 / HTTPS and HSTS headers. |
| SQLite Concurrency Locks | Low | WAL mode + 30s busy timeout | For > 1,000 concurrent active write operations, migrate to PostgreSQL 16. |
| Admin Session Storage | Low | Stateless bearer token / auth header | Implement short-lived JWTs with Redis token revocation list. |
