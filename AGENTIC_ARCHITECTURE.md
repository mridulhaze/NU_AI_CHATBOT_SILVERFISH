# National University Bangladesh AI Assistant — Master Agentic Architecture & System Knowledge

> **Document Type:** Agentic Architecture & Continuity Specification  
> **Target Audience:** Autonomous Agents (OpenAI GPT-4o, Claude 3.5/3.7, Google Antigravity, Human Engineers)  
> **Last Updated:** August 2026  
> **Author:** Antigravity System Architect  

---

## 1. System Overview & Tech Stack

This project is an enterprise-grade AI Assistant and Support Token Operations Platform tailored for **National University Bangladesh (জাতীয় বিশ্ববিদ্যালয় বাংলাদেশ)**.

### Core Stack:
- **Backend Framework:** FastAPI (Python 3.11+) with ASGI runner (`uvicorn`).
- **Database Engine:** SQLite (Dual Database Architecture):
  - `data/nu_assistant.db`: RAG knowledge base, official university services mega-menu (23 services), FAQs, scraped portals, dynamic knowledge gaps queue, and crawler history.
  - `data/nu_tokens.db`: Support token lifecycle, solvers, user credentials, service forms, and audit trail logs.
- **RAG & Orchestration Engine:** Multi-stage retrieval with keyword fallback (<0.001s lookup), intent classification, fast direct preloads, and similarity scoring.
- **Agent Swarm Architecture:**
  - **Agent 1 (Researcher & QA Engine):** `ai_lab/agent1_researcher_qa.py` — Evaluates queries, benchmarks responses against official university portals, detects outdated links, and scores response quality (0-10 scale).
  - **Agent 2 (Quality Evaluator & Knowledge Architect):** `ai_lab/agent2_evaluator.py` — Reviews Agent 1 outputs, validates compliance with official rules, detects knowledge gaps, and enriches responses.
  - **Deep Crawler & Polite Scraper Agents:** Autonomous crawlers with robots.txt compliance, depth tracking, and auto-ingestion.
- **Frontend UI:** Single-page application (`static/index.html`) styled with Tailwind CSS, supporting interactive bilingual (Bengali/English) UX, responsive mobile layouts, real-time ticket management, dynamic QR code generation, and official verification slips.

---

## 2. Verified University Portals & Absolute Truth URLs

Any AI working on this codebase **MUST STRICTLY ADHERE** to these verified working URLs. Older legacy links must NEVER be suggested to students.

| University Service / Portal | Correct Working URL | Status / Purpose |
| :--- | :--- | :--- |
| **Student Online Services Portal (ERP)** | `http://103.113.200.68/nu-app/` | Student Login, Online TC, Original/Provisional Certificate, Marksheet, Academic Transcript, Name & Document Corrections, Duplicate Documents. |
| **Online Admission Portal** | `http://app11.nu.edu.bd/` | Undergraduate (Honours), Degree Pass, Masters, Professional Admissions. |
| **Examination Management System (EMS)** | `http://ems.nu.ac.bd/` | Exam result management, college marks entry, center management. |
| **Form Fill-up & Registration (App1)** | `http://app1.nu.edu.bd/` | College & Exam form fill-up, student subject registration. |
| **Official University Main Portal** | `http://www.nu.ac.bd/` | Official notices, office directories, news, acts & regulations. |
| **Sonali Seba Online Payment Gateway** | `https://sblepay.sonalibank.com.bd/` | Sonali Bank payment slips & fee verification. |

> ⚠️ **CRITICAL FORBIDDEN LINKS:**  
> - `http://services.nu.edu.bd/` (Deprecated & Unreachable)  
> - `http://103.113.200.36/` (Outdated IP, replaced by `http://103.113.200.68/nu-app/`)

---

## 3. Role-Based Access Control (RBAC) & Security Rules

The platform defines 4 strict security roles in `data/nu_tokens.db` -> `users` table:

```
                  ┌──────────────────────────────┐
                  │         SUPER_ADMIN          │ (Full access to all tokens, delete/restore,
                  └──────────────┬───────────────┘  users, backups, crawlers, AI engine)
                                 │
                  ┌──────────────┴───────────────┐
                  │            ADMIN             │ (Token re-assignment, user creation,
                  └──────────────┬───────────────┘  solver desk management, audit logs)
                                 │
                  ┌──────────────┴───────────────┐
                  │            SOLVER            │ (Isolated to own Department / Desk only,
                  └──────────────┬───────────────┘  2-action workflow: Solve OR Return to Admin)
                                 │
                  ┌──────────────┴───────────────┐
                  │             USER             │ (Public student / staff view, token creation,
                  └──────────────────────────────┘  status verification slip & QR access)
```

### 3.1. Solver Isolation Rules:
1. When a user with role `SOLVER` logs in (e.g. `Accounts & Sonali Seba Desk` or `ICT Support Team`):
   - The token query backend **MUST ONLY RETURN** tokens assigned to their own department/desk (`solver_id` or `solver_name` matching their department).
   - Solvers **CANNOT** view tokens belonging to other departments (`EMS`, `TC`, `Examination Section`, etc.).
2. **Solver Menu Restriction:** Solvers only see the `Token Support Center` tab. All administrative tabs (`sitemap`, `ai_engine`, `users`, `logs`, `backups`) are strictly hidden and forbidden.
3. **Solver 2-Action Workflow:**
   - **Action 1 (Solve Token):** `POST /api/token/admin/{token_id}/solve` — Solvers enter verified resolution text and transition status to `SOLVED`.
   - **Action 2 (Send Back to Admin - Not Solved):** `POST /api/token/admin/{token_id}/return-to-admin` — If a solver cannot resolve the ticket or it needs higher administrative instruction, they provide reason notes and return the ticket to `PENDING` status with an audit trail.
   - **Solver Re-Assignment Prohibition:** Only `ADMIN` / `SUPER_ADMIN` can assign or re-assign tokens to other desks. For Solvers, assignment controls are locked with a read-only badge.

---

## 4. Support Token Database Schema (`data/nu_tokens.db`)

### `token_requests` Table:
- `id` (INTEGER PRIMARY KEY)
- `token_id` (TEXT UNIQUE) — Formatted as `NU-YYYY-NNNNNN` (e.g. `NU-2026-000196`).
- `service_type` (TEXT) — Service code (e.g. `FORM_FILLUP`, `EMS`, `TC`, `CERTIFICATE`, `ACCOUNTS`, `OTHER`).
- `problem` (TEXT) — Student/User problem description.
- `user_name` (TEXT), `user_phone` (TEXT), `registration_no` (TEXT), `college_code` (TEXT)
- `status` (TEXT) — `PENDING`, `ASSIGNED`, `PROCESSING`, `SOLVED`, `CANCELLED`, `CLOSED`.
- `solver_id` (INTEGER REFERENCES `token_solvers(id)`)
- `solver_name` (TEXT) — Desk/Officer title (e.g. `Accounts & Sonali Seba Desk`, `ICT Support Team`).
- `solve_message` (TEXT) — Resolution text provided when solved.
- `created_date` (TEXT), `updated_date` (TEXT), `solved_date` (TEXT)
- `estimated_solve_date` (TEXT) — Default `Within 3 Business Days` or custom SLA date.
- `admin_note` (TEXT) — Internal admin/solver handover notes.
- `is_deleted` (INTEGER DEFAULT 0) — Soft-delete flag for Super Admin trash/recycle bin.
- `deleted_at` (TEXT) — Timestamp of deletion.

### `token_solvers` Table:
- `id` (INTEGER PRIMARY KEY)
- `solver_name` (TEXT) — Name or Desk Title.
- `department` (TEXT) — Department (e.g. `Accounts & Sonali Seba Desk`, `ICT Support Team`, `Controller of Examination Section`, `Admission & Registration Cell`, `Certificate & Academic Records Cell`).
- `email` (TEXT), `phone` (TEXT), `active` (INTEGER DEFAULT 1).

### `academic_exam_information` Table (`data/nu_assistant.db`):
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `program_type` (TEXT NOT NULL) — `Honours`, `Degree Pass`, `Master's`, `Professional`
- `examination_year` (INTEGER NOT NULL) — e.g. 2024, 2025
- `part` (TEXT) — `Part 1`, `Part 2`, `Part 3`, `Part 4`, `Final`, `Preliminary`
- `semester` (TEXT) — `Semester 1` through `Semester 8` (Professional courses)
- Unique constraint: `UNIQUE(program_type, examination_year, part, semester)`
- Exam timeline dates: `incourse_date`, `incourse_mark_last_date`, `form_fillup_start_date`, `form_fillup_last_date`, `exam_date`, `exam_routine_date`, `admit_card_date`, `exam_last_date`, `practical_mark_start_date`, `practical_mark_last_date`
- Result tracking: `probable_result_date`, `actual_result_date`, `is_result_published` (BOOLEAN)
- Post-result & verification: `rescrutiny_start_date`, `rescrutiny_last_date`, `rescrutiny_result_date`, `document_print_date`, `is_document_printed` (BOOLEAN)
- Official links & remarks: `revaluation_link`, `college_result_link`, `remarks`
- Timestamps: `created_at`, `updated_at`

### `users` Table:
- `id` (INTEGER PRIMARY KEY), `username` (TEXT UNIQUE), `password_hash` (TEXT), `full_name` (TEXT), `department` (TEXT), `role` (`SUPER_ADMIN`, `ADMIN`, `SOLVER`, `USER`), `active` (INTEGER DEFAULT 1).

---

## 5. Token Verification Slip & QR System

1. **Scannable QR URL:** `${origin}/?token=${token_id}`
2. **Auto-Trigger on Scan:** When opened on mobile, the application detects `?token=NU-YYYY-NNNNNN` in the URL query and immediately displays the official Token Verification Slip.
3. **Slip Presentation:**
   - Official University Crest & Header (`🏛️ National University Bangladesh`).
   - Token Number, Status, Service Category, Assigned Solver/Desk.
   - Generation Date, Assignment Date, Estimated SLA Date.
   - Helpline numbers (`📞 +88029291011 | +88029291000`).
   - Embedded live Scannable Token QR Code (`#slip-qrcode-box`).
   - Student Problem Description & Official Resolution Box.
   - Official Seal Text: **`🏛️ System Genarated   token by National University Bangladesh . Gazipur`**
4. **Print Formatting:**
   - `@media print` rules hide all UI buttons (`Print`, `Close`, `Ask Bot`, search bars) so the document prints as a clean, authentic certificate.

---

## 6. Backup & Restore Architecture

- **Archive Format:** `.zip` archive containing:
  - `nu_tokens.db` (Live token & solver database)
  - `nu_assistant.db` (Knowledge base & services database)
  - `metadata.json` (Timestamp, version, total token count, hash checksums)
- **Super Admin Endpoint:**
  - `POST /api/v1/admin/backup/create` (Download ZIP)
  - `POST /api/v1/admin/backup/restore` (Upload & atomic rollback-safe restoration)

---

## 7. Starting from the Last State — Guide for Future AI Agents

If you are an AI assistant (OpenAI, Claude, Antigravity) continuing work on this project:
1. **Always verify database connections** using `token_service.db.get_token_db_connection` and `backend.core.database.get_db_connection`.
2. **Preserve Solver Department Isolation** in any new queries touching `token_requests`.
3. **Execute domain tests** via `python tests/test_token_service_domain.py` before and after making modifications.
4. **Never hardcode obsolete URLs** (`services.nu.edu.bd` or `103.113.200.36`); always use `http://103.113.200.68/nu-app/` and `http://app11.nu.edu.bd/`.
