# Integrated Professional FAQ Forum Guide
**National University Bangladesh AI Assistant**

## 1. Overview
The Integrated Professional FAQ Forum is embedded directly into the right-side panel of the student chatbot (`static/chat.html`). It enables students and faculty to browse, search, and vote on 676+ officially verified questions and answers from the National University knowledge corpus.

---

## 2. Layout & Design Language

### 2.1 Two-Column Desktop Architecture
- **Left Column (~65% width):** AI Counselor conversational assistant, 3x3 academic examination cards, category filter chips, and floating natural language input.
- **Right Column (~35% width):** High-density, forum-style FAQ panel (`apple-faq-panel`).
- **Responsive Mobile View:** Collapses into a stacked column with quick navigation buttons in the sticky header (`[ফোরাম]`) and smooth scrolling to the FAQ forum section.

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
