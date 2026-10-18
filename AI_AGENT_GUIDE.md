# AI Agent Guide & Codebase Context

Welcome, AI Agent! This guide is designed to help you quickly understand the architecture, data flow, key files, and conventions in this repository so you can work effectively without friction.

---

## 1. Quick Summary of the Project
- **Name**: National University AI Assistant (RAG Chatbot).
- **Core Purpose**: Answers student & faculty questions regarding National University of Bangladesh (জাতীয় বিশ্ববিদ্যালয়) courses, grading, results, routines, and admissions.
- **Tech Stack**:
  - Backend: Python 3.10+, FastAPI, Uvicorn, Pydantic.
  - LLM & GenAI: `google-genai` SDK (`gemini-3.5-flash`), `langchain-google-genai` (`models/gemini-embedding-001`).
  - Vector Store: `ChromaDB` (`langchain-chroma`, stored in `./nu_vector_db`).
  - Ingestion: `requests`, `BeautifulSoup4`, `pdfplumber`, `langchain-text-splitters`.
  - Frontend: Single-file responsive chat widget HTML (`gemini-code-1786959765553.html`) using Tailwind CSS.

---

## 2. Key Files Map

| File | Purpose | Critical Details |
|---|---|---|
| [`ingest.py`](file:///e:/projects/AI_CHAT_BOT/ingest.py) | Ingestion pipeline | Scrapes notices, parses PDFs, chunks text, and embeds into `./nu_vector_db`. Uses rate-safe batching (10 chunks/batch) and exponential backoff. |
| [`main.py`](file:///e:/projects/AI_CHAT_BOT/main.py) | API Server | FastAPI app exposing `POST /api/chat`. Performs similarity search (k=4), formats bilingual RAG prompt, and queries Gemini. |
| [`gemini-code-1786959765553.html`](file:///e:/projects/AI_CHAT_BOT/gemini-code-1786959765553.html) | Chat UI Widget | Client-side widget talking to `http://localhost:8000/api/chat`. |
| [`.env`](file:///e:/projects/AI_CHAT_BOT/.env) | Secrets & Config | Contains `GEMINI_API_KEY`. |
| [`requirements.txt`](file:///e:/projects/AI_CHAT_BOT/requirements.txt) | Dependencies | Package versions for pip. |
| [`PROJECT_STATUS.md`](file:///e:/projects/AI_CHAT_BOT/PROJECT_STATUS.md) | Roadmap & Backlog | Refer to this file for active milestones and next features to implement. |
| [`CHANGELOG.md`](file:///e:/projects/AI_CHAT_BOT/CHANGELOG.md) | History of Changes | Review past fixes and technical decisions. |

---

## 3. Important Rules & Conventions

### Model Names & Compatibility
- **Embedding Model**: ALWAYS use `models/gemini-embedding-001` in both `ingest.py` and `main.py`. Do NOT use `text-embedding-004` (returns 404).
- **LLM Model**: Use `gemini-3.5-flash` via `from google import genai; client = genai.Client(api_key=...)`. Do NOT use deprecated `google.generativeai` with `gemini-1.5-flash`.

### Vector Store Consistency
- Always use `from langchain_chroma import Chroma` (do NOT use `langchain_community.vectorstores.Chroma`).
- Persistent storage path is `./nu_vector_db`.
- Embedding function passed to Chroma must be identical between ingestion and retrieval (`GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=...)`).

### Gemini API Rate Limits
- When generating embeddings in bulk, avoid single large bursts. Maintain batch sizes of 10-25 with short sleeps and retry-on-429 logic.

### Multilingual Support (Bengali & English)
- The assistant is designed to automatically detect and reply in the user's language (Bengali for Bengali questions, English for English questions). Preserve this instruction in prompt templates.

---

## 4. Useful Verification Commands

### Test Knowledge Ingestion:
```bash
python ingest.py
```

### Test Vector Retrieval:
```bash
python -c "import os; from dotenv import load_dotenv; load_dotenv(); from langchain_chroma import Chroma; from langchain_google_genai import GoogleGenerativeAIEmbeddings; emb = GoogleGenerativeAIEmbeddings(model='models/gemini-embedding-001', google_api_key=os.getenv('GEMINI_API_KEY')); db = Chroma(persist_directory='./nu_vector_db', embedding_function=emb); print(db.similarity_search('admission', k=1)[0].page_content[:150])"
```

### Run FastAPI Server:
```bash
uvicorn main:app --reload --port 8000
```
