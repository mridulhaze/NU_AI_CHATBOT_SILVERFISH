## 2026-10-21T14:18:32Z
[Message] timestamp=2026-10-21T14:18:32Z sender=5af1b769-0650-4dd0-9219-1b2493409a96 priority=MESSAGE_PRIORITY_HIGH content=You are Worker M2 (teamwork_preview_test_writer acting as Implementation Worker).
Your working directory is D:\projects\AI_CHAT_BOT\.agents\teamwork\worker_m2_1.
Project root is D:\projects\AI_CHAT_BOT.

MANDATORY: Read D:\projects\AI_CHAT_BOT\.agents\teamwork\ORIGINAL_REQUEST.md (under header ## 2026-10-21T14:03:42Z) and D:\projects\AI_CHAT_BOT\.agents\teamwork\orchestrator_2\SCOPE.md.
Also read the detailed Explorer findings:
- D:\projects\AI_CHAT_BOT\.agents\teamwork\explorer_m1_1\handoff.md
- D:\projects\AI_CHAT_BOT\.agents\teamwork\explorer_m1_2\handoff.md
- D:\projects\AI_CHAT_BOT\.agents\teamwork\explorer_m1_3\handoff.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

File Ownership:
You have exclusive write ownership of:
- backend/services/academic_exam_service.py
- static/chat.html
- tests/test_academic_timeline.py

Objectives & Implementation Tasks:
1. Clean Apple-Style Typography (No Step Cards) in `backend/services/academic_exam_service.py`:
   - Refactor `render_exam_card_timeline_bar(item)`:
     - Completely eliminate the nested boxy cards for steps (`top_cols`, `bottom_cols`, `<div class="w-full bg-white rounded-xl p-2 shadow-2xs border...>`, connector sticks) that created visual clutter.
     - Build a clean, airy Apple-inspired timeline layout:
       - Slim horizontal progress bar track (`h-1.5` or `h-2` with rounded ends, background track + accent progress fill).
       - Neat circular step nodes displaying Bengali numerals `১` to `৬` (or `✓` when `comp` is True).
       - High-contrast Apple-style bold text for milestone titles:
         1. `ইনকোর্স পরীক্ষা`
         2. `ফরম পূরণ`
         3. `রুটিন ও প্রবেশপত্র`
         4. `মূল পরীক্ষা`
         5. `ফলাফল প্রকাশ`
         6. `সনদ ও মার্কশিট`
       - Minimalist date text (e.g., `text-[10px]` or `text-[11px] font-medium text-[var(--text-secondary)]`).
       - Subtle muted status badges (`সম্পন্ন`, `আজ`, `আসন্ন`, `তারিখ অতিক্রান্ত`, `প্রকাশিত`, `তথ্য নেই`).
     - Fix all HTML quoting/string formatting: ensure HTML tags are emitted on single lines without internal newlines across attributes so `formatMarkdown` in `static/chat.html` does NOT inject `<br>` into tag attributes. Remove leading 4-space indentation to prevent markdown blockquote/code formatting.
2. On-Demand Collapsible Timeline (Not Shown Automatically):
   - In `backend/services/academic_exam_service.py` (`format_exam_card_markdown`):
     - The timeline must NOT display automatically when exam cards load. Wrap the timeline in a container directly above the vertical service cards grid with default `class="hidden"` (e.g. `<div id="{timeline_id}" class="hidden ...">`).
     - Place an elegant Apple-style button directly on the exam card:
       `[ 📊 পরীক্ষার টাইমলাইন ও ধাপসমূহ দেখুন ↓ ]`
     - Provide smooth on-demand toggle functionality (inline or via `toggleExamTimeline` in `static/chat.html`), flipping the label/arrow between `[ 📊 পরীক্ষার টাইমলাইন ও ধাপসমূহ দেখুন ↓ ]` and `[ 📊 পরীক্ষার টাইমলাইন ও ধাপসমূহ লুকান ↑ ]`.
3. Frontend Integration in `static/chat.html`:
   - Ensure `toggleExamTimeline(containerId, btn)` is available globally and cleanly handles class toggling and button label/icon updates.
   - Do NOT break any existing DOM elements, IDs, or tests in `test_e2e_ui_redesign.py`.
4. Domain Integrity & Unit Test Coverage in `tests/test_academic_timeline.py`:
   - Maintain strict accuracy rules (past date != completed without confirmation), official portal links, and compatibility with Honours, Degree Pass, Master's, and Professional programs.
   - Add unit test coverage in `tests/test_academic_timeline.py` verifying:
     - `format_exam_card_markdown` includes the toggle button with `পরীক্ষার টাইমলাইন ও ধাপসমূহ দেখুন`.
     - The timeline container starts with `hidden`.
     - `render_exam_card_timeline_bar` contains no boxy step cards, and contains Bengali numerals `১` to `৬` and bold milestone titles.
5. Verification:
   - Run: `python -m pytest tests/test_academic_timeline.py tests/test_token_service_domain.py tests/test_faq_forum.py tests/test_e2e_ui_redesign.py -v`
   - Verify that all tests pass with 0 failures.

Write your report to D:\projects\AI_CHAT_BOT\.agents\teamwork\worker_m2_1\handoff.md and send a message when done.
