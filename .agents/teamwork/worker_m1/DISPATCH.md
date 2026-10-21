## 2026-10-21T06:29:22Z
Sender: d6f83ece-157c-4a55-94b6-dc137a133250
Priority: MESSAGE_PRIORITY_HIGH

You are an implementation worker assigned to Milestone 1.
Your working directory is: D:\projects\AI_CHAT_BOT\.agents\teamwork\worker_m1\
Original request path: D:\projects\AI_CHAT_BOT\.agents\teamwork\ORIGINAL_REQUEST.md
Scope document: D:\projects\AI_CHAT_BOT\.agents\teamwork\sub_orch_m1\SCOPE.md
Project specification: D:\projects\AI_CHAT_BOT\PROJECT.md
Survey findings: D:\projects\AI_CHAT_BOT\.agents\teamwork\explorer_survey_1\survey.md and D:\projects\AI_CHAT_BOT\.agents\teamwork\explorer_survey_1\handoff.md

Scope boundaries:
- Exclusive write ownership: static/index.html ONLY. Do NOT edit any other application files.
- Write your progress, changelog, and handoff to D:\projects\AI_CHAT_BOT\.agents\teamwork\worker_m1\.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. Integrity violations WILL be detected and your work WILL be rejected.

Mission:
Redesign the Administrative & Solver Support Center in static/index.html following Apple/Linear monochromatic aesthetics:
1. Replace noisy, nested multi-colored cards with a clean, high-density data table (#admin-tokens-tbody).
   - Use subtle, muted status badges (soft tints, small dot indicators, clean monochromatic palette: --bg: #F5F5F7, --surface: #FFFFFF, --text: #1D1D1F, --text-secondary: #6E6E73, --hairline: rgba(0,0,0,0.08)).
   - Columns: Token ID & Time, Student Info (Name, Phone, Reg), Service & Desk, Problem, Status, Actions.
   - Make each table row (<tr>) clickable with onclick="openAdminManageToken('${t.token_id}')" to open the slide-over drawer.
   - For quick action buttons on the row (Trash, Restore), attach event.stopPropagation() so clicking them does not open the drawer.
2. Restructure #admin-manage-token-modal into a sleek slide-over drawer:
   - Fixed right-side panel: fixed top-0 right-0 h-full w-full max-w-xl bg-white border-l shadow-2xl transform translate-x-full transition-transform duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] z-[60] flex flex-col.
   - Backdrop overlay for smooth dismissal when clicking outside.
   - Clear sections inside drawer:
     - Header: Token ID, date, close button (closeAdminManageTokenModal()).
     - Student & Problem context: #adm-user-name, #adm-user-phone, #adm-reg-no, #adm-service, #adm-date, #adm-status-badge, #adm-problem.
     - Desk Controls: #adm-admin-controls-panel (#adm-solver-select, #adm-status-select), #solver-assignment-notice (#solver-desk-name-display).
     - Desk Action Controls: #adm-solve-message, submitSolveToken(), #solver-return-reason-input, submitReturnToAdmin().
     - Internal Notes: #adm-note-input, saveAdminNoteOnly().
3. Preserve Strict Solver Role Access Control:
   - When user.role === 'SOLVER', force tab to Support Center only, hide all other admin tabs.
   - Solvers only see their assigned department desk tokens.
   - Solvers only have two actions: Solve or Send Back to Admin (Not Solved). Cannot reassign desk.
4. Bug Fix on Return-to-Admin:
   - In submitReturnToAdmin() (around line 5281), update the API endpoint to:
     ${API_BASE}/api/v1/admin/tokens/${currentAdminSelectedTokenId}/return-to-admin
     (Payload: {"reason": reason, "solver_name": solverName}).
5. Preserve Super Admin Controls:
   - Soft-delete (POST /api/token/admin/${tokenId}/delete), restore (POST /api/token/admin/${tokenId}/restore), and trash view.
6. Preserve all existing DOM IDs and event handlers.
7. Verification:
   - Run: .venv\Scripts\python.exe -m pytest tests/test_token_service_domain.py -v
   - Run: .venv\Scripts\python.exe -m pytest tests/test_faq_forum.py -v
8. Write changes.md and handoff.md in your directory, and report completion back via send_message.
