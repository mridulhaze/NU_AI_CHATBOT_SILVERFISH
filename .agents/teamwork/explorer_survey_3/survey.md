# Comprehensive Domain Logic, Backend APIs, Access Controls & Test Suite Survey

**Date:** 2026-10-21  
**Project:** National University Bangladesh AI Assistant (`D:\projects\AI_CHAT_BOT`)  
**Investigator:** Explorer 3 (`teamwork_preview_explorer`)  
**Scope:** Backend Routes, Domain Services, SQLite Models, RBAC Access Controls, and Test Suite Baselines for UI Redesign

---

## 1. Executive Summary

This survey provides a technical baseline for redesigning the **Administrative & Solver Support Center** in `static/index.html` and the **FAQ Panel** in `static/chat.html`. The goal is to transition the interfaces to an Apple/Linear-inspired monochromatic design while preserving 100% of the backend domain logic, SQLite schemas, role hierarchies, official portal links, and API contracts.

### Key Conclusions:
- **Baseline Test Verification:** Both target test suites (`tests/test_token_service_domain.py` and `tests/test_faq_forum.py`) pass 100% (10 tests total: 4 domain + 6 FAQ forum, 0 failures). Additional security and backup test suites (`test_security_rbac.py`, `test_backup_and_delete.py`) also pass 100%.
- **Dual SQLite Architecture:** The system relies on two separate SQLite databases: `data/nu_tokens.db` (tokens, solvers, users, audit logs) and `data/nu_assistant.db` (FAQs, academic schedules, RAG knowledge base).
- **Strict Solver Isolation:** Solvers belong to a specific department desk and are strictly constrained to viewing their desk's tokens, executing only two actions (`Solve` or `Send Back to Admin`), and viewing only the `Token Support Center` tab. Reassignment is forbidden both at the API level (HTTP 403) and UI level.
- **Official Portals:** All system responses and UI links must strictly point to verified active portals (`http://103.113.200.68/nu-app/`, `http://app11.nu.edu.bd/`, `http://ems.nu.ac.bd/`) and avoid deprecated legacy domains (`services.nu.edu.bd`, `103.113.200.36`).

---

## 2. Test Suite Baseline & Verification Status

Tests were verified using Python 3.14.0 (`C:\Python314\python.exe`) on Windows.

| Test File | Total Tests | Passed | Failed | Status | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `tests/test_token_service_domain.py` | 4 | 4 | 0 | **100% PASSED** | Validates atomic ID sequence (`NU-YYYY-NNNNNN`), PII protection in public status, state machine transitions, and solver "Return to Admin" workflow. |
| `tests/test_faq_forum.py` | 6 | 6 | 0 | **100% PASSED** | Validates `FAQ/faq.txt` parsing (650+ items, 20+ categories), idempotent sync, listing/filtering/search, atomic like toggle with duplicate prevention, and top-liked endpoints. |
| `tests/test_security_rbac.py` | 2 | 2 | 0 | **100% PASSED** | Validates PBKDF2 password hashing and JWT token creation/decoding. |
| `tests/test_backup_and_delete.py` | 3 | 3 | 0 | **100% PASSED** | Validates Super Admin full backup creation, soft-delete to trash (`is_deleted=1`), restore (`is_deleted=0`), and ZIP restore roundtrip. |

### Environment Dependency Resolution:
During initial test execution, several runtime dependencies were missing from the Python 3.14 environment. These were installed into the user environment without modifying any application or test source code:
- `sqlalchemy` (v2.1.5)
- `langchain-core` (v1.6.12)
- `langchain-text-splitters` (v1.1.3), `langchain-community` (v0.4.2), `langchain` (v1.4.6)
- `langchain-chroma` (v1.1.0), `chromadb` (v1.5.9)
- `langchain-google-genai` (v4.4.2), `google-genai` (v2.32.0)

Both required suites now execute and pass cleanly:
```powershell
python -m pytest tests/test_token_service_domain.py -v   # 4 passed in 7.51s
python -m pytest tests/test_faq_forum.py -v              # 6 passed in 20.81s
```

---

## 3. Verified Official URLs & Strict Constraints

As documented in `AGENTS.md` and `AGENTIC_ARCHITECTURE.md`, any UI or assistant response must strictly preserve these URLs:

| Service / Portal | Correct Verified URL | Forbidden Deprecated Links |
| :--- | :--- | :--- |
| **Student Online Services (ERP)** (TC, Certificate, Marksheet, Transcript, Correction) | `http://103.113.200.68/nu-app/` | `http://services.nu.edu.bd/`<br>`http://103.113.200.36/` |
| **Online Admission Portal** (Honours, Degree, Masters) | `http://app11.nu.edu.bd/` | |
| **Examination Management System (EMS)** | `http://ems.nu.ac.bd/` | |
| **Form Fill-up & Registration (App1)** | `http://app1.nu.edu.bd/` | |
| **Official University Main Portal** | `http://www.nu.ac.bd/` | |
| **Sonali Seba Online Payment Gateway** | `https://sblepay.sonalibank.com.bd/` | |

---

## 4. SQLite Database Architecture & Schemas

### 4.1. `data/nu_tokens.db` (Support Token Operations)

1. **`token_requests` Table:**
   - `id` (INTEGER PRIMARY KEY)
   - `token_id` (TEXT UNIQUE): Format `NU-YYYY-NNNNNN` (e.g. `NU-2026-000196`)
   - `service_type` (TEXT): Service code (e.g. `FORM_FILLUP`, `EMS`, `TC`, `CERTIFICATE`, `ACCOUNTS`, `OTHER`)
   - `problem` (TEXT): Problem description
   - `user_id` (INTEGER/TEXT), `user_name` (TEXT), `user_email` (TEXT), `user_phone` (TEXT)
   - `registration_no` (TEXT), `college_code` (TEXT)
   - `status` (TEXT): `PENDING`, `ASSIGNED`, `PROCESSING`, `SOLVED`, `CLOSED`, `REJECTED`
   - `priority` (TEXT): `NORMAL`, `URGENT`
   - `solver_id` (INTEGER REFERENCES `token_solvers(id)`)
   - `solver_name` (TEXT): Assigned desk/officer name
   - `solve_message` (TEXT): Detailed resolution text provided when solved
   - `created_date`, `updated_date`, `solved_date`, `estimated_solve_date` (TEXT)
   - `admin_note` (TEXT): Internal handover notes
   - `is_deleted` (INTEGER DEFAULT 0): Soft-delete flag for Super Admin trash bin
   - `deleted_at` (TEXT): Timestamp when moved to trash

2. **`token_solvers` Table:**
   - `id` (INTEGER PRIMARY KEY)
   - `solver_name` (TEXT): Desk title (e.g., `Accounts & Sonali Seba Desk`, `ICT Support Team`)
   - `department` (TEXT): Department name
   - `email` (TEXT), `phone` (TEXT), `active` (INTEGER DEFAULT 1)

3. **`token_history` Table:**
   - `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
   - `token_id` (TEXT), `old_status` (TEXT), `new_status` (TEXT), `changed_by` (TEXT), `message` (TEXT), `created_date` (TEXT)

4. **`token_sequences` Table:**
   - `year` (INTEGER PRIMARY KEY), `last_seq` (INTEGER DEFAULT 0) — Atomic concurrency-safe counter.

5. **`users` Table:**
   - `id` (INTEGER PRIMARY KEY), `username` (TEXT UNIQUE), `email` (TEXT), `password_hash` (TEXT), `full_name` (TEXT), `department` (TEXT), `role` (`SUPER_ADMIN`, `ADMIN`, `SOLVER`, `USER`), `active` (INTEGER DEFAULT 1), `created_at` (TEXT)

6. **`audit_logs` Table:**
   - `id` (INTEGER PRIMARY KEY), `timestamp` (TEXT), `action` (TEXT), `username` (TEXT), `role` (TEXT), `resource_type` (TEXT), `resource_id` (TEXT), `success` (INTEGER), `details_json` (TEXT)

---

### 4.2. `data/nu_assistant.db` (Knowledge Base & FAQ Forum)

1. **`faq_entries` Table:**
   - `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
   - `question` (TEXT NOT NULL), `answer` (TEXT NOT NULL), `category` (TEXT NOT NULL)
   - `source_key` (TEXT UNIQUE), `keywords` (TEXT), `source_file` (TEXT DEFAULT 'FAQ/faq.txt')
   - `likes_count` (INTEGER DEFAULT 0), `is_active` (INTEGER DEFAULT 1)
   - `created_at`, `updated_at` (DATETIME)

2. **`faq_likes` Table:**
   - `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
   - `faq_id` (INTEGER NOT NULL REFERENCES `faq_entries(id)` ON DELETE CASCADE)
   - `session_id` (TEXT NOT NULL)
   - `created_at` (DATETIME DEFAULT CURRENT_TIMESTAMP)
   - Unique constraint: `UNIQUE(faq_id, session_id)` ensures idempotent, single-like per session.

3. **`academic_exam_information` Table:**
   - Stores program types (`Honours`, `Degree Pass`, `Master's`, `Professional`), exam year, part/semester, exam routines, result dates, and verification links.

---

## 5. Role-Based Access Control (RBAC) & Solver Isolation Rules

### 5.1. Role Hierarchy
Defined in `backend/core/security.py`:
- `USER` (Level 1): Public student/staff access (create token, view verification slip, check status, browse/like FAQs).
- `SOLVER` (Level 2): Department desk solver.
- `ADMIN` (Level 3): Department administrator.
- `SUPER_ADMIN` (Level 4): System superadministrator.

### 5.2. Mandatory Solver Isolation Rules
1. **Department Isolation:**
   - In `backend/api/admin_routes.py` (lines 66-94) and `token_service/routes.py` (lines 136-149): When a user with role `SOLVER` queries tokens, the query enforces:
     ```sql
     AND (solver_id IN (...) OR solver_name IN (...) OR solver_name LIKE '%<dept>%')
     ```
   - Solvers can NEVER see tokens assigned to other departments (e.g., Accounts solver cannot see EMS tokens).
2. **Tab Visibility Restriction:**
   - In `static/index.html` (lines 5422-5439): If `user.role === 'SOLVER'`, all administrative tabs (`sitemap`, `ai_engine`, `qa_knowledge`, `academic_static`, `users`, `logs`, `backups`) are strictly hidden and disabled. Solvers ONLY see the `Token Support Center` (`tokens`) tab.
3. **Solver 2-Action Workflow:**
   - **Action 1 (Solve Token):** `POST /api/token/admin/{token_id}/solve` (or `/api/v1/admin/tokens/{token_id}/solve`)
     - Transitions status to `SOLVED`.
     - Requires non-empty resolution text (`solve_message`).
     - Triggers automatic vector indexing of anonymized solution.
   - **Action 2 (Send Back to Admin - Not Solved):** `POST /api/token/admin/{token_id}/return-to-admin` (or `/api/v1/admin/tokens/{token_id}/return-to-admin`)
     - Transitions status back to `PENDING`.
     - Appends reason to `admin_note`: `[Returned to Admin by {solver} on {date} (Reason: {reason})]`.
     - Logs history entry: `Sent back to Admin (Not Solved): {reason}`.
4. **Reassignment Prohibition:**
   - `POST /api/v1/admin/tokens/{token_id}/assign` requires `[Role.ADMIN, Role.SUPER_ADMIN]`. Any attempt by a `SOLVER` returns `403 Forbidden`.
   - In UI: Reassignment dropdowns and controls MUST BE HIDDEN or rendered as a read-only badge (`Assigned Desk: {solver_name}`) when `isSolver` is true.

### 5.3. Super Admin & Admin Capabilities
- **ADMIN:** Can assign/reassign solvers, update token status, manage users, view audit logs.
- **SUPER_ADMIN:** Full access across all departments, user deletion, full system backup creation (`POST /api/v1/admin/backup/create`), system restoration (`POST /api/v1/admin/backup/restore`), and soft-delete/restore tokens from trash (`POST /api/token/admin/{token_id}/delete` and `.../restore`).

---

## 6. Token State Machine Transitions

Defined in `backend/services/token_service.py`:

```
                 ┌────────────────────────────────────────────────────────┐
                 │                                                        │
                 ▼                                                        │
           ┌───────────┐      assign_solver       ┌────────────┐          │
           │  PENDING  ├─────────────────────────►│  ASSIGNED  │          │
           └─────┬─────┘                          └─────┬──────┘          │
                 │                                      │                 │
                 │ (processing)                         │ (processing)    │
                 ▼                                      ▼                 │
           ┌────────────┐     solve_token         ┌────────────┐          │
           │ PROCESSING ├────────────────────────►│   SOLVED   │          │
           └─────┬──────┘                         └─────┬──────┘          │
                 │                                      │                 │
                 │ (return-to-admin)                    │ (closed)        │
                 ├──────────────────────────────────────┘                 │
                 │                                                        │
                 ▼                                                        │
           ┌────────────┐                                                 │
           │  REJECTED  ├─────────────────────────────────────────────────┘
           └────────────┘ (re-open to PENDING only)
```

- Allowed Transitions (`VALID_TRANSITIONS`):
  - `PENDING` -> `ASSIGNED`, `PROCESSING`, `REJECTED`
  - `ASSIGNED` -> `PROCESSING`, `REJECTED`, `PENDING`
  - `PROCESSING` -> `SOLVED`, `ASSIGNED`, `REJECTED`, `PENDING`
  - `SOLVED` -> `CLOSED`, `PROCESSING`
  - `REJECTED` -> `PENDING`
  - `CLOSED` -> None (Terminal state, cannot transition back unless Super Admin)

---

## 7. Backend API Contracts That UI Redesign Must Strictly Preserve

### 7.1. Support Center (Token Management) Endpoints

#### 1. List Tokens:
- **Route:** `GET /api/token/admin/tokens` (and `GET /api/v1/admin/tokens`)
- **Query Params:**
  - `limit`: int (default 100, max 500)
  - `offset`: int (default 0)
  - `search`: string (optional, searches `token_id`, `problem`, `user_name`, `registration_no`)
  - `status`: string (optional: `PENDING`, `ASSIGNED`, `PROCESSING`, `SOLVED`, `CLOSED`, `REJECTED`)
  - `service_type`: string (optional: `FORM_FILLUP`, `EMS`, `TC`, etc.)
  - `department`: string (optional, for solver isolation)
  - `solver_name`: string (optional)
  - `role`: string (optional, `SOLVER`, `ADMIN`, `SUPER_ADMIN`)
- **Headers:** `Authorization: Bearer <JWT_TOKEN>`
- **Response Shape:**
  ```json
  {
    "success": true,
    "total": 42,
    "limit": 100,
    "offset": 0,
    "tokens": [
      {
        "id": 1,
        "token_id": "NU-2026-000001",
        "service_type": "EMS",
        "service_name": "Examination Management System",
        "problem": "Cannot login to student EMS dashboard",
        "status": "PENDING",
        "priority": "NORMAL",
        "user_name": "Rahim Uddin",
        "user_phone": "01700000000",
        "registration_no": "1920000000",
        "college_code": "0601",
        "solver_id": 1,
        "solver_name": "ICT Support Team",
        "solve_message": null,
        "admin_note": null,
        "created_date": "2026-08-10 14:30:00",
        "updated_date": "2026-08-10 14:30:00",
        "solved_date": null,
        "is_deleted": 0
      }
    ]
  }
  ```

#### 2. Get Single Token Detail:
- **Route:** `GET /api/token/admin/{token_id}`
- **Response Shape:**
  Returns full `TokenAdminDetailResponse` including contact info, service code, solver ID, notes, and full history array.

#### 3. Solver: Solve Token:
- **Route:** `POST /api/token/admin/{token_id}/solve` (or `/api/v1/admin/tokens/{token_id}/solve`)
- **Headers:** `Content-Type: application/json`, `Authorization: Bearer <token>`
- **Request Body:**
  ```json
  {
    "solve_message": "Resolution text describing how problem was fixed.",
    "solver_name": "ICT Support Team",
    "admin_note": "Optional internal note"
  }
  ```
- **Response:** `{"success": true, "message": "Token NU-2026-000001 marked as SOLVED..."}`

#### 4. Solver: Send Back to Admin (Not Solved):
- **Route:** `POST /api/token/admin/{token_id}/return-to-admin` (or `/api/v1/admin/tokens/{token_id}/return-to-admin`)
- **Headers:** `Content-Type: application/json`, `Authorization: Bearer <token>`
- **Request Body:**
  ```json
  {
    "reason": "Clear explanation why this requires admin instruction or re-assignment.",
    "solver_name": "ICT Support Team"
  }
  ```
- **Response:** `{"success": true, "message": "Token NU-2026-000001 sent back to Admin..."}`

#### 5. Admin: Update Status:
- **Route:** `POST /api/token/admin/{token_id}/status`
- **Request Body:**
  ```json
  {
    "status": "PROCESSING",
    "message": "Status change message",
    "admin_note": "Internal note"
  }
  ```

#### 6. Admin: Assign Solver:
- **Route:** `POST /api/token/admin/{token_id}/assign`
- **Request Body:**
  ```json
  {
    "solver_id": 2,
    "admin_note": "Reassigned to Accounts desk"
  }
  ```

#### 7. Super Admin: Soft-Delete to Trash & Restore:
- **Soft Delete:** `POST /api/token/admin/{token_id}/delete` -> `{"success": true, "message": "Token moved to trash successfully."}`
- **Restore:** `POST /api/token/admin/{token_id}/restore` -> `{"success": true, "message": "Token restored from trash successfully."}`

#### 8. Solver Teams List:
- **Route:** `GET /api/token/admin/solvers`
- **Response:** `{"success": true, "solvers": [{"id": 1, "solver_name": "...", "department": "..."}, ...]}`

---

### 7.2. FAQ Forum Endpoints (`static/chat.html`)

#### 1. List FAQs:
- **Route:** `GET /api/v1/faqs`
- **Query Params:**
  - `page`: int (default 1)
  - `limit`: int (default 20, max 100)
  - `category`: string (optional, exact category match)
  - `search`: string (optional, Bengali or English keyword)
  - `sort`: string (`most_liked`, `latest`, `all`)
  - `session_id`: string (or header `X-Session-ID`)
- **Response Shape:**
  ```json
  {
    "status": "success",
    "page": 1,
    "limit": 20,
    "total": 654,
    "items": [
      {
        "id": 1,
        "question": "জাতীয় বিশ্ববিদ্যালয়ের সার্টিফিকেট উত্তোলনের নিয়ম কি?",
        "answer": "সার্টিফিকেট উত্তোলনের জন্য http://103.113.200.68/nu-app/ পোর্টালে লগইন করে...",
        "category": "সার্টিফিকেট",
        "likes_count": 14,
        "has_liked": false,
        "is_active": 1,
        "source_file": "FAQ/faq.txt",
        "created_at": "2026-08-10 12:00:00"
      }
    ]
  }
  ```

#### 2. Get FAQ Categories:
- **Route:** `GET /api/v1/faqs/categories`
- **Response Shape:**
  ```json
  {
    "status": "success",
    "categories": [
      { "category": "ভর্তি", "count": 85 },
      { "category": "সার্টিফিকেট", "count": 64 },
      { "category": "পরীক্ষা", "count": 112 }
    ]
  }
  ```

#### 3. Toggle FAQ Like:
- **Route:** `POST /api/v1/faqs/{faq_id}/like`
- **Headers:** `Content-Type: application/json`
- **Request Body:** `{"session_id": "<client_session_uuid>"}`
- **Response Shape:**
  ```json
  {
    "faq_id": 1,
    "likes_count": 15,
    "has_liked": true
  }
  ```
  *(Calling again with same session toggles back to `has_liked: false` and decrements count).*

#### 4. Top Liked FAQs:
- **Route:** `GET /api/v1/faqs/top-liked?limit=10`
- **Response Shape:**
  ```json
  {
    "status": "success",
    "count": 10,
    "items": [ ... ]
  }
  ```

---

## 8. UI Redesign Preservation & Implementation Guidelines

### 8.1. Administrative & Solver Support Center (`static/index.html`)

1. **Monochromatic Apple/Linear Color Palette:**
   - Background: `--bg: #F5F5F7` (Dark: `#121214`)
   - Surface: `--surface: #FFFFFF` (Dark: `#1C1C1E`)
   - Text Primary: `--text: #1D1D1F` (Dark: `#F5F5F7`)
   - Text Secondary: `--text-secondary: #6E6E73` (Dark: `#A1A1A6`)
   - Hairline Border: `--hairline: rgba(0, 0, 0, 0.08)` (Dark: `rgba(255, 255, 255, 0.1)`)
   - Accent: Restrained slate/neutral or single subtle blue/emerald tint.

2. **Data Table Layout:**
   - High density, clean tabular rows: `Token ID`, `Service Type`, `Problem Summary`, `Status Badge`, `Assigned Desk`, `Created Date`, `Action Trigger`.
   - Subtle, muted status pills (e.g. `PENDING` in soft amber hairline badge, `SOLVED` in soft emerald hairline badge).
   - Clicking anywhere on a token row smoothly slides open the inspection drawer.

3. **Slide-over Inspection Drawer:**
   - Slides from the right edge with smooth transition (`translateX(0)` vs `translateX(100%)`).
   - Header with Token ID, Status Badge, Copy Token ID button, and Close button (`Esc` or `✕`).
   - **Student Information Card:** User Name, Phone, Registration No, College Code.
   - **Problem Context:** Full problem description and service type.
   - **Solver Controls (Role-Aware):**
     - When `user.role === 'SOLVER'`:
       - Show **Solve Token Section**: Textarea for `solve_message`, quick resolution templates, and high-contrast "Mark as Solved" button.
       - Show **Send Back to Admin Section**: Textarea for `reason` and secondary outline button "Send Back to Admin (Not Solved)".
       - Hide solver assignment dropdown; show read-only desk badge: `Assigned Desk: {user.department}`.
     - When `user.role === 'ADMIN'` or `SUPER_ADMIN`:
       - Show solver assignment dropdown (`adm-solver-select`).
       - Show status update dropdown (`adm-status-select`).
       - Show internal admin notes input and save button.
       - Show Super Admin trash button if `SUPER_ADMIN`.
   - **Timeline / History Log:** Clean vertical step list showing timestamp, changed by, old status -> new status, and messages.

---

### 8.2. FAQ Panel (`static/chat.html`)

1. **Layout & Dimensions:**
   - Preserve dynamic 70% (AI Chat) / 30% (FAQ Forum) desktop split layout.
   - Responsive collapse on mobile screens with quick toggle.

2. **Search & Category Pills:**
   - Clean search bar with instant debounced input (`handleFaqSearch`, ~200-250ms).
   - Horizontal scrollable topic pill bar (`#faq-topic-tags`): `#সকল_টপিক`, `#ভর্তি`, `#সার্টিফিকেট`, `#পরীক্ষা`.
   - Smooth pill active state styling.

3. **Minimalist Accordion Cards:**
   - Apple Support-style cards with hairline border and subtle surface hover.
   - Question text in bold, clean typography.
   - Accordion expansion with smooth height transition: clicking card or expand button expands full verified answer and official link citations.
   - Action buttons:
     - **"এআই উত্তর" (Ask AI):** Calls `askAiAboutFaq(question)` to populate the chat input and trigger immediate AI response generation.
     - **Atomic Like Button:** Heart icon + counter, toggles like state immediately via `POST /api/v1/faqs/{id}/like`.
     - **Copy Button:** Copies question + answer + official helpline citation to clipboard with momentary "✓ কপিড" visual feedback.
