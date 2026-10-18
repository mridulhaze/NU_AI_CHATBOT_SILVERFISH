# Project Status, Goals & Roadmap

## 1. Project Vision & Goals
The **National University AI Assistant** aims to be a reliable, 24/7 self-service portal for millions of students, faculty members, and affiliated colleges across Bangladesh.

### Core Objectives:
1. **Accurate Information Retrieval**: Provide factual answers regarding NU admissions, syllabi, exam schedules, results, re-scrutiny (খাতা পুনর্নিরীক্ষণ), improvement exams, and degree verification.
2. **Bilingual Accessibility**: Seamlessly answer inquiries in both **Bengali (বাংলা)** and **English**.
3. **Up-to-Date Notices**: Continuously capture new official notices and circulars directly from `nu.ac.bd` and affiliated portals.
4. **Lightweight & Embeddable**: Supply a drop-in chat widget that can be integrated onto college websites and portals.

---

## 2. Current Progress & Milestones

| Component | Status | Description |
|---|---|---|
| **Data Scraping & Cleaning** | ✅ Completed | Scrapes notice boards (`recent-news-notice.php`, `examination-notice.php`, `admission-notice.php`), extracts clean table rows, and parses PDFs. |
| **Flexible JSON Dataset System** | ✅ Completed | `data/nu_knowledge_base.json` and `data/quick_links.json` provide modular, editable knowledge catalogs. |
| **Automated Knowledge Updater** | ✅ Completed | `updater.py` with standalone, daemon scheduler (`--daemon`), and REST API (`POST /api/update-knowledge`) integration. |
| **Vector DB Ingestion** | ✅ Completed | Chunks documents and builds persistent vector embeddings in `./nu_vector_db` using `models/gemini-embedding-001` with retry & rate-limit backoff. |
| **FastAPI Backend & Multi-Device IP** | ✅ Completed | Bound to `0.0.0.0:8000`, serves web app directly on root `GET /`, provides multi-turn chat and quick links APIs. |
| **LLM Inference** | ✅ Completed | Powered by modern Google GenAI Client with `gemini-3.5-flash` and senior academic counselor prompt. |
| **Interactive Portal Hub & Chat UI** | ✅ Completed | Standalone responsive floating widget & hub with 1-click official portal tiles, markdown rendering, and PDF download buttons. |
| **Multi-turn Chat History** | ⏳ Planned | Preserve conversation history context across multiple turns. |
| **Streaming Responses (SSE)** | ⏳ Planned | Stream Gemini token generation directly to the frontend for zero-latency UX. |
| **Scheduled Crawler Cron** | ⏳ Planned | Automated periodic ingestion job to refresh vector embeddings daily/weekly. |

---

## 3. Technical Architecture & Decisions

### 3.1 LLM & Embedding Models
- **Embedding Model**: `models/gemini-embedding-001` (dimension: 3072, high multilingual quality).
  - *Decision rationale*: Replaced deprecated `text-embedding-004` which returned 404 in API v1beta.
- **Generative Model**: `gemini-3.5-flash` via `google.genai.Client`.
  - *Decision rationale*: Fast inference, low latency, robust reasoning in Bengali and English, replaces deprecated `gemini-1.5-flash` / `google.generativeai` package.

### 3.2 Vector Store
- **ChromaDB**: Embedded persistent vector store located in `./nu_vector_db`.
- **Chunking Strategy**: `RecursiveCharacterTextSplitter` with `chunk_size=1000` and `chunk_overlap=150`.

### 3.3 Rate Limiting & Throttling
- Free-tier Gemini accounts have rate limits (e.g. 15 requests per minute).
- `ingest.py` groups documents into batches of 10 chunks, introduces a 1.0s inter-batch delay, and applies exponential backoff retry (up to 5 attempts with 6s-24s sleep).

---

## 4. Backlog & Future Tasks for AI Agents / Developers

### High Priority
- [ ] **Stream LLM Output**: Upgrade `/api/chat` to support Server-Sent Events (SSE) / streaming (`client.models.generate_content_stream`) and update JavaScript frontend `fetch` loop to render words progressively.
- [ ] **Session & Conversation History**: Add `session_id` to `ChatRequest` to allow follow-up questions within the same chat session.

### Medium Priority
- [ ] **Direct Source PDF Links**: Enhance the frontend chat window to render clickable citation badges linking directly to specific National University circular PDFs.
- [ ] **Automated Daily Re-indexing**: Add a lightweight scheduled script (cron / task scheduler) that checks for new circular notices published in the last 24-48 hours and incrementally adds them to ChromaDB.

### Low Priority
- [ ] **Admin Ingestion Dashboard**: Provide a password-protected endpoint or simple UI to trigger re-scraping or upload specific circular PDF files manually.
