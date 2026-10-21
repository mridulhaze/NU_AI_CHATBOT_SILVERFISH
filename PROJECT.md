# Project: National University AI Assistant Support Center & FAQ UI Redesign

## Architecture
The system is a FastAPI + SQLite backend with vanilla HTML/Tailwind/JavaScript frontends serving National University Bangladesh students, administrators, and department solvers.
- **Frontend Layer**:
  - `static/index.html`: Administrative & Solver Support Center, token management, system configuration.
  - `static/chat.html`: Student AI Chat interface with dynamic 70%/30% flex split to the FAQ Forum panel.
  - `static/widget.js`: Embeddable iframe client embedding `chat.html`.
- **Backend & API Layer**:
  - `backend/api/admin_routes.py`: Admin & Solver token endpoints (`/api/v1/admin/tokens/...`), backup/restore, soft delete.
  - `token_service/routes.py`: Legacy and public token routes (`/api/token/...`).
  - `backend/api/faq_routes.py`: FAQ forum routes (`/api/v1/faqs/...`), category listing, atomic like toggle, sync.
- **Domain & Security Layer**:
  - Role-based access control (RBAC): `ADMIN`, `SUPER_ADMIN`, `SOLVER`, `STUDENT`.
  - Solvers are isolated to their assigned department desk tokens and only have `Solve` and `Send Back to Admin (Not Solved)` actions.
  - Super Admins have trash soft-delete/restore and system backup/restore.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | E2E Testing Suite & Infra | Comprehensive test suite for Support Center and FAQ UI contracts, RBAC isolation, and URL integrity | M0 | Survey & User Criteria |
| 2 | High-Density Token Table | High-density data table replacing cluttered cards in `static/index.html` with subtle status badges | M1 | ORIGINAL_REQUEST §R1 |
| 3 | Slide-Over Inspection Drawer | Smooth right-side slide-over drawer opening upon clicking any token row in `static/index.html` | M1 | ORIGINAL_REQUEST §R1 |
| 4 | Solver & Admin Drawer Controls | Clean context separation: Student info, Solver actions (`Solve`, `Return to Admin`), Admin assignment, Notes | M1 | ORIGINAL_REQUEST §R1 |
| 5 | Return-to-Admin Route Fix | Ensure `submitReturnToAdmin` calls `/api/v1/admin/tokens/{id}/return-to-admin` without 404 | M1 | Survey Explorer 1 |
| 6 | Solver Role Access Enforcement | Solvers only see Support Center tab, assigned desk tokens, no desk re-assignment dropdown | M1 | ORIGINAL_REQUEST §R3 & AGENTS.md |
| 7 | Super Admin Trash & Actions | Preserve soft-delete, restore, and backup actions in Support Center table/drawer | M1 | ORIGINAL_REQUEST §R3 & AGENTS.md |
| 8 | Monochromatic Design Tokens in Index | Apply `--bg: #F5F5F7`, `--surface: #FFFFFF`, `--text: #1D1D1F`, `--text-secondary: #6E6E73`, `--hairline: rgba(0,0,0,0.08)` | M1 | ORIGINAL_REQUEST §R1 |
| 9 | FAQ Monochromatic Redesign | Redesign FAQ panel in `static/chat.html` removing Twitter/X motifs in favor of Apple Support/Stripe aesthetic | M2 | ORIGINAL_REQUEST §R2 |
| 10 | Horizontal Category Scroll Pills | Replace vertical category box with a smooth horizontal scroll pill bar with hashtag topics | M2 | ORIGINAL_REQUEST §R2 |
| 11 | Debounced Search Bar | Instant debounced search filtering for FAQs | M2 | ORIGINAL_REQUEST §R2 |
| 12 | Sleek FAQ Accordion Cards | Clean accordion cards with smooth expanding answer drawers and chevron animation | M2 | ORIGINAL_REQUEST §R2 |
| 13 | FAQ Inline Action Controls | Inline atomic like counter with heart, "এআই উত্তর" prompt injection into chat, and one-click copy | M2 | ORIGINAL_REQUEST §R2 |
| 14 | Dynamic 70%/30% Split Layout | Preserve smooth cubic-bezier flex transition between AI chat and FAQ panel | M2 | ORIGINAL_REQUEST §R2 |
| 15 | Theme & Dark Mode Unification | Ensure seamless light and dark mode monochromatic color system across both pages | M3 | Acceptance Criteria |
| 16 | Official Portal URLs Preserved | Retain `http://103.113.200.68/nu-app/`, `http://app11.nu.edu.bd/`, `http://ems.nu.ac.bd/`, forbid deprecated URLs | M3 | AGENTS.md & User Criteria |
| 17 | Final Verification & 100% Tests | 100% pass on domain tests (`test_token_service_domain.py`, `test_faq_forum.py`), E2E suite, and clean audit | M4 | Acceptance Criteria |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M0 | E2E Testing Track & Test Suite | Implement automated E2E tests in `tests/test_e2e_ui_redesign.py` and publish `TEST_READY.md` | none | DONE |
| M1 | Support Center Data Table & Slide-Over Drawer | Redesign `static/index.html` Support Center to minimalist table, slide-over drawer, fix return-to-admin route | none | DONE |
| M2 | Sleek FAQ Panel & Category Pills | Redesign `static/chat.html` FAQ panel to Apple/Stripe accordion, horizontal pills, remove X motifs | none | DONE |
| M3 | Theme & Dark Mode Unification | Harmonize monochromatic design tokens and dark mode across both pages | M1, M2 | DONE |
| M4 | Final Milestone: Verification & Hardening | Run all test suites, E2E tests, adversarial challenge, and Forensic Auditor verification | M0, M1, M2, M3 | DONE |

## Interface Contracts
### Support Center Frontend ↔ Backend Admin Routes
- `GET /api/token/admin/tokens?limit=100`: Returns token array `[{ token_id, student_name, student_phone, reg_no, service_type, problem_description, status, solver_name, solver_id, created_at, is_deleted, admin_note, ... }]`
- `GET /api/token/admin/{token_id}`: Returns single token details object.
- `POST /api/token/admin/{token_id}/solve`: Payload `{"solve_message": str, "solver_name": Optional[str], "admin_note": Optional[str]}`.
- `POST /api/v1/admin/tokens/{token_id}/return-to-admin`: Payload `{"reason": str, "solver_name": Optional[str]}`. (Note: Must use `/api/v1/admin/tokens/...` prefix).
- `POST /api/token/admin/{token_id}/assign`: Payload `{"solver_id": int, "admin_note": Optional[str]}` (Admin/Super Admin only).
- `POST /api/token/admin/{token_id}/status`: Payload `{"status": str, "message": Optional[str], "admin_note": Optional[str]}`.
- `POST /api/token/admin/{token_id}/delete`: Soft delete to trash (Super Admin only).
- `POST /api/token/admin/{token_id}/restore`: Restore from trash (Super Admin only).

### FAQ Panel Frontend ↔ Backend FAQ Routes
- `GET /api/v1/faqs?category={category}&search={search}&sort={sort}&session_id={session_id}`: Returns list of FAQ items `[{ id, category, question, answer, source, likes, is_liked, created_at }]`.
- `GET /api/v1/faqs/categories`: Returns `[{ category: str, count: int }]`.
- `POST /api/v1/faqs/{id}/like`: Payload `{"session_id": str}`. Returns `{ success: true, likes: int, is_liked: bool }`.

### Chat Console ↔ FAQ Panel Interaction
- `askAiAboutFaq(questionText)`: Sets `split-container` `data-split="chat"`, injects question text into `#user-input`, dispatches input event, focuses input, and calls `handleSend()`.
- `setSplitMode("chat" | "faq")`: Toggles attribute `data-split` on `#split-container`.

## Code Layout
- `static/index.html`: Owned exclusively by Milestone 1 Worker. Contains Support Center table, slide-over drawer, and modal logic.
- `static/chat.html`: Owned exclusively by Milestone 2 Worker. Contains FAQ forum panel, category pills, accordion, and chat split view.
- `tests/test_e2e_ui_redesign.py`: Owned exclusively by Milestone 0 Test Writer.
- `tests/test_token_service_domain.py`: Preserved, must pass 100%.
- `tests/test_faq_forum.py`: Preserved, must pass 100%.
- `tests/test_security_rbac.py`: Preserved, must pass 100%.
- `tests/test_backup_and_delete.py`: Preserved, must pass 100%.
