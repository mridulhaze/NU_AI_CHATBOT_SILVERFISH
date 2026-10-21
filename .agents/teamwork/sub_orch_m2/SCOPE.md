# Scope: Milestone 2 — FAQ Panel Redesign & Dynamic Chat Integration

## Mission
Refine the FAQ panel in `static/chat.html` following Apple Support and Stripe monochromatic design principles: clean search bar with instant debounced filtering, smooth horizontal category pill bar with hashtag topics, sleek accordion cards, and inline action controls while preserving the dynamic 70%/30% flex split.

## Architecture & Boundaries
- Owned files: `static/chat.html` (strictly exclusive write ownership)
- Input reports: `D:\projects\AI_CHAT_BOT\.agents\teamwork\explorer_survey_2\survey.md`, `D:\projects\AI_CHAT_BOT\.agents\teamwork\explorer_survey_2\handoff.md`, `D:\projects\AI_CHAT_BOT\.agents\teamwork\ORIGINAL_REQUEST.md`, `PROJECT.md`, `AGENTS.md`
- Target verification commands:
  - `.venv\Scripts\python.exe -m pytest tests/test_faq_forum.py -v` (must pass 6/6)
  - `.venv\Scripts\python.exe -m pytest tests/test_token_service_domain.py -v` (must pass 4/4)

## Key Technical Specifications
1. **Monochromatic Apple/Stripe Aesthetic**:
   - Apply design tokens: `--bg: #F5F5F7`, `--surface: #FFFFFF`, `--text: #1D1D1F`, `--text-secondary: #6E6E73`, `--hairline: rgba(0,0,0,0.08)`, and official green accent `--accent: #006A4E`.
   - Remove residual Twitter/X motifs (the `𝕏` black circle avatar, `@nu_official` handles, and Twitter blue verified badges). Replace with clean NU emblem/monochrome badge.
2. **Horizontal Category Scroll Pills**:
   - Refactor `#faq-topic-tags` into a smooth horizontal scrollbar (`flex items-center gap-2 overflow-x-auto no-scrollbar py-2`) with hashtag topics (`#সকল_টপিক`, `#ভর্তি`, `#রেজিস্ট্রেশন`, `#সনদ_উত্তোলন`, etc.).
   - Active state: crisp monochromatic pill (`bg-[#1D1D1F] text-white`). Inactive state: subtle outline pill (`bg-white border border-[rgba(0,0,0,0.08)] text-[#6E6E73] hover:text-[#1D1D1F] hover:bg-[#F5F5F7]`).
3. **Debounced Search Bar**:
   - Clean search input with search icon, clear button, and 250ms debounced search handler (`handleFaqSearch`).
4. **Sleek Accordion Cards**:
   - Accordion questions with clean typography and smooth chevron rotation on disclosure.
   - Smooth answer drawer expansion (`transition: all 280ms cubic-bezier(0.16,1,0.3,1)`).
5. **Action Controls**:
   - Atomic Like button: Heart icon + atomic counter from `POST /api/v1/faqs/{id}/like` with `localStorage` session ID.
   - "এআই উত্তর" (Ask AI): Injects question into chat `#user-input` and triggers `handleSend()`.
   - One-Click Copy: Copies question + answer to clipboard with immediate `✓ কপিড` visual feedback for 1,800ms.
6. **Dynamic 70%/30% Split Layout**:
   - Preserve existing cubic-bezier flex transition (`data-split="chat"` vs `data-split="faq"`).
   - Ensure clicking FAQ card questions smoothly expands panel to 70% while chat contracts to 30%, and clicking chat / "এআই উত্তর" smoothly restores chat to 70%.
7. **Preserved DOM IDs & JS Handlers**:
   - Preserve `#split-container`, `#chat-section`, `#faq-forum-panel`, `#faq-search-input`, `#faq-topic-tags`, `#faq-main-list`, `handleFaqSearch`, `handleTopicTagClick`, `askAiAboutFaq`, `handleFaqLikeClick`, `copyFaqToClipboard`, `setSplitMode`.

## Completion Criteria
1. `static/chat.html` updated with monochromatic Apple Support / Stripe aesthetic, horizontal category scroll pills, and refined accordion.
2. Twitter/X motifs cleanly replaced with NU monochromatic identity.
3. 70%/30% split layout transition and all action controls work flawlessly.
4. FAQ test suite passes 100%: `.venv\Scripts\python.exe -m pytest tests/test_faq_forum.py -v`.
5. Reviewer and Challenger approvals + Forensic Auditor clean verdict.
