# Scope: Academic Examination Milestone Timeline Apple-Style Refactor

## Architecture & Context
The National University AI Assistant provides academic examination timeline milestones and status for students across various programs (Honours, Degree Pass, Master's, Professional).
Currently, the timeline steps use boxy/nested cards that create clutter and raw HTML string bleeding in chat/card rendering.
The refactor transforms this into:
1. Clean Apple-style typography with a slim horizontal progress track, bold milestone titles (১ to ৬), minimalist date text, subtle muted status badges.
2. An on-demand collapsible container with a toggle button `[ 📊 পরীক্ষার টাইমলাইন ও ধাপসমূহ দেখুন ↓ ]` directly on the exam card, default collapsed/hidden.
3. Strict domain integrity and 100% pass on all 97 automated tests (plus 8 static academic tests = 105 passed).

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Survey & Technical Investigation | Identify timeline rendering code, templates, HTML generation, toggle logic, and test assertions | None | DONE |
| M2 | Apple-Style Timeline & Collapsible Refactor | Remove boxy cards, implement slim horizontal progress bar + bold Apple typography + toggle button | M1 | DONE |
| M3 | Comprehensive Review & Challenger Verification | Inspect visual quality, dark mode, HTML escaping, and interactive toggling | M2 | DONE |
| M4 | Forensic Audit & Quality Gate | Independent integrity check and full test regression pass | M3 | DONE |

## Interface Contracts & Constraints
- Button Text: `[ 📊 পরীক্ষার টাইমলাইন ও ধাপসমূহ দেখুন ↓ ]` flipping to `[ 📊 পরীক্ষার টাইমলাইন ও ধাপসমূহ লুকান ↑ ]`
- Milestone Titles:
  1. `ইনকোর্স পরীক্ষা`
  2. `ফরম পূরণ`
  3. `রুটিন ও প্রবেশপত্র`
  4. `মূল পরীক্ষা`
  5. `ফলাফল প্রকাশ`
  6. `সনদ ও মার্কশিট`
- Status Badges:
  - `সম্পন্ন`, `আজ`, `আসন্ন`, `তারিখ অতিক্রান্ত`, `প্রকাশিত`, `তথ্য নেই`
- Zero HTML syntax bleeding or attribute quoting issues in markdown/chat rendering.
- All 97 automated tests pass:
  `python -m pytest tests/test_academic_timeline.py tests/test_token_service_domain.py tests/test_faq_forum.py tests/test_e2e_ui_redesign.py -v` (0 failures)
