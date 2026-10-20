# FAQ Forum REST API Reference
**National University Bangladesh AI Assistant**

Base URL: `http://127.0.0.1:5005/api/v1/faqs`

---

## 1. List FAQs
Retrieves a paginated list of FAQs with filtering, full-text search, and sorting.

- **Method:** `GET`
- **Endpoint:** `/api/v1/faqs`
- **Query Parameters:**
  - `category` *(string, optional)*: Filter by category name (e.g. `ভর্তি, রিলিজ স্লিপ ও কোটা`). Default: all.
  - `search` *(string, optional)*: Keyword query in Bengali or English (e.g. `ভর্তি` or `TC`).
  - `sort` *(string, optional)*: Ordering mode. Options: `most_liked` (default), `latest`, `all`.
  - `page` *(integer, optional)*: Page number (default: 1).
  - `limit` *(integer, optional)*: Items per page (default: 20, max: 100).
  - `session_id` *(string, optional)*: Session identifier for `has_liked` resolution.
- **Headers:**
  - `X-Session-ID` *(string, optional)*: Alternative to `session_id` query param.

### Example Response:
```json
{
  "status": "success",
  "page": 1,
  "limit": 20,
  "total": 676,
  "items": [
    {
      "id": 1,
      "source_key": "faq_0001",
      "question": "১ম মেধা তালিকায় নাম আসার পর ভর্তি না হলে কি রিলিজ স্লিপে আবেদন করা যাবে?",
      "answer": "হ্যাঁ। তবে মেধা তালিকায় নির্বাচিত কলেজে যদি আপনি ভর্তি না হন...",
      "category": "ভর্তি, রিলিজ স্লিপ ও কোটা",
      "likes_count": 14,
      "has_liked": false,
      "is_active": 1
    }
  ]
}
```

---

## 2. Top 10 Most-Liked FAQs
Retrieves the most popular FAQs sorted by like count.

- **Method:** `GET`
- **Endpoint:** `/api/v1/faqs/top-liked`
- **Query Parameters:**
  - `limit` *(integer, optional)*: Number of top FAQs to return (default: 10).
  - `session_id` *(string, optional)*: Client session ID.

### Example Response:
```json
{
  "status": "success",
  "count": 10,
  "items": [
    {
      "id": 4,
      "question": "অনার্স ১ম বর্ষের ইনকোর্স পরীক্ষা না দিলে কি মূল পরীক্ষায় অংশ নেওয়া যায়?",
      "likes_count": 25,
      "has_liked": true,
      "category": "ক্লাস, ইনকোর্স ও ফরম পূরণ"
    }
  ]
}
```

---

## 3. List Categories
Returns all categories and their respective question counts.

- **Method:** `GET`
- **Endpoint:** `/api/v1/faqs/categories`

### Example Response:
```json
{
  "status": "success",
  "categories": [
    {
      "category": "ভর্তি, রিলিজ স্লিপ ও কোটা",
      "count": 15
    },
    {
      "category": "ক্লাস, ইনকোর্স ও ফরম পূরণ",
      "count": 15
    }
  ]
}
```

---

## 4. Toggle Like / Unlike
Atomically toggles a like for a given FAQ entry. If already liked by the session, the like is removed and the counter is decremented.

- **Method:** `POST`
- **Endpoint:** `/api/v1/faqs/{faq_id}/like`
- **Request Body:**
```json
{
  "session_id": "student_sess_9a8b7c"
}
```

### Example Response:
```json
{
  "faq_id": 1,
  "likes_count": 15,
  "has_liked": true
}
```

---

## 5. Get FAQ Detail
Retrieves a single FAQ record by its database ID.

- **Method:** `GET`
- **Endpoint:** `/api/v1/faqs/{faq_id}`

### Example Response:
```json
{
  "status": "success",
  "faq": {
    "id": 1,
    "question": "...",
    "answer": "...",
    "category": "...",
    "likes_count": 15,
    "has_liked": false
  }
}
```

---

## 6. Trigger Synchronization (Admin)
Idempotently scans `FAQ/faq.txt` and inserts/updates records while preserving like counts.

- **Method:** `POST`
- **Endpoint:** `/api/v1/faqs/sync`

### Example Response:
```json
{
  "status": "success",
  "synced": 676,
  "categories_count": 40,
  "source_file": "D:\\projects\\AI_CHAT_BOT\\FAQ\\faq.txt"
}
```
