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
