# FAQ Ingestion & Parsing Engine Guide
**National University Bangladesh AI Assistant**

## 1. Overview
The FAQ Ingestion Engine (`backend/services/faq_service.py`) automatically ingests, validates, hashes, and indexes questions and answers from `FAQ/faq.txt` into the persistent SQLite database (`data/nu_assistant.db`).

---

## 2. Source File Specifications
- **File path:** `D:\projects\AI_CHAT_BOT\FAQ\faq.txt`
- **Total lines:** 2,130
- **Total characters:** ~196,000
- **Categories:** 41 distinct sections
- **Valid Q&A pairs:** 676 verified entries

---

## 3. Parsing Grammar & Regex Logic

### 3.1 Category Detection
Categories in `faq.txt` start with keywords such as `ক্যাটাগরি`, `বিষয়:`, or `বিভাগ:`.
```python
def clean_category_name(raw: str) -> str:
    # Strips question counters like (প্রশ্ন ১ - ১৫)
    s = re.sub(r"\(.*?\)", "", raw).strip()
    # Strips category prefixes like 'ক্যাটাগরি ১:'
    s = re.sub(r"^(ক্যাটাগরি|বিষয়|বিভাগ|অধ্যায়)\s*[\d০-৯]+[:\s\-]*", "", s).strip()
    if s.startswith(":"):
        s = s[1:].strip()
    return s.strip() or "সাধারণ তথ্য"
```

### 3.2 Question & Answer Pattern Matching
- **Question regex:** `r"^\s*(\d+|[০-৯]+)\.\s*প্রশ্ন\s*:\s*(.*)"`
- **Answer regex:** `r"^\s*উত্তর\s*:\s*(.*)"`
- Multi-line answers (tables, bullet points, official portal links) are continuously captured until the next question or category boundary.
- Malformed headers with empty answers (e.g. line 325) are filtered by `if ans.strip():`.

---

## 4. Idempotency & Like Preservation

Each FAQ entry is assigned an MD5 content hash:
```python
source_hash = md5(f"{question.strip()}|{answer.strip()}".encode("utf-8")).hexdigest()
```
When re-running ingestion or admin re-sync:
1. If an entry with matching `source_hash` exists, its metadata (`question`, `answer`, `category`, `keywords`) is updated, but its user-generated `likes_count` is **strictly preserved**.
2. If new, it is inserted with `likes_count = 0`.
3. Auto-seeding runs automatically on server startup if active FAQs count < 500.

---

## 5. Triggering Ingestion Manually

### Via Python Script
```python
from backend.services.faq_service import get_faq_service
service = get_faq_service()
result = service.sync_from_file()
print(result)
```

### Via HTTP API
```bash
curl -X POST http://127.0.0.1:5005/api/v1/faqs/sync
```
