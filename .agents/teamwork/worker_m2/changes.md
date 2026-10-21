# Changes Summary — Milestone 2

**Agent**: `worker_m2`  
**File Modified**: `static/chat.html` (exclusive write ownership)  
**Date**: 2026-10-21  

---

## 1. Twitter / X Visual Motifs Replacement
- **FAQ Forum Header Avatar**:
  - Removed black circular avatar with mathematical double-struck `𝕏`.
  - Replaced with clean official NU Monogram / Shield emblem in an Apple-style rounded container (`bg-[var(--surface)] border border-[var(--hairline)] text-[var(--accent)]`).
- **FAQ Forum Header Title & Verified Badge**:
  - Replaced "এক্সপ্লোর ফোরাম" and Twitter blue verified circle with "অফিশিয়াল প্রশ্নোত্তর ও নির্দেশিকা" and monochromatic badge:
    `<span class="x-verified-badge" title="জাতীয় বিশ্ববিদ্যালয় অফিশিয়াল ভেরিফাইড">✓ ভেরিফাইড</span>` (`bg-[var(--accent-light)] text-[var(--accent)] border border-[var(--accent)]/16`).
  - Updated subtitle to "৬৭০+ পরীক্ষিত একাডেমিক প্রশ্ন ও দিকনির্দেশনা".
- **FAQ Cards Header**:
  - Replaced black `NU` avatar with clean official graduation emblem badge SVG.
  - Removed Twitter `@nu_official` handle.
  - Replaced Twitter blue `#1d9bf0` badge with monochromatic official badge:
    `<span class="x-verified-badge" title="জাতীয় বিশ্ববিদ্যালয় অফিশিয়াল ভেরিফাইড তথ্য">✓ ভেরিফাইড</span>`.
  - Cleaned up category hashtag pill with official hairline border:
    `bg-[var(--accent-light)] border border-[var(--accent)]/10 text-[var(--accent)]`.

## 2. Horizontal Category Scroll Pills Bar
- **Markup Refactoring**:
  - Updated `#faq-topic-tags` container to:
    `class="flex items-center gap-2 overflow-x-auto no-scrollbar py-2.5"`
  - Preserved `#সকল_টপিক` and dynamic `#${category_name}` hashtag pills.
- **Monochromatic Apple/Stripe Styling**:
  - Inactive state: subtle outline pill (`bg-white border border-[rgba(0,0,0,0.08)] text-[#6E6E73] hover:text-[#1D1D1F] hover:bg-[#F5F5F7]`).
  - Active state: crisp monochromatic pill (`bg-[#1D1D1F] text-white`).
  - Added full dark mode support: dark surface (`#2C2C2E`), subtle hairline border (`rgba(255,255,255,0.10)`), and text (`#98989D` / `#F5F5F7`).
  - Removed old desktop CSS `max-height: 140px;` constraint so category pills remain a single-row horizontal scroll carousel in both 30% and 70% FAQ modes.

## 3. Search Bar
- **Clean Monochromatic Input**:
  - Retained `#faq-search-input` with instant 250ms debounced filtering (`handleFaqSearch`).
  - Enhanced styling with Apple Support quiet input tokens:
    `bg-[var(--bg)] border border-[var(--hairline)] hover:border-[var(--hairline-hover)] rounded-full py-2.5 pl-9 pr-9 text-xs text-[var(--text)] focus:outline-none focus:border-[var(--accent)] focus:bg-[var(--surface)] transition-all shadow-2xs`.
  - Added clean search icon SVG and circular quiet clear button (`#faq-clear-search`).

## 4. Sleek Accordion Cards & Disclosure Chevron
- **Card Aesthetics**:
  - Refined `.x-feed-card` with generous whitespace (`padding: 15px 16px`), crisp typography, and subtle border hover states.
  - Preview snippet (`#faq-snippet-list-${item.id}`) remains 2-line clamp.
  - Answer drawer (`#faq-ans-list-${item.id}`) has smooth transition class `.faq-drawer` (`cubic-bezier(0.16, 1, 0.3, 1)`).
- **Smooth Chevron Rotation**:
  - Accordion expand button now includes a disclosure chevron:
    `<svg id="expand-chevron-list-${item.id}" class="w-3.5 h-3.5 text-[var(--accent)] transition-transform duration-300 transform" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">...`
  - In `toggleFaqExpand(suffix)`, toggles `.rotate-180` and smoothly updates label between "বিস্তারিত" and "সংক্ষেপ করুন".

## 5. Inline Action Controls
- **Atomic Like Counter**:
  - Heart icon SVG calling `POST /api/v1/faqs/${item.id}/like` with session ID from `localStorage`.
  - Monochromatic outline when unliked, crimson `#e11d48` when liked.
  - Multi-node counter sync via `.like-counter-${item.id}` preserved.
- **"এআই উত্তর" (Ask AI)**:
  - Quiet chat bubble icon button.
  - Injects question into chat `#user-input` and triggers `handleSend()`.
  - Switches split mode smoothly to chat (`setSplitMode("chat")`).
- **One-Click Copy**:
  - Formatted text copy with `✓ কপিড` visual feedback for 1,800ms.

## 6. Dynamic 70%/30% Split Layout
- Preserved cubic-bezier flex transitions (`data-split="chat"` vs `data-split="faq"`).
- Mode A (70% Chat / 30% FAQ) and Mode B (30% Chat / 70% FAQ) fully intact.
- 2-column balanced grid for `#faq-main-list` in 70% FAQ mode preserved.

## 7. Contract & ID Preservation
- All DOM IDs (`#split-container`, `#chat-section`, `#faq-forum-panel`, `#faq-search-input`, `#faq-clear-search`, `#faq-category-select`, `#faq-topic-active-name`, `#faq-topic-tags`, `#faq-list-count-label`, `#faq-active-filter-badge`, `#faq-main-list`, `#faq-empty-state`, `#faq-load-more-wrap`, `#faq-load-more-btn`, `#chat-focus-pill`, `#user-input`, `#send-btn`) preserved 100%.
- All JavaScript controller functions (`handleFaqSearch`, `handleTopicTagClick`, `askAiAboutFaq`, `handleFaqLikeClick`, `copyFaqToClipboard`, `setSplitMode`, `toggleSplitMode`, `handleChatSectionClick`, `handleFaqQuestionClick`, `toggleFaqExpand`, `clearFaqSearch`, `clearFaqFilters`, `loadMoreFaqs`, `refreshFaqData`, `initFaqForum`) preserved 100%.
