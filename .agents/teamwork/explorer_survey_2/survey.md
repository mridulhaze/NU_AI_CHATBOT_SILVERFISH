# Comprehensive Survey Report: FAQ Panel & AI Chat Integration
**National University Bangladesh AI Assistant**
**Explorer**: Teamwork Explorer 2 (`explorer_survey_2`)
**Target File**: `static/chat.html` (and associated backend services `backend/api/faq_routes.py`, `backend/services/faq_service.py`, `tests/test_faq_forum.py`)
**Date**: October 21, 2026

---

## 1. Executive Summary

This survey provides a complete architectural map and technical evaluation of the student-facing interface in `static/chat.html`, focusing specifically on the **Integrated FAQ Panel**, the **AI Chat Console**, and the dynamic **70% / 30% Split Layout System**.

The current implementation provides a rich, responsive interface with dual-mode layout flexibility, real-time debounced Bengali/English search, category topic tags, atomic like/unlike voting backed by SQLite, clipboard copy with feedback, and instant question injection into the AI counselor. However, visual elements retain Twitter/X style motifs (e.g. `𝕏` avatar, `@nu_official` handles, and blue verified badges) that diverge from the clean, calm, Apple Support and Stripe monochromatic design language stipulated in `ORIGINAL_REQUEST.md`.

Both backend and frontend APIs are operational, and the integration test suite (`tests/test_faq_forum.py` and `tests/test_token_service_domain.py`) passes 100% with 0 errors.

---

## 2. Architectural Context & File Manifest

### 2.1 File Map
- **Primary Viewport**: `static/chat.html` (81.5 KB, 1,918 lines)
  - Hosted at endpoints: `GET /chat`, `GET /student`
  - Self-contained HTML5 single-page application containing Tailwind CSS (CDN), embedded CSS tokens in `<style>`, SVG asset vectors, and vanilla JavaScript controllers.
- **Backend API Endpoints**: `backend/api/faq_routes.py`
  - `GET /api/v1/faqs` (listing, search, category filter, pagination, sort)
  - `GET /api/v1/faqs/top-liked` (top 10 pinned popular questions)
  - `GET /api/v1/faqs/categories` (list categories with active counts)
  - `GET /api/v1/faqs/{id}` (detail by id)
  - `POST /api/v1/faqs/{id}/like` (atomic toggle like/unlike with session isolation)
  - `POST /api/v1/faqs/sync` (idempotent sync from `FAQ/faq.txt`)
- **Backend Service**: `backend/services/faq_service.py`
  - Connects to `data/nu_assistant.db` (`faqs` and `faq_likes` tables)
  - Seed source: `FAQ/faq.txt` (676+ verified academic Q&As)
- **Automated Test Suite**:
  - `tests/test_faq_forum.py` (6 tests: file parsing, sync idempotency, listing/filtering, bilingual search, like toggle, top-liked order) — **100% PASS**
  - `tests/test_token_service_domain.py` (4 domain tests) — **100% PASS**

---

## 3. Dynamic Split Layout (70% : 30% Toggle System)

### 3.1 Mechanism & State Management
The layout is wrapped in a container that controls child dimensions using a custom attribute:
```html
<main id="split-container" data-split="chat" class="split-layout ...">
  <section id="chat-section">...</section>
  <aside id="faq-forum-panel">...</aside>
</main>
```

The active state is stored in JavaScript variable:
```javascript
let currentSplitMode = "chat"; // "chat" = 70% Chat / 30% FAQ; "faq" = 70% FAQ / 30% Chat
```

### 3.2 Desktop CSS Rules (`min-width: 1024px`)
Transitions utilize Apple-standard cubic-bezier acceleration for fluid panel resizing:
```css
#chat-section, #faq-forum-panel {
  transition: flex 380ms cubic-bezier(0.16, 1, 0.3, 1), 
              max-width 380ms cubic-bezier(0.16, 1, 0.3, 1), 
              width 380ms cubic-bezier(0.16, 1, 0.3, 1);
}

/* Mode A: Chat Focused (Default) */
.split-layout[data-split="chat"] #chat-section {
  flex: 0 0 70%;
  max-width: 70%;
  width: 70%;
}
.split-layout[data-split="chat"] #faq-forum-panel {
  flex: 0 0 calc(30% - 1.5rem);
  max-width: calc(30% - 1.5rem);
  width: calc(30% - 1.5rem);
}

/* Mode B: FAQ Focused */
.split-layout[data-split="faq"] #chat-section {
  flex: 0 0 calc(30% - 1.5rem);
  max-width: calc(30% - 1.5rem);
  width: calc(30% - 1.5rem);
}
.split-layout[data-split="faq"] #faq-forum-panel {
  flex: 0 0 70%;
  max-width: 70%;
  width: 70%;
}
```

### 3.3 Dynamic Content Re-flow in Alternate Modes
When switching from Chat (70%) to FAQ (70%):
- **Chat Section Adaptation**:
  - The 3x3 menu grid (`#cards-3x3-grid`) dynamically switches from a 3-column layout into a compact single-column stack:
    ```css
    .split-layout[data-split="faq"] #cards-3x3-grid {
      grid-template-columns: repeat(1, minmax(0, 1fr)) !important;
      gap: 0.625rem;
    }
    ```
  - Card padding, icon circles (from 40px to 32px), and typography shrink to prevent truncation.
  - A quick restore pill (`#chat-focus-pill`) appears at top right: `💬 চ্যাট ফোকাস (৭০%)`.
- **FAQ Section Adaptation**:
  - The FAQ cards container (`#faq-main-list`) expands from a single column into a 2-column balanced grid:
    ```css
    .split-layout[data-split="faq"] #faq-main-list {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 0.75rem;
      max-height: 620px;
    }
    ```
  - Topic pill tag container max-height expands from `110px` to `140px`.

### 3.4 Mobile / Responsive Behavior (`< 1024px`)
- On screens under 1024px width, `split-layout` switches to standard column stacking (`flex flex-col`).
- A mobile header action button (`scrollToFaqForum()`) is displayed:
  ```html
  <button onclick="scrollToFaqForum()" class="apple-quiet-btn lg:hidden" title="প্রশ্নোত্তর ফোরামে যান">
  ```
  which invokes `element.scrollIntoView({ behavior: "smooth", block: "start" })`.

---

## 4. DOM Catalog & Element ID Inventory

| DOM ID | Tag / Role | CSS Classes | Functionality & Event Handlers |
|---|---|---|---|
| `split-container` | `<main>` | `split-layout flex-1 max-w-[1440px] ...` | Hosts `data-split` attribute ("chat" or "faq"). Handles responsive flex transitions. |
| `chat-section` | `<section>` | `w-full flex flex-col justify-between ...` | Left column. `onclick="handleChatSectionClick(event)"` switches split to chat mode if clicked while in FAQ mode. |
| `welcome-view` | `<div>` | `space-y-4` | Displays 3x3 menu cards before user sends first message. Hidden upon conversation start. |
| `chat-focus-pill` | `<button>` | `hidden apple-quiet-btn ...` | Quick button visible only in FAQ 70% mode to restore chat to 70%. `onclick="setSplitMode('chat')"`. |
| `cards-3x3-grid` | `<div>` | `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 ...` | Hosts the 9 official academic service cards with SVG icons. |
| `conversation-view` | `<div>` | `hidden flex-1 space-y-4 overflow-y-auto ...` | Scrollable message container shown during active chat sessions. |
| `messages-container` | `<div>` | `space-y-4` | Container where `.user-bubble` and `.assistant-bubble` DOM nodes are dynamically appended. |
| `chips-bar` | `<div>` | `flex items-center gap-2 overflow-x-auto no-scrollbar` | Carousel of `.apple-chip` pills for quick menu and subject suggestions. |
| `user-input` | `<input>` | `flex-1 bg-transparent text-[14px] ...` | Main chat prompt input. `onfocus="setSplitMode('chat')"`, `onkeydown="if(event.key === 'Enter') handleSend();"`. |
| `send-btn` | `<button>` | `apple-send-btn` | Submits chat prompt via `onclick="handleSend()"`. |
| `theme-icon` | `<svg>` | `w-4 h-4` | Icon container toggled between Sun and Moon based on active color theme. |
| `faq-forum-panel` | `<aside>` | `w-full flex flex-col apple-faq-panel` | Right column hosting the full FAQ forum, search, topics, and question stream. |
| `faq-toggle-split-btn` | `<button>` | `apple-quiet-btn text-[11px] ...` | Header toggle button invoking `onclick="toggleSplitMode()"`. |
| `faq-toggle-split-text` | `<span>` | Text node | Displays `⤢ ৭০% ফোরাম` or `⤡ ৭০% চ্যাট`. |
| `faq-search-input` | `<input>` | `w-full bg-[var(--bg)] rounded-full py-2 pl-9 pr-8 ...` | Live search input with `oninput="handleFaqSearch(this.value)"`. |
| `faq-clear-search` | `<button>` | `hidden absolute right-3 ...` | "✕" icon to clear search query and re-render default stream. `onclick="clearFaqSearch()"`. |
| `faq-category-select` | `<select>` | `hidden` | Hidden dropdown maintained for programmatic category selection synchronization. |
| `faq-topic-active-name`| `<span>` | `text-[10.5px] text-[var(--text-secondary)] font-medium` | Header label indicating the currently active topic name (e.g. `#ভর্তি` or `সব বিষয়`). |
| `faq-topic-tags` | `<div>` | `flex flex-wrap gap-1.5 max-h-[110px] overflow-y-auto` | Holds dynamic `.x-topic-pill` buttons. |
| `faq-list-count-label` | `<span>` | `text-[11.5px] font-semibold text-[var(--text-secondary)]` | Displays count label: `টাইমলাইন ও প্রশ্নোত্তর (${items.length}/${total})`. |
| `faq-active-filter-badge`| `<span>` | `text-[10.5px] text-[var(--accent)] font-medium` | Secondary badge displaying active category name. |
| `faq-main-list` | `<div>` | `space-y-2.5 overflow-y-auto max-h-[500px] thin-scrollbar` | Scrollable stream rendering FAQ card articles. |
| `faq-empty-state` | `<div>` | `hidden py-8 text-center text-xs space-y-2` | Displays empty indicator and filter reset button when 0 items match. |
| `faq-load-more-wrap` | `<div>` | `hidden pt-3 text-center border-t ...` | Wrapper shown when `items.length < total`. |
| `faq-load-more-btn` | `<button>` | `apple-quiet-btn text-xs font-semibold px-4 py-1.5` | Triggers `onclick="loadMoreFaqs()"`. |
| `staff-auth-modal` | `<div>` | `fixed inset-0 z-50 hidden ...` | Password-protected modal for staff and solver portal access. |

---

## 5. FAQ Search & Category Filtering Architecture

### 5.1 Debounced Search Engine
- Handler: `handleFaqSearch(val)`
- Delay: 250 milliseconds
- Operation:
  ```javascript
  function handleFaqSearch(val) {
    clearTimeout(faqSearchTimer);
    faqState.search = val;
    const clearBtn = document.getElementById("faq-clear-search");
    if (clearBtn) {
      if (val.trim()) clearBtn.classList.remove("hidden");
      else clearBtn.classList.add("hidden");
    }
    faqSearchTimer = setTimeout(() => {
      loadFaqList(true);
    }, 250);
  }
  ```
- Bilingual Support: Searches both Bengali script (e.g. `ভর্তি`, `ইনকোর্স`, `মূল সনদ`, `টিসি`) and English abbreviations (e.g. `TC`, `EMS`, `CGPA`, `BBA`, `CSE`).

### 5.2 Category Topic Tags (`#টপিকসমূহ`)
- Fetched via `GET /api/v1/faqs/categories`.
- Renders:
  1. Default root pill: `#সকল_টপিক` with aggregate count across all questions.
  2. Dynamic hashtag pills: `#${category_name}` with individual item count.
- Click handler: `handleTopicTagClick(catName)`:
  - Updates `faqState.category`.
  - Toggles active class on clicked pill: `.x-topic-pill.active` (high-contrast monochromatic inversion: `background: var(--text); color: var(--surface)`).
  - Triggers `loadFaqList(true)`.

---

## 6. Accordion Cards Behavior & Animations

### 6.1 Card Structure
Each FAQ item is rendered as an `<article class="x-feed-card">` with an embedded accordion pattern:
1. **Header & Question**:
   - Always visible.
   - Truncated question text formatted in high-contrast bold typography (`text-[13.5px] font-semibold text-[var(--text)]`).
2. **Preview Snippet**:
   - Tag: `<div id="faq-snippet-list-${item.id}">`
   - Class: `line-clamp-2 text-xs text-[var(--text-secondary)] mt-1.5 leading-relaxed`
   - Visible when collapsed, provides immediate readability without taking excessive vertical space.
3. **Full Answer Drawer (Accordion Body)**:
   - Tag: `<div id="faq-ans-list-${item.id}" class="hidden mt-2.5 pt-2 border-t border-[var(--hairline)]">`
   - Inner surface: `p-3 rounded-xl bg-[var(--bg)] border border-[var(--hairline)] text-xs text-[var(--text)] leading-relaxed whitespace-pre-line`.
4. **Interaction Trigger**:
   - Clicking the question card invokes:
     ```javascript
     function handleFaqQuestionClick(suffix) {
       setSplitMode("faq");
       toggleFaqExpand(suffix);
     }
     ```
   - Clicking the explicit "বিস্তারিত ▼" / "সংক্ষেপ করুন ▲" button toggles only the expansion without forcing panel split.
   - Accordion toggle function:
     ```javascript
     function toggleFaqExpand(suffix) {
       const fullAns = document.getElementById(`faq-ans-${suffix}`);
       const snippet = document.getElementById(`faq-snippet-${suffix}`);
       const label = document.getElementById(`expand-label-${suffix}`);
       if (!fullAns) return;

       const isHidden = fullAns.classList.contains("hidden");
       if (isHidden) {
         fullAns.classList.remove("hidden");
         if (snippet) snippet.classList.add("hidden");
         if (label) label.innerText = "সংক্ষেপ করুন ▲";
       } else {
         fullAns.classList.add("hidden");
         if (snippet) snippet.classList.remove("hidden");
         if (label) label.innerText = "বিস্তারিত ▼";
       }
     }
     ```

---

## 7. Action Controls Specification

### 7.1 "এআই উত্তর" (Ask AI) Prompt Injection
- **DOM Element**: `<button onclick="event.stopPropagation(); askAiAboutFaq('...')" class="x-action-btn reply">`
- **Icon**: Chat bubble SVG icon.
- **Workflow**:
  1. `event.stopPropagation()` prevents parent accordion trigger.
  2. Sets split mode to Chat: `setSplitMode("chat")`.
  3. Injects the verbatim question text into `#user-input.value`.
  4. Triggers `handleSend()` immediately to send prompt to `/api/v1/chat`.
  5. If on viewport `< 1024px`, scrolls window smoothly to top to show conversation view.

### 7.2 Inline Atomic Like Counter with Heart
- **DOM Element**: `<button onclick="event.stopPropagation(); handleFaqLikeClick(${item.id})" class="x-action-btn like ${isLiked ? 'liked' : ''}" id="like-btn-list-${item.id}">`
- **Session Identification**:
  - `localStorage.getItem("nu_chat_session_id")` generated on first load:
    `student_sess_` + random 8-character string.
- **Backend API**:
  - `POST /api/v1/faqs/${faqId}/like` with payload `{"session_id": sessionId}`.
  - Returns: `{"faq_id": int, "likes_count": int, "has_liked": bool}`.
- **Visual State**:
  - Unliked: Gray outline heart icon, `fill="none"`, `stroke="currentColor"`.
  - Liked: Crimson red `#e11d48`, `fill="currentColor"`, font-weight 600.
  - Multi-node sync: Updates all `.like-counter-${faqId}` elements across the DOM simultaneously.

### 7.3 One-Click Copy with Instant Feedback
- **DOM Element**: `<button onclick="event.stopPropagation(); copyFaqToClipboard(..., this)" class="x-action-btn share">`
- **Formatted Text**:
  ```text
  প্রশ্ন: [Question text]

  উত্তর:
  [Answer text]

  (সূত্র: জাতীয় বিশ্ববিদ্যালয় অফিশিয়াল হেল্পডেস্ক)
  ```
- **Feedback Lifecycle**:
  1. Copies via `navigator.clipboard.writeText(text)` (with fallback `execCommand`).
  2. Replaces "কপি" label with `✓ কপিড` in emerald green (`text-emerald-500`).
  3. Reverts after 1,800ms via `setTimeout()`.

---

## 8. Monochromatic Styling & Theming System

### 8.1 Apple & Stripe Design Tokens
All styling variables are defined cleanly in `:root` and `[data-theme="dark"]`:

```css
:root {
  --bg: #F5F5F7;
  --surface: #FFFFFF;
  --text: #1D1D1F;
  --text-secondary: #6E6E73;
  --hairline: rgba(0, 0, 0, 0.08);
  --hairline-hover: rgba(0, 0, 0, 0.16);
  --accent: #006A4E; /* Official National University Green */
  --accent-hover: #00563F;
  --accent-light: rgba(0, 106, 78, 0.12);
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 8px 24px rgba(0, 0, 0, 0.08);
  --radius-card: 20px;
  --radius-pill: 999px;
  --radius-input: 24px;
}

[data-theme="dark"] {
  --bg: #1C1C1E;
  --surface: #2C2C2E;
  --text: #F5F5F7;
  --text-secondary: #98989D;
  --hairline: rgba(255, 255, 255, 0.10);
  --hairline-hover: rgba(255, 255, 255, 0.20);
  --accent: #008763;
  --accent-hover: #059669;
  --accent-light: rgba(0, 135, 99, 0.22);
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.25);
  --shadow-md: 0 8px 24px rgba(0, 0, 0, 0.45);
}
```

### 8.2 Light / Dark Theme Switching
- Checked automatically via `localStorage.getItem("nu_theme")` and `window.matchMedia("(prefers-color-scheme: dark)")`.
- Toggled via `toggleTheme()` button in the header.
- Dynamic SVG update: Sun icon in light mode, crescent Moon icon in dark mode.

---

## 9. Edge Cases & Failure Modes

1. **High Category Volume Wrapping**:
   - There are 25+ academic categories. In `#faq-topic-tags`, rendering all pills in a flex-wrap container with `max-h-[110px]` introduces vertical scrolling within the top filter area.
   - *Design Opportunity*: Converting to a single-row horizontal pill carousel (`overflow-x-auto no-scrollbar` matching the chat chips bar `#chips-bar`) gives a cleaner, Stripe-like feel.
2. **Long Bengali Answers & Complex Markdown**:
   - Some FAQ answers have multi-paragraph instructions or tabular breakdown. The container uses `whitespace-pre-line`, which accurately preserves paragraph breaks.
3. **Optimistic Like Voting Under Network Latency**:
   - `handleFaqLikeClick` awaits the network response before changing the UI. If a user clicks rapidly, adding optimistic toggling or a debounced disabled state prevents duplicate network requests.
4. **Clipboard Permissions in Cross-Origin Embeds**:
   - When embedded via iframe (as demonstrated in `static/nu-chat-widget.js`), `navigator.clipboard.writeText()` may throw a permission error. The existing code handles this via a `textarea` fallback `document.execCommand('copy')`.
5. **Twitter / X Aesthetic vs. Apple Monochromatic Specification**:
   - The current UI references Twitter / X branding (`𝕏` avatar, `@nu_official` handles, and Twitter blue `#1d9bf0` verified badges). Replacing these with official University seals (`nu_logo.png` or monoline graduation/document icons) and monochromatic Apple Support badges will align the interface with R2 requirements.

---

## 10. Verification & Test Suite Status

The test suites were executed and verified:
- **FAQ Forum Test Suite**:
  - Command: `python -m pytest tests/test_faq_forum.py -v`
  - Result: `6 passed, 0 failures` (Execution duration: 23.11s)
- **Token Domain Service Test Suite**:
  - Command: `python -m pytest tests/test_token_service_domain.py -v`
  - Result: `4 passed, 0 failures` (Execution duration: 6.99s)
