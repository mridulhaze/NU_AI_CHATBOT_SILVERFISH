## 2026-10-21T06:29:43Z
You are an implementation worker assigned to Milestone 2.
Your working directory is: D:\projects\AI_CHAT_BOT\.agents\teamwork\worker_m2\
Original request path: D:\projects\AI_CHAT_BOT\.agents\teamwork\ORIGINAL_REQUEST.md
Scope document: D:\projects\AI_CHAT_BOT\.agents\teamwork\sub_orch_m2\SCOPE.md
Project specification: D:\projects\AI_CHAT_BOT\PROJECT.md
Survey findings: D:\projects\AI_CHAT_BOT\.agents\teamwork\explorer_survey_2\survey.md and D:\projects\AI_CHAT_BOT\.agents\teamwork\explorer_survey_2\handoff.md

Scope boundaries:
- Exclusive write ownership: static/chat.html ONLY. Do NOT edit any other application files.
- Write your progress, changelog, and handoff to D:\projects\AI_CHAT_BOT\.agents\teamwork\worker_m2\.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Mission:
Refine the FAQ panel in static/chat.html following Apple Support and Stripe monochromatic design principles:
1. Replace Twitter/X visual motifs:
   - In header avatar: replace the 𝕏 black circular badge with clean NU emblem/monochrome badge.
   - In FAQ cards: replace @nu_official handles and Twitter blue verified badges with clean official monochromatic badges.
2. Horizontal Category Scroll Pills:
   - Refactor #faq-topic-tags into a smooth horizontal scroll pill bar (flex items-center gap-2 overflow-x-auto no-scrollbar py-2.5) with hashtag topics (#সকল_টপিক, #ভর্তি, #পরীক্ষা, #সনদ_উত্তোলন, etc.).
   - Active state: crisp monochromatic pill (bg-[#1D1D1F] text-white). Inactive state: subtle outline pill (bg-white border border-[rgba(0,0,0,0.08)] text-[#6E6E73] hover:text-[#1D1D1F] hover:bg-[#F5F5F7]).
3. Search Bar:
   - Clean search bar with instant debounced filtering (preserving handleFaqSearch with 250ms debounce).
4. Sleek Accordion Cards:
   - Minimalist accordion cards with crisp typography, generous whitespace, and smooth expanding answer drawers.
   - Clean disclosure chevron with smooth rotation on expansion.
5. Action Controls:
   - Atomic Like: Inline atomic like counter with heart icon calling POST /api/v1/faqs/${item.id}/like using session ID.
   - "এআই উত্তর" (Ask AI): Injects question into chat #user-input and triggers handleSend().
   - One-Click Copy: Copies question and answer with instant ✓ কপিড visual feedback for 1,800ms.
6. Dynamic 70%/30% Split Layout:
   - Preserve fluid cubic-bezier transition between data-split="chat" and data-split="faq".
7. Preserve all existing DOM IDs, functions, and API contracts.
8. Verification:
   - Run: .venv\Scripts\python.exe -m pytest tests/test_faq_forum.py -v
   - Run: .venv\Scripts\python.exe -m pytest tests/test_token_service_domain.py -v
9. Write changes.md and handoff.md in your directory, and report completion back via send_message.
