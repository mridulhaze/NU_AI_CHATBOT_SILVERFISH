# Project Structure & Developer Handover Guide: National University AI Chatbot (`nu_ai_chatbot`)

> **Note for AI Assistants & Developers:** This file is the single source of truth for the project architecture, directory structure, core data flows, and active development roadmap. **Whenever new files, APIs, or architectural changes are introduced, update this document accordingly.**

---

## 1. Project Overview & Mission
- **Project Name:** National University Bangladesh AI Assistant (`nu_ai_chatbot`)
- **Domain:** Official Knowledge & Support Engine for National University Bangladesh (nu.ac.bd) serving 3M+ students across 2,200+ affiliated colleges.
- **Key Objectives:**
  1. Accurate, hallucination-free bilingual (Bangla, English, Banglish) RAG answers for notices, admission, examination routines, results, and fees.
  2. Autonomous 24/7 continuous simulation and database self-enrichment using **NousResearch Hermes-3 / Cloud LLMs**.
  3. Integrated **Token Support & Helpdesk Service** (`NU-YYYY-XXXXX`) with role-based routing (Admin, Super Admin, Solvers).

---

## 2. Directory Tree & File Inventory
d:\projects\AI_CHAT_BOT
│ ├── .venv/ # Python 3.11 virtual environment 
├── data/ # Local persistent storage & caches 
│ ├── knowledge_gaps.json # Logged retrieval failures and missing topic registry 
│ └── enrichment_log.json # History of auto-enriched Q&A pairs 
│ ├── prompts/ # System prompts & Agent Persona configurations 
│ ├── system_prompt.txt # Primary RAG bot persona & guardrails 
│ ├── nu_student_system_prompt.md # Upgraded System Prompt enforcing direct answer first, structured formatting (headings/bullets/steps), concrete examples/formats, follow-up suggestions, ambiguity clarifications, and uncertainty admission.
│ └── solver_templates.txt # Pre-formatted resolution templates for support desks 
│ ├── backend/
│ ├── services/session_memory.py # In-memory multi-turn conversation session store (10-turn sliding window) with extensible architecture for Redis/PostgreSQL.
│ └── api/admin_routes.py # Admin management endpoints including User Management, Department Assignment, Trash Recovery, and Many-to-Many Q&A Knowledge Management.
│ ├── db/
│ └── schema.sql # Relational schemas for SQLite/PostgreSQL including qa_knowledge_base, qa_question_variants, and qa_answer_variants.
│ ├── static/ # Web Frontend UI assets 
│ ├── index.html # Master Single Page Application featuring Student Chat Interface, Solver Token Center, and Admin Control Center (with 6-in-1 AI Engine and Many-to-Many Q&A Knowledge Hub).
│ ├── admin.html # Helpdesk triage, solver desks & management portal 
│ ├── css/ # Custom styles, dark/light theme, responsive UI 
│ └── js/ # WebSocket/REST API handlers, QR code generation 
│ ├── token_service/ # Token lifecycle & support ticket engine 
│ ├── init.py 
│ ├── token_manager.py # Token CRUD, status transitions, escalation 
│ ├── models.py # SQLAlchemy / Pydantic schemas (Token, User, Department) 
│ └── desk_router.py # Departmental routing (ICT, Accounts, Exams, etc.) 
│ ├── tests/ # Automated testing & evaluation suite 
│ ├── test_token_service_domain.py # Core domain & RBAC compliance tests 
│ ├── hermes_agent_tester.py # Multi-persona adversarial stress-tester 
│ └── benchmark_after.py # Retrieval accuracy, latency & hallucination benchmarks 
│ ├── paper/ # Academic research papers & IEEE publications 
│ ├── IEEE_Paper.html # Double-column IEEE formatted paper source 
│ ├── IEEE_Paper_Autonomous_... .pdf # Compiled publication-ready PDF 
│ └── generate_paper_pdf.py # Automated ReportLab/Edge PDF compiler 
│ ├── AGENTIC_ARCHITECTURE.md # Complete system architecture & database schema definitions 
├── AGENTS.md # AI assistant memory, official URL rules & RBAC hierarchy 
├── CHANGELOG.md # Historical record of changes and releases 
├── docker-compose.yml # Container orchestration (Web server + Vector DB) 
├── Dockerfile # Multi-stage production container build 
├── ingest.py # Multi-source web/PDF scraper & vector ingestion pipeline 
├── main.py # FastAPI/Flask server, RAG orchestration, API endpoints 
├── program_structure.md # [THIS FILE] Complete project structure & developer roadmap 
├── requirements.txt # Project dependencies 
└── .env # Environment secrets (API keys, ports, DB URLs)

---

## 3. Core Architectural Modules

### A. Dynamic Ingestion & Vector Pipeline (`ingest.py`)
- **Sources Scraped:**
  - `https://www.nu.ac.bd/recent-news-notice.php` (General/Recent notices)
  - `https://www.nu.ac.bd/examination-notice.php` (Exam routines, Form fill-up circulars)
  - `https://www.nu.ac.bd/admission-notice.php` (Admission guidelines)
  - Direct PDF parsing & OCR for tables, fee charts, and schedules.
- **Storage:** Vector Store (ChromaDB / FAISS / Qdrant) with metadata (`title`, `date`, `subject_tag`, `url`).

### B. Hybrid RAG & Query Intent Filter (`main.py`)
- **Subject & Date Matcher:** Extracts course tags (`LLB`, `CSE`, `BBA`, `Degree`, `Honours`, `Masters`) and years (`2024`, `2025`, `2026`).
- **Strict Notice Retrieval Policy:** Only returns notices strictly matching the queried subject. If no matching notice is active, provides a polite fallback link instead of dumping unrelated notices.
- **Temporal Decay Scoring:** Ensures recent notifications are prioritized over historical records.

### C. Token Resolution System (`token_service/`)
- **Token Format:** `NU-YYYY-XXXXX`
- **Role Hierarchies:**
  - **Student / Visitor:** Create token, view status, scan mobile QR.
  - **Solver:** Restricted to assigned desk (`Solve` or `Send Back to Admin`).
  - **Super Admin:** Full access across all departments, system backup/restore, soft-delete recovery.

### D. Autonomous Hermes Agent Simulation (`tests/hermes_agent_tester.py`)
- **Adversarial Red-Teaming:** Emulates panicked students, multilingual queries, and edge cases.
- **Self-Enrichment Loop:** Identifies unanswered questions -> logs to `knowledge_gaps.json` -> synthesizes validated Q&A -> updates Vector DB.

---

## 4. Official University Portals & Reference URLs
> ⚠️ **CRITICAL RULE:** Never output deprecated links (`services.nu.edu.bd` or `103.113.200.36`). Always use:
- **Student Services (TC, Certificate, Correction):** `http://103.113.200.68/nu-app/`
- **Admission Portal:** `http://app11.nu.edu.bd/`
- **EMS Portal (Form Fill-up & Examination):** `https://ems.nu.ac.bd/`
- **Results Portal:** `https://results.nu.ac.bd/`
- **Official Notice Board:** `https://www.nu.ac.bd/recent-news-notice.php`
- **Examination Portal:** `https://www.nu.ac.bd/examination-notice.php`

---

## 5. Architectural Enhancements Completed (Production Readiness Overhaul)

1. **Clean Separation of Student Chat & Staff Workspace:**
   - **Public Student UI:** Served on `/` and `/chat` via `static/chat.html`. Fast, lightweight, zero staff/token/solver clutter.
   - **Admin & Staff Workspace:** Served on `/admin` via `static/index.html`. Full Super Admin governance, Solvers Desk, and system maintenance.
   - **Embeddable Widget:** `static/nu-chat-widget.js` allows one-line `<script>` integration on any affiliated college or portal page. Demo at `/embed-demo.html`.

2. **Automated Incremental Knowledge Synchronization:**
   - Configured 30-minute interval crawling in `crawler/scheduler.py`.
   - **SHA-256 Vector Deduplication:** Implemented in `db/vector_store.py` (`ingest_hash_cache.json`), skipping redundant chunk embeddings and avoiding database write locks.
   - **Non-blocking Startup Crawl:** Background thread inside FastAPI lifespan executes incremental synchronization without holding up server boot.

3. **One-Click Maintenance Sync:**
   - `POST /api/v1/admin/sync-and-maintain`: Trigger background crawl and database optimization on demand.
   - `GET /api/v1/admin/sync-status`: Real-time monitoring of maintenance operations.

4. **Testing, Benchmarking & Security:**
   - **Domain & Notice Unit Tests:** 27/27 tests passing across `tests/test_token_service_domain.py` and `tests/test_notice_filter_service.py`.
   - **Chatbot Quality Evaluation:** 16/16 categories passing (100.0%) in `tests/test_chatbot_evaluation.py` documented in `docs/CHATBOT_EVALUATION_REPORT.md`.
   - **Load & Concurrency Benchmark:** Empirical stress-test across 10 to 1,000 concurrency tiers via `tests/load/benchmark_runner.py` documented in `docs/LOAD_TEST_REPORT.md`.
   - **Security Review & Deployment:** Comprehensive audits in `docs/SECURITY_REVIEW.md` and `docs/DEPLOYMENT_GUIDE.md`.

---

5. **Academic Examination Information Management System:**
   - **Admin Hub:** Section G in `static/index.html` allowing Admin/Super Admin to manage, filter, and preview examination lifecycles for Honours, Degree Pass, Master's, and Professional programs.
   - **Dependent Professional Semesters:** Dynamic binding of Part 1 (Sem 1, 2), Part 2 (Sem 3, 4), Part 3 (Sem 5, 6), and Part 4 (Sem 7, 8).
   - **Student Chat Cards & Drilldown:** Eye-catching cards for each program in `static/chat.html` with dynamic sub-pickers for parts/semesters.
   - **Hallucination Prevention:** Chatbot grounds answers directly in `academic_exam_information` records, displaying neutral placeholders (*"তথ্য এখনো প্রকাশ করা হয়নি।"*) when data is unavailable.
   - **Test Suite:** `tests/test_academic_static.py` (7/7 tests passing).

## 6. Guidelines for AI Assistants Making Updates
1. Every time you add a new endpoint, script, or directory, **append/update its description in Section 2 and Section 3 of this file**.
2. Preserve comments and domain compliance rules (`AGENTS.md`).
3. Run test suites before marking tasks as complete.