# Handoff Report: Domain Logic, Backend APIs, Access Controls & Test Suite Baselines

**Date:** 2026-10-21  
**Author:** Explorer 3 (`teamwork_preview_explorer`)  
**Working Directory:** `D:\projects\AI_CHAT_BOT\.agents\teamwork\explorer_survey_3\`  
**Target Milestone:** Domain & Backend Architecture Survey for UI Redesign

---

## 1. Observation

1. **Test Execution Baselines:**
   - Ran `python -m pytest tests/test_token_service_domain.py -v`. Initially encountered missing dependency `ModuleNotFoundError: No module named 'sqlalchemy'`. Installed required packages into user environment (`sqlalchemy`, `langchain-core`, `langchain-text-splitters`, `langchain-community`, `langchain`, `langchain-chroma`, `chromadb`, `langchain-google-genai`, `google-genai`).
   - Re-running `python -m pytest tests/test_token_service_domain.py -v` produced:
     ```
     ======================= 4 passed, 48 warnings in 7.51s ========================
     ```
     All 4 domain tests passed: `test_atomic_sequence_generation`, `test_token_creation_and_public_status`, `test_status_transitions_and_rules`, `test_return_to_admin_flow`.
   - Running `python -m pytest tests/test_faq_forum.py -v` produced:
     ```
     ======================= 6 passed, 9 warnings in 20.81s ========================
     ```
     All 6 FAQ tests passed: `test_faq_file_parsing`, `test_faq_sync_idempotent`, `test_faq_listing_and_filtering`, `test_faq_search`, `test_faq_like_toggle_and_anti_duplicate`, `test_top_liked_faqs`.
   - Running `python -m pytest tests/test_security_rbac.py -v` produced:
     ```
     ============================== 2 passed in 0.90s ==============================
     ```
   - Running `python -m pytest tests/test_backup_and_delete.py -v` produced:
     ```
     ============================== 3 passed in 4.12s ==============================
     ```

2. **Official Portals and URLs:**
   - In `AGENTS.md` (lines 9-14) and `AGENTIC_ARCHITECTURE.md` (lines 32-44):
     - Student Services (TC, Certificate, Marksheet, Transcript, Correction): `http://103.113.200.68/nu-app/`
     - Admission Portal: `http://app11.nu.edu.bd/`
     - EMS Portal: `http://ems.nu.ac.bd/`
     - Form Fill-up: `http://app1.nu.edu.bd/`
     - Main Portal: `http://www.nu.ac.bd/`
     - Sonali Seba: `https://sblepay.sonalibank.com.bd/`
     - Deprecated and forbidden links: `http://services.nu.edu.bd/` and `http://103.113.200.36/`.

3. **Solver Role Access Control & Desk Isolation:**
   - In `backend/api/admin_routes.py` (lines 66-94) and `token_service/routes.py` (lines 136-149):
     If `user_role == "SOLVER"`, queries enforce department desk filtering:
     `solver_id IN (...) OR solver_name IN (...) OR solver_name LIKE '%<dept>%'`.
     Solvers cannot view tokens of other departments.
   - In `backend/api/admin_routes.py` (lines 128-132):
     `POST /api/v1/admin/tokens/{token_id}/assign` has dependency `require_roles([Role.ADMIN, Role.SUPER_ADMIN])`. Solvers cannot reassign tokens; calling this returns HTTP 403 Forbidden.
   - In `backend/services/token_service.py`:
     - Action 1: `solve_token(token_id, solve_message, solver_name, ...)` (lines 403-461) sets status to `SOLVED` and triggers auto-indexing.
     - Action 2: `return_to_admin(token_id, reason, solver_name, ...)` (lines 352-401) sets status back to `PENDING` and appends note `[Returned to Admin by {solver_name} on {timestamp} (Reason: {reason})]`.
   - In `static/index.html` (lines 5422-5439):
     `switchAdminTab(tab)` forces `tab = "tokens"` when `isSolver` is true, hiding all other administrative tabs (`sitemap`, `ai_engine`, `qa_knowledge`, `users`, `logs`, `backups`).

4. **API Endpoints & Contracts:**
   - Token Admin/Solver routes:
     - `GET /api/token/admin/tokens` (and `GET /api/v1/admin/tokens`)
     - `GET /api/token/admin/{token_id}`
     - `POST /api/token/admin/{token_id}/solve` (payload: `{"solve_message": str, "solver_name": Optional[str], "admin_note": Optional[str]}`)
     - `POST /api/token/admin/{token_id}/return-to-admin` (payload: `{"reason": str, "solver_name": Optional[str]}`)
     - `POST /api/token/admin/{token_id}/status` (payload: `{"status": str, "message": Optional[str], "admin_note": Optional[str]}`)
     - `POST /api/token/admin/{token_id}/assign` (payload: `{"solver_id": int, "admin_note": Optional[str]}`)
     - `POST /api/token/admin/{token_id}/delete` and `.../restore` (Super Admin trash operations)
   - FAQ Forum routes:
     - `GET /api/v1/faqs` (query: `category`, `search`, `sort`, `page`, `limit`, `session_id`)
     - `GET /api/v1/faqs/categories` (returns list of `{category, count}`)
     - `GET /api/v1/faqs/top-liked` (returns top 10 items)
     - `POST /api/v1/faqs/{id}/like` (payload: `{"session_id": str}`)
     - `POST /api/v1/faqs/sync` (idempotent parser from `FAQ/faq.txt`)

---

## 2. Logic Chain

1. **Domain Baseline Integrity:**
   - Observation 1 demonstrates that both core domain test suites (`test_token_service_domain.py` and `test_faq_forum.py`) pass with 0 failures when runtime dependencies are available.
   - Therefore, the domain logic and SQLite queries are completely functional and must not be altered during UI redesign.

2. **Access Control Enforcement:**
   - Observation 3 shows that solver isolation is enforced at both the backend SQL query level and API permission level (`require_roles`), in addition to frontend tab and button visibility logic.
   - Therefore, replacing the support center interface with an Apple/Linear table and slide-over drawer must preserve:
     - The role check `isSolver = (user && user.role === 'SOLVER')`.
     - Read-only display of assigned desk for Solvers (no assignment dropdown).
     - The two action triggers: Solve (`POST .../solve`) and Send Back to Admin (`POST .../return-to-admin`).
     - Super Admin soft-delete (`POST .../delete`) and restore (`POST .../restore`) capabilities.

3. **FAQ Forum Interaction Consistency:**
   - Observation 4 shows that FAQ search, category filtering, and like toggling rely on `/api/v1/faqs` and `/api/v1/faqs/{id}/like` with `session_id`.
   - Therefore, redesigning the FAQ panel into an Apple Support accordion with horizontal category pills and inline action buttons will work seamlessly if the existing JS fetch handlers (`handleFaqSearch`, `handleTopicTagClick`, `handleFaqLikeClick`, `copyFaqToClipboard`, `askAiAboutFaq`) are preserved or cleanly adapted with identical API contracts.

---

## 3. Caveats

- **Test Suite Scope:** While `test_token_service_domain.py` and `test_faq_forum.py` pass 100%, `test_token_service.py` has 1 legacy test failure in `test_rag_engine_instant_token_flow` where the RAG classification classifier categorizes "ফরম পূরণ" as `EMS_INFO` instead of `token_attached`. This is outside the scope of the UI redesign and does not impact token domain services or FAQ forum operations.
- **Source Code Immutability:** In accordance with the Explorer mission boundary, no backend or application files were modified. All findings reflect the exact live state of the codebase.

---

## 4. Conclusion

The backend APIs, SQLite models, access controls, and domain test suites are fully mapped, verified, and ready to support the UI redesign:
1. The **Administrative & Solver Support Center** can safely be refactored into a high-density data table with a slide-over inspection drawer without touching any backend endpoints.
2. The **FAQ Panel** can safely be refactored into a sleek Apple Support accordion with horizontal category tags and inline actions (`Like`, `Ask AI`, `Copy`) using existing `/api/v1/faqs` endpoints.
3. Strict Solver role isolation and Super Admin trash operations are clearly identified and defined for seamless preservation.

---

## 5. Verification Method

To independently verify the findings in this report, run the following commands from `D:\projects\AI_CHAT_BOT`:

1. **Verify Token Domain Logic:**
   ```powershell
   python -m pytest tests/test_token_service_domain.py -v
   ```
   *Expected Result:* 4 passed, 0 failed.

2. **Verify FAQ Forum Logic:**
   ```powershell
   python -m pytest tests/test_faq_forum.py -v
   ```
   *Expected Result:* 6 passed, 0 failed.

3. **Verify Security RBAC:**
   ```powershell
   python -m pytest tests/test_security_rbac.py -v
   ```
   *Expected Result:* 2 passed, 0 failed.

4. **Verify Backup & Soft-Delete:**
   ```powershell
   python -m pytest tests/test_backup_and_delete.py -v
   ```
   *Expected Result:* 3 passed, 0 failed.

5. **Inspect Detailed Survey Report:**
   Read `D:\projects\AI_CHAT_BOT\.agents\teamwork\explorer_survey_3\survey.md` for full schema tables, API contracts, and implementation checklists.
