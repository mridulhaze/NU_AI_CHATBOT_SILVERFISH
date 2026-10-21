# Handoff Report: Academic Examination Milestone Timeline & Layout Architecture Investigation

**Date**: 2026-10-21T14:16:00Z  
**Agent**: Explorer 1 (`teamwork_preview_explorer`)  
**Working Directory**: `D:\projects\AI_CHAT_BOT\.agents\teamwork\explorer_m1_1`  
**Milestone**: M1 (Survey & Technical Investigation)

---

## 1. Observation

### 1.1 Files and Functions Responsible for Timeline Data & Rendering
Through `grep_search` and `view_file`, we observed the following components governing the academic examination timeline:

1. **Backend Service (`backend/services/academic_exam_service.py`)**:
   - `render_exam_card_timeline_bar(item: Dict[str, Any]) -> str` (lines 1112–1368):
     Generates the HTML string representing the 6-step horizontal timeline bar.
   - `format_exam_card_markdown(item: Dict[str, Any]) -> str` (lines 1370–1620):
     Constructs the official Academic Examination Card markdown string.
     Directly embeds `{render_exam_card_timeline_bar(item)}` at line 1477 immediately below the header card and above the 4 small vertical cards (`<!-- Small Modern Vertical Cards Grid -->`).
   - `build_academic_milestone_timeline(record, ...) -> Dict[str, Any]` (lines 182–380):
     Produces the comprehensive 5-phase data dictionary (`phases`, `summary`, `official_portals`) for `/lookup` and `chat.html`'s dedicated view.
   - `evaluate_milestone_status(milestone_id, raw_val, record, today_bd)` (lines 87–159):
     Evaluates intelligent status labels and flags adhering strictly to the accuracy rule (past date without confirmation is NOT marked as completed).
   - `process_academic_exam_query(query: str) -> Optional[ChatResponse]` (lines 1622–1866):
     Evaluates chat queries (e.g., "অনার্স ১ম বর্ষের পরীক্ষা কবে?") and builds response replies using `format_exam_card_markdown(rec)` (lines 1737, 1832, 1842).

2. **Backend API Route (`backend/api/academic_exam_routes.py`)**:
   - `GET /api/v1/academic-exams/lookup` (lines 111–174): Calls `format_exam_card_markdown(record)` and `build_academic_milestone_timeline(...)`, returning `{ "status": "success", "markdown_card": ..., "timeline": ... }`.
   - `GET /api/v1/academic-exams/years` (lines 19–40): Returns available examination years.

3. **Frontend Markdown Renderer & Chat (`static/chat.html`)**:
   - `formatMarkdown(text)` (lines 1793–1836): Custom markdown converter used by `handleSend()` (line 1918) to render bot responses. Lines 1830–1834 manipulate newlines and tags:
     ```javascript
     html = html.replace(/>\s*\n\s*</g, '><');
     html = html.replace(/\n\n/g, '<br><br>').replace(/\n/g, '<br>');
     html = html.replace(/<br>\s*<(div|section|p|h[1-6]|table|tbody|thead|tr|td|th|button|ul|li)/gi, '<$1');
     html = html.replace(/<\/(div|section|p|h[1-6]|table|tbody|thead|tr|td|th|button|ul|li)>\s*<br>/gi, '</$1>');
     ```
   - `renderTimelineView(timeline, availableYears)` (lines 1375–1570): Renders the dedicated full `#timeline-view` inside the chat modal.

---

### 1.2 Timeline Steps, Milestone Titles, Dates, and Status Badges
In `backend/services/academic_exam_service.py` (`render_exam_card_timeline_bar`, lines 1120–1239):
- **Step 1**: `title`: `"ইনকোর্স পরীক্ষা"`, `sub`: `"ইনকোর্স ও নম্বর জমা"`, field: `incourse_exam_date` / `incourse_marks_deadline`.
- **Step 2**: `title`: `"ফরম পূরণ"`, `sub`: `"অনলাইন ফরম ও ফি"`, field: `form_fillup_deadline` / `form_fillup_start_date`.
- **Step 3**: `title`: `"রুটিন ও প্রবেশপত্র"`, `sub`: `"সময়সূচি ও এডমিট কার্ড"`, field: `routine_publication_date` / `admit_card_date`.
- **Step 4**: `title`: `"মূল পরীক্ষা"`, `sub`: `"তত্ত্বীয় ও ব্যবহারিক পরীক্ষা"`, field: `exam_date` / `last_exam_date`.
- **Step 5**: `title`: `"ফলাফল প্রকাশ"`, `sub`: `"ফলাফল ও পুনঃনিরীক্ষণ"`, field: `results_published` flag, `actual_result_date` / `probable_result_date`.
- **Step 6**: `title`: `"সনদ ও মার্কশিট"`, `sub`: `"মূল মার্কশিট ও সনদ বিতরণ"`, field: `documents_printed` flag, `document_printing_date`.

**Status Badge Logic (`evaluate_milestone_status`, lines 87–159)**:
- `সম্পন্ন` (completed): When confirmed completion is explicitly verified in DB (`documents_printed == "yes"`, etc.).
- `আজ` (today): When parsed milestone date equals today's date in Bangladesh Standard Time (`p_date == today_bd`).
- `আসন্ন` (upcoming): When parsed milestone date is in the future (`p_date > today_bd`).
- `তারিখ অতিক্রান্ত` (passed_unconfirmed): When milestone date is in the past, but completion is not confirmed.
- `প্রকাশিত` (published): When official result or routine URL is confirmed published (`results_published == "yes"` or `routine_publication_date.startswith("http")`).
- `তথ্য নেই` (no_info): When admin has not supplied date or info.

---

### 1.3 Identification of Nested Boxy Step Cards & Raw HTML Bleeding
1. **Nested Boxy Cards Location**:
   In `backend/services/academic_exam_service.py`:
   - `top_cols` (lines 1268–1278):
     `<div class="w-full bg-white rounded-xl p-2 shadow-2xs border {m["border_color"]} hover:shadow-xs transition">` alternating on top with `<div class="w-0.5 h-3.5 bg-slate-300 mt-1"></div>`.
   - `bottom_cols` (lines 1306–1314):
     `<div class="w-full bg-white rounded-xl p-2 shadow-2xs border {m["border_color"]} hover:shadow-xs transition">` alternating on bottom with `<div class="w-0.5 h-3.5 bg-slate-300 mb-1"></div>`.
   - In addition, the central nodes (line 1290) use ASCII digits: `icon = "✓" if m["comp"] else str(idx + 1)` instead of Bengali numerals (১, ২, ৩, ৪, ৫, ৬).

2. **Root Cause of Raw HTML String Bleeding / Quoting Leaks**:
   - In `backend/services/academic_exam_service.py` lines 1291–1296:
     ```python
     node_cols.append(f'''<div class="flex items-center justify-center">
       <div class="w-7 h-7 rounded-full flex items-center justify-center text-white text-[11px] font-bold shadow-xs transition hover:scale-110 cursor-default {pulse_style}" 
            style="background: {m["color"]}; border: 3px solid #ffffff;" 
            title="{m["title"]}: {m["date"]} ({m["status"]})">
         {icon}
       </div>
     </div>''')
     ```
     The attributes (`class`, `style`, `title`) of the inner `<div>` tag are split across lines 1292, 1293, and 1294 with literal `\n` characters.
   - In `static/chat.html` lines 1830–1831:
     `html.replace(/>\s*\n\s*</g, '><')` only cleans newlines between `>` and `<`.
     `html.replace(/\n/g, '<br>')` converts the intra-attribute newlines into `<br>`:
     `<div class="..." <br> style="background: ...;" <br> title="...">`.
   - The browser's HTML parser cannot parse `<br>` inside an unclosed tag's attribute list, causing the tag to break and leaking `style="background: ...;" title="..."` directly into the chat bubble as visible raw text!

---

## 2. Logic Chain

1. **From Observation 1.1 to 1.3**:
   `format_exam_card_markdown` in `academic_exam_service.py` is invoked whenever exam information is queried in chat or returned via `/lookup`.
2. **From Observation 1.3 to Visual Clutter**:
   `render_exam_card_timeline_bar` generates 6 top cards and 6 bottom cards with alternating vertical connector ticks and a central progress bar. This multi-level card-in-card hierarchy causes severe visual noise and consumes excessive vertical screen real estate.
3. **From Observation 1.3 to HTML Bleeding**:
   Because `render_exam_card_timeline_bar` splits HTML tag attributes across multiple lines within Python multiline triple-quoted strings, `chat.html`'s `formatMarkdown` parser replaces those `\n` characters with `<br>`. Because `<br>` is inserted between attributes, browsers fail to parse the tag correctly and render raw HTML attributes directly on screen.
4. **From Observation 1.1 to Collapsibility Requirement**:
   `format_exam_card_markdown` currently renders `{render_exam_card_timeline_bar(item)}` unconditionally at line 1477. Wrapping this timeline in a collapsible container with default class `hidden` and placing a toggle button `[ 📊 পরীক্ষার টাইমলাইন ও ধাপসমূহ দেখুন ↓ ]` will satisfy Requirement R2 and keep the primary card view clean and focused.

---

## 3. Caveats

- In `tests/test_e2e_ui_redesign.py`, test `test_f4_05_super_admin_backup_creation_and_listing` encountered a transient Windows file lock error on `temp_file.unlink()` during a full suite run, but passed cleanly in isolation (`1 passed in 7.16s`). No code changes were made to project sources per read-only explorer constraints.
- `renderAcademicPreviewModal` in `static/index.html` (admin preview) renders the 4 vertical cards without the timeline bar; the timeline bar is primarily rendered in chat responses and public API lookups via `format_exam_card_markdown`.

---

## 4. Conclusion & Layout Architecture Recommendations

### 4.1 Recommended Clean Apple-Style Layout Architecture
1. **Remove Boxy Cards (No Card Boxes for Steps)**:
   - Deprecate `top_cols` and `bottom_cols` with their enclosing `bg-white rounded-xl border` containers and vertical tick bars.
   - Replace with a sleek, unified, single-level horizontal timeline container:
     - **Slim Central Track**: `h-1` or `h-1.5` background track (`bg-slate-200 dark:bg-slate-700 rounded-full`) with an accent fill (`bg-slate-900 dark:bg-white` or `bg-indigo-600`).
     - **Neat Circular Step Nodes**: 24px circles (`w-6 h-6 rounded-full flex items-center justify-center text-[11px] font-bold border-2 border-white dark:border-slate-800 shadow-2xs`).
     - **Step Numerals**: Use Bengali digits `to_bn_digits(idx + 1)`: `১, ২, ৩, ৪, ৫, ৬` (or `✓` when `m["comp"]`).
     - **Node Column Typography**:
       - **Title**: Apple-style bold text: `font-bold text-[12px] text-slate-900 dark:text-white tracking-tight leading-snug`.
       - **Date**: Minimalist neutral text: `text-[10px] text-slate-500 dark:text-slate-400 font-medium mt-0.5`.
       - **Status Badge**: Subtle muted badge: `text-[9.5px] px-2 py-0.5 rounded-full font-medium border bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-slate-200/60 dark:border-slate-700/60`.

2. **On-Demand Collapsible Toggle Architecture**:
   - In `format_exam_card_markdown`:
     - Generate a deterministic DOM ID for each card:
       `t_id = f"timeline-collapse-{abs(hash(str(item.get('id', '')) + str(item.get('program_type', '')) + str(item.get('examination_year', '')) + str(item.get('part', '')))) % 1000000}"`
     - Directly on the exam card, place the Apple-style toggle button:
       ```html
       <div class="flex justify-center my-1.5">
         <button type="button" 
           onclick="const el=document.getElementById('{t_id}'); const isH=el.classList.toggle('hidden'); this.querySelector('.toggle-label').textContent=isH?'📊 পরীক্ষার টাইমলাইন ও ধাপসমূহ দেখুন ↓':'📊 পরীক্ষার টাইমলাইন ও ধাপসমূহ বন্ধ করুন ↑';"
           class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 dark:bg-slate-800 dark:hover:bg-slate-700 dark:text-slate-200 text-xs font-semibold border border-slate-200 dark:border-slate-700 transition cursor-pointer shadow-2xs">
           <span class="toggle-label">📊 পরীক্ষার টাইমলাইন ও ধাপসমূহ দেখুন ↓</span>
         </button>
       </div>
       <div id="{t_id}" class="hidden transition-all duration-300">
         {render_exam_card_timeline_bar(item)}
       </div>
       ```
     - Default class is `hidden`, satisfying Requirement R2.

3. **Zero HTML Syntax Bleeding Immunity**:
   - In `academic_exam_service.py`, ensure every HTML tag is emitted on a single physical line (no newlines between tag opening `<` and closing `>`).
   - Clean up or strip newlines from generated HTML fragments using `re.sub(r'>\s+<', '><', ...)` or single-line tag strings so `formatMarkdown` never injects `<br>` into tags.
   - In `static/chat.html` (`formatMarkdown`), add a safety check preventing `<br>` replacement inside HTML tags.

---

## 5. Verification Method

To verify these findings independently:
1. **Inspect Timeline Generator**:
   `view_file` on `D:\projects\AI_CHAT_BOT\backend\services\academic_exam_service.py` at lines 1112–1368 and lines 1470–1485.
2. **Inspect HTML Tag Splitting (Root Cause)**:
   `view_file` on `D:\projects\AI_CHAT_BOT\backend\services\academic_exam_service.py` at lines 1291–1297 (notice newlines between `class`, `style`, and `title`).
3. **Inspect Markdown Converter**:
   `view_file` on `D:\projects\AI_CHAT_BOT\static\chat.html` at lines 1830–1835 (notice `\n` to `<br>` conversion logic).
4. **Run Existing Test Suite**:
   Execute:
   ```powershell
   python -m pytest tests/test_academic_timeline.py tests/test_academic_static.py tests/test_token_service_domain.py tests/test_faq_forum.py -v
   ```
   All test cases pass, confirming baseline domain integrity.
