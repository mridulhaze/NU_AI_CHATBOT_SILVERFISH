# Investigation Handoff Report: Exam Cards & On-Demand Milestone Timeline Refactor

**Agent ID**: Explorer 2 (`teamwork_preview_explorer`)  
**Working Directory**: `D:\projects\AI_CHAT_BOT\.agents\teamwork\explorer_m1_2`  
**Date/Timestamp**: 2026-10-21T14:15:00Z  
**Target Milestone**: M1 (Survey & Technical Investigation) -> Ready for M2 (Implementation)

---

## 1. Observation

### 1.1 Architecture of Exam Cards & Vertical Service Cards
Exam cards and vertical service cards are generated on the backend and injected into the chat stream:
- **Generation Source**: `backend/services/academic_exam_service.py` in `format_exam_card_markdown(item: Dict[str, Any]) -> str` (lines 1370–1614).
- **Endpoint Usage**: In `backend/api/academic_exam_routes.py` (lines 159, 197) and `backend/services/academic_exam_service.py` (lines 1737, 1832, 1842).
- **Frontend Ingestion**:
  In `static/chat.html`, user queries or chip selections trigger `handleSend()` (lines 1839–1942), which sends a POST request to `/api/v1/chat`. The server response (`botReply`) contains the markdown/HTML string produced by `format_exam_card_markdown()`.
  The response is rendered via:
  ```javascript
  // static/chat.html lines 1913-1920
  botBubble.innerHTML = `
    <div class="w-8 h-8 rounded-full bg-[var(--surface)] border border-[var(--hairline)] flex items-center justify-center shrink-0 text-xs font-semibold text-[var(--text)] shadow-xs">
      NU
    </div>
    <div class="assistant-bubble chat-bubble-bot flex-1">
      ${formatMarkdown(botReply)}
    </div>
  `;
  ```
  `formatMarkdown()` in `static/chat.html` (lines 1793–1836) preserves HTML tags (`div`, `button`, `span`, `table`, etc.), executing inline event handlers like `onclick` when user interactions occur.

### 1.2 Current DOM Structure in `academic_exam_service.py`
Inside `format_exam_card_markdown(item)` (lines 1452–1613), the layout is currently ordered as follows:
```html
<div class="my-2 space-y-2.5 text-left font-sans">
  <!-- 1. Header Card (Gradient Blue) -->
  <div class="p-3.5 rounded-2xl bg-gradient-to-r from-blue-900 via-indigo-900 to-blue-950 text-white shadow-xs border border-blue-800">
    ... (Header info, year badge, publication badge)
  </div>

  <!-- 2. Current Inline Timeline Bar (Line 1477: Unconditional Render) -->
  {render_exam_card_timeline_bar(item)}

  <!-- 3. Small Modern Vertical Cards Grid (Line 1480) -->
  <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
    <!-- Card 1: 📝 ইনকোর্স ও ফরম পূরণ (lines 1482-1502) -->
    <!-- Card 2: 📅 পরীক্ষা ও রুটিনের সময়সূচি (lines 1504-1532) -->
    <!-- Card 3: 📊 ফলাফল ও পুনর্নিরীক্ষণ (lines 1534-1562) -->
    <!-- Card 4: 📜 সনদ ও মার্কশিট বিতরণ (lines 1564-1580) -->
  </div>

  <!-- 4. Remarks (lines 1584) -->
  {remarks_html}

  <!-- 5. Card 5: 🔗 সরাসরি পোর্টাল লিংকসমূহ (lines 1587-1612) -->
  <div class="bg-slate-50 border border-slate-200 rounded-xl p-3 flex flex-wrap items-center justify-between gap-2 text-xs">
    ...
  </div>
</div>
```

### 1.3 Defects in Current `render_exam_card_timeline_bar(item)`
Directly observed in `backend/services/academic_exam_service.py` (lines 1112–1368):
1. **Always-Visible Visual Clutter**: Renders unconditionally at line 1477, pushing the 4 vertical service cards far down the viewport.
2. **Boxy Nested Step Cards**:
   - Top row (lines 1268–1278): 3 nested cards `<div class="w-full bg-white rounded-xl p-2 shadow-2xs border {m['border_color']} hover:shadow-xs transition">` with connector sticks `<div class="w-0.5 h-3.5 bg-slate-300 mt-1"></div>`.
   - Bottom row (lines 1304–1314): 3 nested cards `<div class="w-full bg-white rounded-xl p-2 shadow-2xs border {m['border_color']} hover:shadow-xs transition">` with connector sticks.
   - Total of 6 heavy boxed cards surrounding a track.
3. **Raw HTML String Bleeding**:
   Because multiline f-strings (`f'''...'''`) use indented blocks (lines 1268–1278 and 1304–1314), lines indented with 4 spaces or separated by empty lines are interpreted by markdown parsers as `<pre><code>` code blocks, leaking raw CSS classes like `class="text-[12px] font-bold"` into the user bubble.
4. **Dark Mode Incompatibility**:
   Hardcoded classes (`bg-slate-50`, `bg-white`, `border-slate-200`, `text-slate-800`, `bg-slate-200`) do not respect `[data-theme="dark"]` tokens (`--surface: #2C2C2E`, `--text: #F5F5F7`), creating bright white contrast clashes when in dark mode.

### 1.4 Design Tokens & Styling Assets
In `static/chat.html` (lines 18–47):
- Monochromatic Light Tokens:
  - `--bg: #F5F5F7`
  - `--surface: #FFFFFF`
  - `--text: #1D1D1F`
  - `--text-secondary: #6E6E73`
  - `--hairline: rgba(0, 0, 0, 0.08)`
  - `--hairline-hover: rgba(0, 0, 0, 0.16)`
  - `--accent: #006A4E` (NU Green)
- Monochromatic Dark Tokens:
  - `--bg: #1C1C1E`
  - `--surface: #2C2C2E`
  - `--text: #F5F5F7`
  - `--text-secondary: #98989D`
  - `--hairline: rgba(255, 255, 255, 0.10)`
  - `--accent: #008763`

---

## 2. Logic Chain

### 2.1 Placement of On-Demand Toggle Button
- **Requirement R2**: "Place a clean, elegant Apple-style button directly on the exam card: `[ 📊 পরীক্ষার টাইমলাইন ও ধাপসমূহ দেখুন ↓ ]`. Clicking the button smoothly toggles (expands/collapses) the timeline container directly above the vertical service cards. By default, the timeline starts collapsed/hidden, keeping the primary card view clean and focused."
- **Optimal Location**:
  Immediately below the Header Card and immediately above the Timeline Container.
  This positions the toggle directly at the top of the card's action hierarchy, clearly indicating that timeline expansion occurs right below the button and directly above the 4 vertical service cards.
- **Button Structure**:
  ```html
  <div class="pt-0.5">
    <button type="button"
            id="{btn_id}"
            onclick="toggleExamTimeline('{timeline_id}', this)"
            class="w-full py-2 px-3.5 rounded-xl border border-[var(--hairline)] bg-[var(--surface)] hover:bg-[var(--bg)] text-[var(--text)] text-xs font-semibold shadow-2xs hover:shadow-xs transition-all flex items-center justify-between cursor-pointer group"
            aria-expanded="false">
      <span class="flex items-center gap-2">
        <span class="text-sm">📊</span>
        <span class="timeline-toggle-label font-bold">পরীক্ষার টাইমলাইন ও ধাপসমূহ দেখুন</span>
      </span>
      <span class="timeline-toggle-icon text-xs text-[var(--text-secondary)] group-hover:text-[var(--text)] font-bold transition-transform duration-200">↓</span>
    </button>
  </div>
  ```
- **Toggle States**:
  - Collapsed (Default): Label is `পরীক্ষার টাইমলাইন ও ধাপসমূহ দেখুন`, arrow is `↓`, `aria-expanded="false"`.
  - Expanded (After Click): Label updates to `পরীক্ষার টাইমলাইন ও ধাপসমূহ লুকান` (or `পরীক্ষার টাইমলাইন ও ধাপসমূহ সংক্ষেপ করুন`), arrow is `↑`, `aria-expanded="true"`.

### 2.2 Placement and Behavior of Timeline Container
- **Position**: Positioned immediately above `<div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">` (the 4 vertical service cards).
- **Default State**: Wrapped with `<div id="{timeline_id}" class="hidden transition-all duration-300">`.
  Because it contains `hidden` (`display: none;`), it consumes 0 vertical space on initial render.
- **Smooth Toggle Implementation**:
  In `static/chat.html` (under `<script>`):
  ```javascript
  function toggleExamTimeline(containerId, btn) {
    const el = document.getElementById(containerId);
    if (!el) return;
    const isHidden = el.classList.contains("hidden");
    if (isHidden) {
      el.classList.remove("hidden");
      if (btn) {
        btn.setAttribute("aria-expanded", "true");
        const label = btn.querySelector(".timeline-toggle-label");
        const icon = btn.querySelector(".timeline-toggle-icon");
        if (label) label.textContent = "পরীক্ষার টাইমলাইন ও ধাপসমূহ লুকান";
        if (icon) icon.textContent = "↑";
      }
    } else {
      el.classList.add("hidden");
      if (btn) {
        btn.setAttribute("aria-expanded", "false");
        const label = btn.querySelector(".timeline-toggle-label");
        const icon = btn.querySelector(".timeline-toggle-icon");
        if (label) label.textContent = "পরীক্ষার টাইমলাইন ও ধাপসমূহ দেখুন";
        if (icon) icon.textContent = "↓";
      }
    }
  }
  window.toggleExamTimeline = toggleExamTimeline;
  ```
- **Instance Isolation**:
  To support multiple exam cards in a single chat history, generate a unique suffix per card instance using `uuid.uuid4().hex[:6]` or a timestamp hash:
  `timeline_id = f"exam-timeline-{prog}_{part}_{year}_{unique_suffix}"`
  `btn_id = f"exam-toggle-btn-{prog}_{part}_{year}_{unique_suffix}"`

### 2.3 Refactoring `render_exam_card_timeline_bar` to Apple-Style Typography (No Step Cards)
- **Eliminate Nested Cards**:
  Remove `top_row_html` and `bottom_row_html` box containers.
- **Slim Horizontal Track**:
  A single continuous track:
  - Height: `h-1.5` or `h-2` with rounded ends.
  - Background track: `bg-[var(--hairline)] dark:bg-white/10`.
  - Progress fill: `bg-emerald-500` with transition `width: {track_fill_pct}%`.
  - 6 step nodes: Circular indicators numbered `১` through `৬` (completed steps show `✓`).
- **Milestone Typography Layout**:
  Directly below each node on the track, arrange a clean 6-column grid without boxes or borders:
  1. Title: Bold Apple-style font (`text-[12px] font-bold text-[var(--text)] leading-tight`).
     Titles:
     - `১. ইনকোর্স পরীক্ষা`
     - `২. ফরম পূরণ`
     - `৩. রুটিন ও প্রবেশপত্র`
     - `৪. মূল পরীক্ষা`
     - `৫. ফলাফল প্রকাশ`
     - `৬. সনদ ও মার্কশিট`
  2. Minimalist Date: `text-[11px] font-medium text-[var(--text-secondary)] mt-1 truncate`.
  3. Subtle Muted Badges:
     - `সম্পন্ন`: Soft emerald badge (`bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800/40`)
     - `আজ`: Soft blue pulse badge (`bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300 border border-blue-200 dark:border-blue-800/40`)
     - `আসন্ন`: Soft amber badge (`bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300 border border-amber-200 dark:border-amber-800/40`)
     - `তারিখ অতিক্রান্ত`: Soft orange badge (`bg-orange-50 text-orange-700 dark:bg-orange-950/40 dark:text-orange-300 border border-orange-200 dark:border-orange-800/40`)
     - `প্রকাশিত`: Soft emerald badge
     - `তথ্য নেই`: Soft slate badge (`bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400 border border-slate-200 dark:border-slate-700`)
- **Fix Raw HTML String Bleeding**:
  Compact the HTML template in Python: remove 4-space leading indentation from lines within the template string, and use single line or clean unindented blocks so markdown parsers never mistake HTML attributes for indented code blocks.

---

## 3. Caveats
- **Self-Contained Fallback**: If a user runs in an environment where `chat.html`'s `<script>` is not loaded (e.g. standalone widget snippet), an inline fallback `onclick="if(window.toggleExamTimeline){window.toggleExamTimeline('...')}else{document.getElementById('...').classList.toggle('hidden')}"` should be included in the button tag.
- **Dedicated Full View State C**: The full-screen `#timeline-view` triggered by Card 5's `openTimelineView()` remains functional and independent; our refactor modifies the inline exam card experience in chat responses without disturbing State C.
- **Test Integrity**: The 7 unit tests in `tests/test_academic_timeline.py` assert on `build_academic_milestone_timeline()` and `evaluate_milestone_status()`. Those functions and their output contracts must remain strictly untouched.

---

## 4. Conclusion & Proposed Implementation Specification

### 4.1 Target Files for M2 Implementation
1. **`backend/services/academic_exam_service.py`**:
   - Refactor `render_exam_card_timeline_bar(item)`:
     - Replace the 3-layer boxy card system with a slim horizontal track + 6 step nodes (১ to ৬) + bold Apple typography + minimalist dates + soft muted status badges.
     - Eliminate all nested card boxes (`bg-white rounded-xl p-2 border`).
     - Remove 4-space indentation to prevent markdown attribute bleeding.
     - Adapt classes to CSS variables (`var(--surface)`, `var(--text)`, `var(--hairline)`).
   - Update `format_exam_card_markdown(item)`:
     - Add unique ID generation (`uuid.uuid4().hex[:6]`).
     - Place the on-demand toggle button `[ 📊 পরীক্ষার টাইমলাইন ও ধাপসমূহ দেখুন ↓ ]` directly between Header Card and the Timeline Container.
     - Wrap `render_exam_card_timeline_bar(item)` in `<div id="{timeline_container_id}" class="hidden transition-all duration-300">` directly above the 4 vertical service cards grid.
2. **`static/chat.html`**:
   - Add `toggleExamTimeline(containerId, btn)` to the script section.
   - Add Apple-style smooth fade animation `@keyframes timelineFadeIn` or transition helper.
3. **`tests/test_academic_timeline.py`**:
   - Add tests verifying:
     - `format_exam_card_markdown()` contains the toggle button with text `পরীক্ষার টাইমলাইন ও ধাপসমূহ দেখুন`.
     - The timeline container has `class="hidden"`.
     - `render_exam_card_timeline_bar()` contains no boxy step cards (`rounded-xl p-2 shadow-2xs border` within steps).
     - Bold milestone titles (`font-bold`) and 6 milestone titles are present.

---

## 5. Verification Method

### 5.1 Test Commands
Execute the full test suite from the repository root:
```powershell
python -m pytest tests/test_academic_timeline.py tests/test_token_service_domain.py tests/test_faq_forum.py tests/test_e2e_ui_redesign.py -v
```
**Expected Result**: All 91 test cases pass with 0 failures.

### 5.2 Specific Assertions to Verify
1. **Collapsible State**:
   - The returned HTML from `format_exam_card_markdown()` has `id="exam-timeline-..."` with class `hidden`.
   - The toggle button has `onclick="toggleExamTimeline('exam-timeline-...'..."` and text `পরীক্ষার টাইমলাইন ও ধাপসমূহ দেখুন`.
2. **Apple-Style Typography**:
   - No step card wrappers: verify absence of `top_row_html` and `bottom_row_html` card containers.
   - Exact milestone titles present with bold styling:
     `ইনকোর্স পরীক্ষা`, `ফরম পূরণ`, `রুটিন ও প্রবেশপত্র`, `মূল পরীক্ষা`, `ফলাফল প্রকাশ`, `সনদ ও মার্কশিট`.
   - Muted status badges present (`সম্পন্ন`, `আজ`, `আসন্ন`, `তারিখ অতিক্রান্ত`, `প্রকাশিত`, `তথ্য নেই`).
3. **Zero HTML Bleeding**:
   - Inspect output rendered in `static/chat.html` via test or browser to ensure no raw `<div class=...>` strings leak as text.
4. **Dark Mode Inspection**:
   - Toggle `data-theme="dark"` and verify that the timeline container and nodes adapt seamlessly to dark background (`#2C2C2E`) and text (`#F5F5F7`).

### 5.3 Invalidation Conditions
- If the timeline appears automatically when an exam query is submitted without clicking the toggle button -> INVALID.
- If the timeline container appears anywhere other than directly above the vertical service cards grid -> INVALID.
- If nested boxy cards remain around individual milestone steps -> INVALID.
- If any of the existing 91 tests fail -> INVALID.
