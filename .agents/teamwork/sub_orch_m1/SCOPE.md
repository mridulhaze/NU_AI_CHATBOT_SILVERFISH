# Scope: Milestone 1 — Support Center Data Table & Slide-over Drawer

## Mission
Redesign the Administrative & Solver Support Center in `static/index.html` from a cluttered layout into a clean, calm, Apple/Linear-inspired monochromatic interface with a high-density data table and a smooth slide-over drawer for token inspection and actions.

## Architecture & Boundaries
- Owned files: `static/index.html` (strictly exclusive write ownership)
- Input reports: `D:\projects\AI_CHAT_BOT\.agents\teamwork\explorer_survey_1\survey.md`, `D:\projects\AI_CHAT_BOT\.agents\teamwork\explorer_survey_1\handoff.md`, `D:\projects\AI_CHAT_BOT\.agents\teamwork\ORIGINAL_REQUEST.md`, `PROJECT.md`, `AGENTS.md`
- Target verification commands:
  - `.venv\Scripts\python.exe -m pytest tests/test_token_service_domain.py -v` (must pass 4/4)
  - `.venv\Scripts\python.exe -m pytest tests/test_faq_forum.py -v` (must pass 6/6)

## Key Technical Specifications
1. **High-Density Table**:
   - Monochromatic styling using `--bg: #F5F5F7`, `--surface: #FFFFFF`, `--text: #1D1D1F`, `--text-secondary: #6E6E73`, `--hairline: rgba(0,0,0,0.08)`.
   - Table columns: Token ID / Time, Student Details (Name, Phone, Reg), Service & Desk, Problem Summary, Status Badge, Quick Actions.
   - Soft muted status pips (e.g. subtle monochrome badges with small colored dot).
   - Entire row `<tr>` is clickable with `onclick="openAdminManageToken('${t.token_id}')"` to smoothly open the slide-over drawer. Action buttons (Delete, Restore) must call `event.stopPropagation()`.
2. **Slide-over Drawer**:
   - Restructure `#admin-manage-token-modal` into a sleek slide-over drawer (`fixed top-0 right-0 h-full w-full max-w-xl bg-white border-l shadow-2xl transform translate-x-full transition-transform duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] z-[60]`).
   - Clean card/section hierarchy:
     - Header: Token ID, creation time, close button.
     - Section 1: Student & Problem context (`#adm-user-name`, `#adm-user-phone`, `#adm-reg-no`, `#adm-service`, `#adm-date`, `#adm-status-badge`, `#adm-problem`).
     - Section 2: Desk Action Controls (`#adm-admin-controls-panel` for Admin vs `#solver-assignment-notice` for Solver).
     - Section 3: Solver Actions (`#adm-solve-message`, `submitSolveToken()`, `#solver-return-reason-input`, `submitReturnToAdmin()`).
     - Section 4: Internal Notes (`#adm-note-input`, `saveAdminNoteOnly()`).
3. **Solver RBAC Isolation**:
   - When `user.role === 'SOLVER'`, force tab to Support Center only, hide all other admin tabs.
   - Show only assigned department desk tickets.
   - Solver only has 2 actions: `Solve` or `Send Back to Admin (Not Solved)`. Cannot reassign desk.
4. **Bug Fix**:
   - In `submitReturnToAdmin()`, update endpoint URL from `${API_BASE}/api/token/admin/...` to `${API_BASE}/api/v1/admin/tokens/${currentAdminSelectedTokenId}/return-to-admin` to prevent 404.
5. **Preserved DOM IDs**:
   - Preserve all existing DOM IDs (`#admin-tokens-tbody`, `#admin-token-search`, `#admin-token-status-filter`, `#admin-token-service-filter`, `#adm-solve-message`, `#solver-return-reason-input`, `#adm-note-input`, `#adm-solver-select`, `#adm-status-select`, etc.).

## Completion Criteria
1. `static/index.html` updated with clean Apple/Linear monochromatic table and slide-over drawer.
2. Solver and Admin role access controls strictly enforced.
3. `submitReturnToAdmin` correctly hits `/api/v1/admin/tokens/{id}/return-to-admin`.
4. Domain tests pass 100%: `.venv\Scripts\python.exe -m pytest tests/test_token_service_domain.py -v`.
5. Reviewer and Challenger approvals + Forensic Auditor clean verdict.
