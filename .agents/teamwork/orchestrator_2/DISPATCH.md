# Dispatch Log

## 2026-10-21T14:05:32Z
You are the Project Orchestrator for the task defined in D:\projects\AI_CHAT_BOT\.agents\teamwork\ORIGINAL_REQUEST.md under header ## 2026-10-21T14:03:42Z.

Your working directory is D:\projects\AI_CHAT_BOT\.agents\teamwork\orchestrator_2\.
Project root is D:\projects\AI_CHAT_BOT.

Objective:
Refactor the Academic Examination Milestone Timeline in the National University AI Assistant (D:\projects\AI_CHAT_BOT) from cluttered step cards into a clean, minimalist Apple-style timeline with bold typography, and make it collapsible on-demand via a toggle button so it does not show automatically.

Key Requirements:
1. Clean Apple-Style Typography (No Step Cards):
   - Eliminate all nested boxy cards for timeline steps that created visual clutter and raw HTML string bleeding.
   - Design a clean, airy Apple-inspired timeline layout:
     - Slim horizontal progress bar track with neat step nodes (১ to ৬).
     - Clean, high-contrast Apple-style bold text for milestone titles (ইনকোর্স পরীক্ষা, ফরম পূরণ, রুটিন ও প্রবেশপত্র, মূল পরীক্ষা, ফলাফল প্রকাশ, সনদ ও মার্কশিট).
     - Minimalist date text and subtle muted status badges (সম্পন্ন, আজ, আসন্ন, তারিখ অতিক্রান্ত, প্রকাশিত, তথ্য নেই).
     - Fix all HTML quoting/string formatting so no raw attributes or template code leaks into markdown rendering.
2. On-Demand Collapsible Timeline (Not Shown Automatically):
   - The timeline must NOT display automatically when the exam cards load.
   - Place a clean, elegant Apple-style button directly on the exam card:
     [ 📊 পরীক্ষার টাইমলাইন ও ধাপসমূহ দেখুন ↓ ]
   - Clicking the button smoothly toggles (expands/collapses) the timeline container directly above the vertical service cards.
   - By default, the timeline starts collapsed/hidden, keeping the primary card view clean and focused.
3. Domain & Data Integrity:
   - Preserve all existing SQLite database queries, examination records, status calculation rules (past date != completed without confirmation), and portal links.
   - Maintain compatibility with all programs: Honours, Degree Pass, Master's, and Professional.

Acceptance Criteria:
- Visual & interaction standards met with zero HTML syntax bleeding.
- All 91 automated tests pass: python -m pytest tests/test_academic_timeline.py tests/test_token_service_domain.py tests/test_faq_forum.py tests/test_e2e_ui_redesign.py -v (0 failures).

Management Rules:
- Decompose, dispatch specialists (workers, reviewers), monitor progress.
- Maintain D:\projects\AI_CHAT_BOT\.agents\teamwork\orchestrator_2\progress.md and BRIEFING.md.
- When finished, write handoff.md and send a message claiming completion to me.
