# Original User Request

## 2026-10-21T06:07:11Z

Redesign and simplify the 'Administrative & Solver Support Center' and FAQ Panel in the National University AI Assistant project (D:\projects\AI_CHAT_BOT) from a cluttered, colorful layout into a clean, calm, Apple/Linear-inspired monochromatic interface with streamlined token management and intuitive FAQ discovery.

Working directory: D:\projects\AI_CHAT_BOT
Integrity mode: development

## Requirements

### R1. Minimalist Table & Slide-over Drawer for Administrative & Solver Support Center
- Redesign the cluttered support center in `static/index.html` following Apple/Linear design aesthetics.
- Replace noisy, nested multi-colored cards with a clean, high-density data table featuring subtle status badges, crisp typography, and generous whitespace.
- Implement a sleek slide-over drawer (or right-side inspection pane) that opens smoothly upon clicking any token row, displaying student details, service context, internal notes, and desk action controls (`Solve`, `Return to Admin`).
- Use the monochromatic design tokens: `--bg: #F5F5F7`, `--surface: #FFFFFF`, `--text: #1D1D1F`, `--text-secondary: #6E6E73`, `--hairline: rgba(0,0,0,0.08)`, and a single restrained accent color.

### R2. Sleek Accordion & Category Pills for FAQ Panel
- Refine the FAQ panel in `static/chat.html` following Apple Support and Stripe design principles.
- Feature a clean search bar with instant debounced filtering, a smooth horizontal category pill bar with hashtag topics, and minimalist accordion cards.
- Cleanly integrate action controls: inline atomic like counter with heart, "এআই উত্তর" (Ask AI) prompt injection, and one-click copy with instant feedback.
- Preserve the dynamic 70% / 30% split layout between the AI Chat console and the FAQ panel.

### R3. Domain & Architecture Integrity
- Preserve all existing backend logic, FastAPI endpoints, SQLite schemas, role hierarchies, and official portal links.
- Maintain strict Solver role access controls: Solvers only access their assigned department desk tokens and only have two actions: `Solve` or `Send Back to Admin (Not Solved)`.
- Maintain Super Admin control capabilities across all departments and trash management.

## Acceptance Criteria

### Visual & Usability Standards
- [ ] Support Center UI is clean and uncluttered: table rows are easy to scan, status badges use soft muted tints, and actions live in a dedicated slide-over drawer.
- [ ] FAQ Panel is clean, responsive, and easy to navigate with horizontal topic tags and seamless accordion animation.
- [ ] Monochromatic color system consistently applied across light and dark modes.

### Verification & Test Suite
- [ ] Domain test suite passes 100%: `python -m pytest tests/test_token_service_domain.py -v` (0 failures).
- [ ] FAQ forum test suite passes 100%: `python -m pytest tests/test_faq_forum.py -v` (0 failures).
- [ ] Manual inspection verifies that token status transitions, solver actions, and FAQ interactions work flawlessly.


## 2026-10-21T14:03:42Z

This is a single self-contained UI/UX refactor; keep it small and focused. Refactor the Academic Examination Milestone Timeline in the National University AI Assistant (`D:\projects\AI_CHAT_BOT`) from cluttered step cards into a clean, minimalist Apple-style timeline with bold typography, and make it collapsible on-demand via a toggle button so it does not show automatically.

Working directory: D:\projects\AI_CHAT_BOT
Integrity mode: development

## Requirements

### R1. Clean Apple-Style Typography (No Step Cards)
- Eliminate all nested boxy cards for timeline steps that created visual clutter and raw HTML string bleeding.
- Design a clean, airy Apple-inspired timeline layout:
  - Slim horizontal progress bar track with neat step nodes (১ to ৬).
  - Clean, high-contrast **Apple-style bold text** for milestone titles (`ইনকোর্স পরীক্ষা`, `ফরম পূরণ`, `রুটিন ও প্রবেশপত্র`, `মূল পরীক্ষা`, `ফলাফল প্রকাশ`, `সনদ ও মার্কশিট`).
  - Minimalist date text and subtle muted status badges (`সম্পন্ন`, `আজ`, `আসন্ন`, `তারিখ অতিক্রান্ত`, `প্রকাশিত`, `তথ্য নেই`).
  - Fix all HTML quoting/string formatting so no raw attributes or template code leaks into markdown rendering.

### R2. On-Demand Collapsible Timeline (Not Shown Automatically)
- The timeline must **not** display automatically when the exam cards load.
- Place a clean, elegant Apple-style button directly on the exam card:
  `[ 📊 পরীক্ষার টাইমলাইন ও ধাপসমূহ দেখুন ↓ ]`
- Clicking the button smoothly toggles (expands/collapses) the timeline container directly above the vertical service cards.
- By default, the timeline starts collapsed/hidden, keeping the primary card view clean and focused.

### R3. Domain & Data Integrity
- Preserve all existing SQLite database queries, examination records, status calculation rules (past date != completed without confirmation), and portal links.
- Maintain compatibility with all programs: Honours, Degree Pass, Master's, and Professional.

## Acceptance Criteria

### Visual & Interaction Standards
- [ ] Timeline does not appear automatically upon selecting an exam/part.
- [ ] Clicking the toggle button instantly reveals/hides the timeline smoothly.
- [ ] No nested card boxes for steps; titles use clear Apple-style bold typography with dates and clean status badges.
- [ ] Zero HTML syntax bleeding or escaped attribute artifacts in chat rendering.

### Verification & Test Suite
- [ ] All 91 automated tests pass 100%: `python -m pytest tests/test_academic_timeline.py tests/test_token_service_domain.py tests/test_faq_forum.py tests/test_e2e_ui_redesign.py -v` (0 failures).
- [ ] Manual inspection verifies that the button toggles the Apple-style timeline smoothly and renders flawlessly in both light and dark modes.
