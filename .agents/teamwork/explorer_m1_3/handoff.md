# Handoff Report: Test Suite & Domain Constraints Investigation (Milestone 1)

**Investigator**: Explorer 3 (`teamwork_preview_explorer`)  
**Working Directory**: `D:\projects\AI_CHAT_BOT\.agents\teamwork\explorer_m1_3`  
**Date/Time**: 2026-10-21T14:15:00Z  
**Parent Agent**: `5af1b769-0650-4dd0-9219-1b2493409a96`  

---

## 1. Observation

### 1.1 Baseline Test Suite Execution
- **Command Executed**:
  ```powershell
  python -m pytest tests/test_academic_timeline.py tests/test_token_service_domain.py tests/test_faq_forum.py tests/test_e2e_ui_redesign.py -v
  ```
- **Execution Output**:
  - Result: `91 passed, 147 warnings in 56.89s` (Exit Code 0).
  - Breakdown:
    1. `tests/test_academic_timeline.py`: **7 passed**
    2. `tests/test_token_service_domain.py`: **4 passed**
    3. `tests/test_faq_forum.py`: **8 passed**
    4. `tests/test_e2e_ui_redesign.py`: **72 passed** (Tier 1: 55, Tier 2: 6, Tier 3: 4, Tier 4: 7)
    - Total: **91 tests passed (100%), 0 failures**.

---

### 1.2 Inspection of `tests/test_academic_timeline.py` (Lines 1–124)
- **Functions & Assertions**:
  1. `test_milestone_status_critical_accuracy_rule()` (Lines 25–35):
     - Evaluates `past_date_str = "15 May 2024"` against `today = date(2026, 10, 21)` for `field="exam_date"`.
     - Direct assertions:
       ```python
       label, status_type, is_comp, desc = evaluate_milestone_status("exam_date", past_date_str, record, today)
       assert is_comp is False
       assert status_type == "passed_unconfirmed"
       assert "তারিখ অতিক্রান্ত" in label
       ```
  2. `test_milestone_status_confirmed_completion()` (Lines 36–52):
     - Evaluates explicit confirmation flags: `results_published="Yes"`, `documents_printed="Yes"`.
     - Direct assertions:
       ```python
       label, status_type, is_comp, _ = evaluate_milestone_status("results_published", "Yes", record, today)
       assert is_comp is True
       assert status_type == "published"
       assert "প্রকাশিত" in label

       label, status_type, is_comp, _ = evaluate_milestone_status("documents_printed", "Yes", record, today)
       assert is_comp is True
       assert status_type == "completed"
       assert "সম্পন্ন" in label
       ```
  3. `test_milestone_status_today_and_future()` (Lines 53–68):
     - Today: `"21-10-2026"` -> `status_type == "today"`, `"আজ" in label`, `is_comp is False`.
     - Future: `"25 December 2026"` -> `status_type == "upcoming"`, `"আসন্ন" in label`, `is_comp is False`.
  4. `test_milestone_status_routine_link()` (Lines 69–77):
     - Live URL: `"https://www.nu.ac.bd/uploads/2026/routine_honours.pdf"` -> `status_type == "published"`, `"প্রকাশিত" in label`, `is_comp is True`.
  5. `test_timeline_structure_and_phases()` (Lines 78–104):
     - Database lookup via `store.lookup_academic_exam_info("Honours", "2024", "Part 1")`.
     - Calls `build_academic_milestone_timeline(rec, available_years=["2025", "2024"])`.
     - Direct assertions:
       ```python
       assert len(timeline["phases"]) == 5
       # Phase titles: "ইনকোর্স ও ফরম পূরণ", "পরীক্ষা", "ফলাফল", "পুনঃনিরীক্ষণ", "সনদ ও মার্কশিট"
       assert summary["total_milestones"] == 18
       assert summary["completed_milestones"] >= 1
       assert "disclaimer" in summary
       # Portals check
       assert any("results.nu.ac.bd" in u for u in portal_urls)
       assert any("103.113.200.68/nu-app/" in u for u in portal_urls)
       ```
  6. `test_api_years_endpoint()` (Lines 105–113):
     - `GET /api/v1/academic-exams/years?program_type=Honours&part=Part 1` -> returns status `"success"`, years include `"2024"` and `"2025"`.
  7. `test_api_lookup_endpoint_with_timeline()` (Lines 114–124):
     - `GET /api/v1/academic-exams/lookup?program_type=Honours&examination_year=2025&part=Part 1` -> returns `"timeline"` with `examination_year == "2025"`, `len(phases) == 5`, `len(available_years) >= 2`.

---

### 1.3 Inspection of `backend/services/academic_exam_service.py`
- **Timeline Generation in Chat Messages**:
  - `render_exam_card_timeline_bar(item)` (Lines 1112–1368):
    - Uses 6 milestones:
      1. `ইনকোর্স পরীক্ষা` (`pos="top"`, color `#0284c7`, sub: `ইনকোর্স ও নম্বর জমা`)
      2. `ফরম পূরণ` (`pos="bottom"`, color `#6366f1`, sub: `অনলাইন ফরম ও ফি`)
      3. `রুটিন ও প্রবেশপত্র` (`pos="top"`, color `#2563eb`, sub: `সময়সূচি ও এডমিট কার্ড`)
      4. `মূল পরীক্ষা` (`pos="bottom"`, color `#0d9488`, sub: `তত্ত্বীয় ও ব্যবহারিক পরীক্ষা`)
      5. `ফলাফল প্রকাশ` (`pos="top"`, color `#d97706`, sub: `ফলাফল ও পুনঃনিরীক্ষণ`)
      6. `সনদ ও মার্কশিট` (`pos="bottom"`, color `#e11d48`, sub: `মূল মার্কশিট ও সনদ বিতরণ`)
    - Currently renders nested boxy cards:
      `<div class="w-full bg-white rounded-xl p-2 shadow-2xs border {m['border_color']} hover:shadow-xs transition">` (Lines 1269 and 1306) which causes visual noise and string formatting issues.
  - `format_exam_card_markdown(item)` (Lines 1370–1614):
    - Line 1477: Directly embeds `{render_exam_card_timeline_bar(item)}` unconditionally between the Header Card and the Small Modern Vertical Cards Grid.
    - Result: The timeline currently displays automatically when the exam cards load (violating R2).

---

### 1.4 Inspection of `static/chat.html` & Markdown Parser
- **Markdown Conversion**:
  - `formatMarkdown(text)` (Lines 1793–1836):
    - Lines 1830–1834:
      ```javascript
      html = html.replace(/>\s*\n\s*</g, '><');
      html = html.replace(/\n\n/g, '<br><br>').replace(/\n/g, '<br>');
      html = html.replace(/<br>\s*<(div|section|p|h[1-6]|table|tbody|thead|tr|td|th|button|ul|li)/gi, '<$1');
      html = html.replace(/<\/(div|section|p|h[1-6]|table|tbody|thead|tr|td|th|button|ul|li)>\s*<br>/gi, '</$1>');
      ```
    - Critical finding: Any multiline template string in python with newlines inside HTML tags (or between non-block elements like `<span>` or attribute declarations) will have `<br>` injected, causing broken attributes, leaking template code, or rendering glitches in chat.

---

### 1.5 Inspection of `tests/test_token_service_domain.py` (Lines 1–96)
- **4 Tests**:
  1. `test_atomic_sequence_generation`: verifies prefix `NU-` and uniqueness.
  2. `test_token_creation_and_public_status`: verifies token creation and that PII (`user_phone`) is omitted from public status.
  3. `test_status_transitions_and_rules`: verifies state transitions (`PENDING -> ASSIGNED -> PROCESSING -> SOLVED -> CLOSED`), and validates that `CLOSED -> PENDING` fails.
  4. `test_return_to_admin_flow`: verifies solver can send back token to admin with reason, transitioning status to `PENDING` and appending to `admin_note`.

---

### 1.6 Inspection of `tests/test_faq_forum.py` (Lines 1–278)
- **8 Tests**:
  1. `test_faq_file_parsing`: `>= 650` items from `FAQ/faq.txt`, `>= 20` categories.
  2. `test_faq_sync_idempotent`: repeated syncing keeps record count stable.
  3. `test_faq_listing_and_filtering`: pagination and category filtering.
  4. `test_faq_search`: bilingual search (Bengali and English).
  5. `test_faq_like_toggle_and_anti_duplicate`: session-isolated like/unlike toggling.
  6. `test_top_liked_faqs`: descending order of `likes_count`.
  7. `test_faq_addition_and_similarity_detection`: similarity check (threshold >= 0.70), force insertion.
  8. `test_admin_faq_routes_with_auth`: RBAC authorization on admin endpoints.

---

### 1.7 Inspection of `tests/test_e2e_ui_redesign.py` (Lines 1–1115)
- **72 Tests across 4 Tiers**:
  - **Tier 1 (55 tests)**:
    - Feature 1: High-Density Table (`#admin-tokens-tbody`, headers, status badges, `openAdminManageToken`, `stopPropagation`).
    - Feature 2: Slide-Over Drawer (`#admin-manage-token-modal`, student DOM IDs `#adm-token-id` through `#adm-problem`, solver controls `#adm-solve-message`, `#solver-return-reason-input`, admin panel `#adm-admin-controls-panel`, close handler `closeAdminManageTokenModal`).
    - Feature 3: Solver Role Desk Isolation (ICT vs Accounts isolation, banner `#solver-assignment-notice`, `solve_token`, `return_to_admin`).
    - Feature 4: Super Admin Controls (`#opt-trash-filter`, soft-delete to `DELETED`, omitted from active, restore to active, backup creation).
    - Feature 5: Return to Admin Route (`POST /api/v1/admin/tokens/{token_id}/return-to-admin`, auth required, frontend `submitReturnToAdmin`).
    - Feature 6: FAQ Accordion & Search (`#faq-search-input`, `handleFaqSearch` with 250ms debounce, `#faq-clear-search`, `#faq-main-list`, `toggleFaqExpand`, bilingual search).
    - Feature 7: Horizontal Category Pills (`#faq-topic-tags` with horizontal scroll, `/api/v1/faqs/categories`, `#সকল_টপিক`, `handleTopicTagClick`, category precision).
    - Feature 8: Inline Actions (`handleFaqLikeClick`, like toggle invertibility, `askAiAboutFaq` injecting into `#user-input` and calling `handleSend`, `copyFaqToClipboard` with attribution, `কপিড` feedback).
    - Feature 9: 70%/30% Split Layout (`#split-container[data-split="chat"]`, `#chat-section`, `#faq-forum-panel`, `setSplitMode`, `toggleSplitMode`, `#faq-toggle-split-btn`, `#chat-focus-pill`).
    - Feature 10: Monochromatic Design Tokens (`--bg: #F5F5F7`, `--surface: #FFFFFF`, `--text: #1D1D1F`, `--text-secondary: #6E6E73`, `--hairline: rgba(0, 0, 0, 0.08)`, and dark tokens `[data-theme="dark"]`, `--bg: #1C1C1E`, `--surface: #2C2C2E`, `--text: #F5F5F7`, `toggleTheme`, `prefers-color-scheme`).
    - Feature 11: Official Portal URL Integrity (`103.113.200.68/nu-app`, `app11.nu.edu.bd`, `ems.nu.ac.bd` present; `services.nu.edu.bd` and `103.113.200.36` strictly absent!).
  - **Tier 2 (6 tests)**: Empty list, missing student phone/reg, max problem boundary (2000 chars accepted, 2001 chars rejected), illegal transitions, SQL/XSS search sanitization, unauthenticated rejection.
  - **Tier 3 (4 tests)**: Solver role + desk isolation, category + search + accordion, multi-session like toggle, split toggle + ask AI.
  - **Tier 4 (7 tests)**: Solver solve E2E, solver return E2E, student FAQ discovery, super admin trash governance, portal link authenticity, Admin FAQ form + chat lighting bars (`.chat-lighting-bar-green`, `.faq-lighting-bar-orange`, `#chat-input-criteria-hint`, `Card 4 (Professional) has <svg>`), simplified FAQ header (`<h3>FAQ</h3>`, `#admin-modal-maximize-btn`).

---

## 2. Logic Chain

1. **Test Suite Composition & Target**:
   - The user request and SCOPE.md mandate 100% pass on 91 automated tests:
     `pytest tests/test_academic_timeline.py tests/test_token_service_domain.py tests/test_faq_forum.py tests/test_e2e_ui_redesign.py -v`.
   - Current execution confirms exactly 91 tests exist and all 91 currently pass.
2. **Timeline Refactor Location & Mechanism**:
   - The timeline rendered directly on the examination chat cards is generated in `backend/services/academic_exam_service.py` via `render_exam_card_timeline_bar(item)` and embedded in `format_exam_card_markdown(item)`.
   - In `format_exam_card_markdown`, line 1477 unconditionally includes `{render_exam_card_timeline_bar(item)}`.
   - Refactoring to satisfy R2 requires:
     a. Replacing unconditional inclusion with a collapsible container that has `class="hidden"` or `style="display:none"` by default.
     b. Inserting an Apple-style toggle button:
        `[ 📊 পরীক্ষার টাইমলাইন ও ধাপসমূহ দেখুন ↓ ]`
     c. Clicking the toggle button toggles visibility (e.g. `classList.toggle('hidden')`) and toggles button arrow/text (`↓` <-> `↑`).
3. **Typography & Boxy Card Elimination (R1)**:
   - In `render_exam_card_timeline_bar(item)`:
     - Remove the boxy cards (`bg-white rounded-xl p-2 shadow-2xs border`).
     - Implement a clean Apple-style layout: a slim horizontal progress track, neat circular step nodes (১ to ৬), high-contrast bold milestone titles (`ইনকোর্স পরীক্ষা`, `ফরম পূরণ`, `রুটিন ও প্রবেশপত্র`, `মূল পরীক্ষা`, `ফলাফল প্রকাশ`, `সনদ ও মার্কশিট`), minimalist date text, and subtle muted status badges (`সম্পন্ন`, `আজ`, `আসন্ন`, `তারিখ অতিক্রান্ত`, `প্রকাশিত`, `তথ্য নেই`).
4. **HTML String Sanitization**:
   - Because `formatMarkdown` in `static/chat.html` replaces `\n` with `<br>`, any multi-line template code with newlines inside HTML tags causes broken attribute quotes and syntax bleeding.
   - All HTML produced by `render_exam_card_timeline_bar` and `format_exam_card_markdown` must be cleanly formatted without internal newlines across attributes.
5. **Domain Integrity & Zero Regression**:
   - None of the 91 tests assert the exact DOM classes of the card timeline steps, but `test_academic_timeline.py` strictly asserts:
     - 5 phases in `build_academic_milestone_timeline`: `"ইনকোর্স ও ফরম পূরণ"`, `"পরীক্ষা"`, `"ফলাফল"`, `"পুনঃনিরীক্ষণ"`, `"সনদ ও মার্কশিট"`.
     - Status evaluation: past unconfirmed (`passed_unconfirmed`), routine URL (`published`), completed (`completed`), today (`today`), upcoming (`upcoming`).
     - Endpoints `/api/v1/academic-exams/years` and `/api/v1/academic-exams/lookup`.
   - `test_e2e_ui_redesign.py` tests `static/chat.html` and `static/index.html` structure. Any modification to `chat.html` (e.g., adding a toggle helper script) must NOT touch or break the expected DOM IDs, CSS variables, or portal URLs.

---

## 3. Caveats

1. **Python 3.14 Warnings**:
   - Running pytest produces 147 deprecation warnings related to `datetime.utcnow()` and third-party libraries (`chromadb`, `google.genai`). These warnings do not cause test failures, but new code should avoid introducing additional deprecated calls.
2. **Database Side Effects during Tests**:
   - Tests in `test_faq_forum.py` and `test_token_service_domain.py` write to the SQLite database `db/nu_assistant.db`. They have internal teardown logic that removes test FAQs, but the database file must not be locked or corrupted during test execution.
3. **Professional Program Semester Selection**:
   - In `academic_exam_service.py`, `Professional` programs have course-level selection (18 courses across 5 branches) and semester-level selection (8 semesters). When course + semester is resolved, it renders `format_exam_card_markdown(rec)`. The timeline toggle must work identically across all programs (`Honours`, `Degree Pass`, `Master's`, `Professional`).

---

## 4. Conclusion

- **Test Suite Status**: 91 of 91 tests are passing with 0 failures.
- **Contract for M2 (Apple-Style Timeline Refactor)**:
  1. Refactor `render_exam_card_timeline_bar` in `backend/services/academic_exam_service.py`:
     - Remove boxy step card boxes.
     - Implement a slim horizontal progress track with clean step nodes (১ to ৬), high-contrast bold milestone titles, minimalist dates, and muted status badges.
     - Ensure tight, clean HTML strings to prevent `<br>` bleeding from `formatMarkdown`.
  2. Refactor `format_exam_card_markdown` in `backend/services/academic_exam_service.py`:
     - Wrap timeline in a container that is hidden by default (`class="hidden"`).
     - Add Apple-style toggle button: `[ 📊 পরীক্ষার টাইমলাইন ও ধাপসমূহ দেখুন ↓ ]`.
     - Toggle dynamically shows/hides timeline above the vertical service cards and updates text/arrow.
  3. Ensure that all 4 program types (`Honours`, `Degree Pass`, `Master's`, `Professional`) render the new toggle button and Apple timeline seamlessly.
  4. Preserve all 72 E2E DOM selectors, design tokens, and portal links in `static/chat.html` and `static/index.html`.
  5. Target: Maintain 100% pass on all 91 tests.

---

## 5. Verification Method

To independently verify the test suite and domain constraints:

1. **Execute Complete 91-Test Suite**:
   ```powershell
   python -m pytest tests/test_academic_timeline.py tests/test_token_service_domain.py tests/test_faq_forum.py tests/test_e2e_ui_redesign.py -v
   ```
   - **Expected**: `91 passed, 0 failures`.

2. **Verify Academic Exam Static & Query Grounding**:
   ```powershell
   python -m pytest tests/test_academic_static.py -v
   ```
   - **Expected**: `8 passed, 0 failures`.

3. **Verify Official Portal URLs & Deprecated URL Invalidation**:
   - Confirm official URLs present:
     - `http://103.113.200.68/nu-app/`
     - `http://app11.nu.edu.bd/`
     - `http://ems.nu.ac.bd/`
   - Confirm deprecated URLs strictly absent:
     - `services.nu.edu.bd` (MUST NOT APPEAR)
     - `103.113.200.36` (MUST NOT APPEAR)
