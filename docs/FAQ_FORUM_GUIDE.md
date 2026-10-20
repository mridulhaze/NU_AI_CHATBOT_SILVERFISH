# Integrated Professional FAQ Forum Guide
**National University Bangladesh AI Assistant**

## 1. Overview
The Integrated Professional FAQ Forum is embedded directly into the right-side panel of the student chatbot (`static/chat.html`). It enables students and faculty to browse, search, and vote on 676+ officially verified questions and answers from the National University knowledge corpus.

---

## 2. Layout & Design Language

### 2.1 Dynamic Split Layout (70% : 30% Toggle)
- **Mode A (Chat Focused — Default):**
  - **AI Chat Section:** 70% width
  - **FAQ Forum Panel:** 30% width
  - Activated by clicking anywhere on the chat container, typing into the input bar, selecting menu cards, or clicking "🤖 এআই-কে জিজ্ঞেস করুন".
- **Mode B (FAQ Focused — Expanded):**
  - **FAQ Forum Panel:** 70% width
  - **AI Chat Section:** 30% width
  - Activated whenever a student clicks on **any FAQ question** (in either the Top 10 list or the main FAQ stream) or clicks the `[⤢ ৭০% ফোরাম]` button.
  - In 70% mode, the FAQ cards automatically format into an expanded, readable 2-column grid.
  - The Chat section gently adjusts to 30% width with a compact card layout and a quick `[💬 চ্যাট ফোকাস (৭০%)]` pill.
- **Fluid Animation:** Controlled via GPU-accelerated cubic-bezier transitions (`transition: flex 380ms cubic-bezier(0.16, 1, 0.3, 1), width 380ms...`).
- **Responsive Mobile View:** On viewports under `1024px`, the system smoothly stacks both panels and provides quick header jumping.

### 2.2 Design System & Monochromatic Tokens
Following Apple's monochromatic design philosophy:
- Page Background: `var(--bg)` (`#F5F5F7` light, `#1C1C1E` dark)
- Card Surfaces: `var(--surface)` (`#FFFFFF` light, `#2C2C2E` dark)
- Hairline Borders: `var(--hairline)` (`rgba(0,0,0,0.08)` light, `rgba(255,255,255,0.10)` dark)
- Primary Text: `var(--text)` (`#1D1D1F` light, `#F5F5F7` dark)
- Secondary Text: `var(--text-secondary)` (`#6E6E73` light, `#98989D` dark)
- Official NU Accent: `var(--accent)` (`#006A4E` / `#008763`)

---

## 3. Core Functional Capabilities

### 3.1 🏆 Top 10 Most-Liked Section
- Pinned at the top of the forum panel.
- Displays the 10 most popular FAQs determined by `likes_count DESC`.
- Features gold (`🥇`), silver (`🥈`), and bronze (`🥉`) rank badges for top positions.
- Can be collapsed/expanded via the "লুকান ▲ / দেখান ▼" toggle.

### 3.2 Real-Time Search & Category Filtering
- **Debounced Live Search (250ms):** Supports searching in Bengali (e.g. `ভর্তি`, `ইনকোর্স`, `টিসি`, `সিজিপিএ`) and English (e.g. `TC`, `EMS`, `Re-scrutiny`).
- **Category Filter Dropdown:** 40+ structured categories with live question counts.
- **Sort Modes:**
  - `🏆 জনপ্রিয় (Most Liked)`
  - `🕒 সর্বশেষ (Latest)`
  - `📑 সকল (All)`

### 3.3 Interactive Like System
- Atomic like/unlike toggle via `POST /api/v1/faqs/{id}/like`.
- Session-based tracking: Each browser session maintains an isolated `sessionId` stored in `localStorage`.
- Heart icon dynamically transitions from outline to red filled with instant count updates across both the Top 10 list and the main stream.

### 3.4 🤖 "Ask AI About This FAQ" Injection
Every FAQ card includes an "🤖 এআই-কে জিজ্ঞেস করুন" action button. Clicking it:
1. Copies the exact FAQ question into the chatbot prompt input.
2. Automatically triggers `handleSend()` to run the question through the RAG engine and Gemini LLM.
3. Automatically scrolls the user smoothly to the conversation view.
