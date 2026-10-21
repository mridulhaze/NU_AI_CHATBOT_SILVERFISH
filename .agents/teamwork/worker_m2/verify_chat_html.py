import re

def verify_chat_html():
    with open("static/chat.html", "r", encoding="utf-8") as f:
        content = f.read()

    dom_ids = [
        "split-container", "chat-section", "faq-forum-panel", "faq-toggle-split-btn",
        "faq-toggle-split-text", "faq-search-input", "faq-clear-search", "faq-category-select",
        "faq-topic-active-name", "faq-topic-tags", "faq-list-count-label", "faq-active-filter-badge",
        "faq-main-list", "faq-empty-state", "faq-load-more-wrap", "faq-load-more-btn",
        "chat-focus-pill", "user-input", "send-btn"
    ]
    missing_ids = [d for d in dom_ids if f'id="{d}"' not in content and f"id='{d}'" not in content]
    print(f"Missing DOM IDs: {missing_ids}")
    assert not missing_ids, f"Missing IDs: {missing_ids}"

    functions = [
        "handleFaqSearch", "handleTopicTagClick", "askAiAboutFaq", "handleFaqLikeClick",
        "copyFaqToClipboard", "setSplitMode", "toggleSplitMode", "handleChatSectionClick",
        "handleFaqQuestionClick", "toggleFaqExpand", "clearFaqSearch", "clearFaqFilters",
        "loadMoreFaqs", "refreshFaqData", "initFaqForum"
    ]
    missing_funcs = [f for f in functions if f not in content]
    print(f"Missing functions: {missing_funcs}")
    assert not missing_funcs, f"Missing functions: {missing_funcs}"

    # Twitter visual motifs check
    assert "𝕏" not in content, "Residual 𝕏 found in chat.html"
    assert "@nu_official" not in content, "Residual @nu_official found in chat.html"

    # Monochromatic classes & styles check
    assert "x-topic-pill" in content, "x-topic-pill class missing"
    assert "no-scrollbar" in content, "no-scrollbar class missing"
    assert "flex items-center gap-2 overflow-x-auto no-scrollbar py-2.5" in content, "Horizontal scroll pill bar classes missing"
    assert "data-split" in content, "data-split attribute missing"
    assert "✓ কপিড" in content, "✓ কপিড visual feedback text missing"
    assert "POST /api/v1/faqs/" in content or "/api/v1/faqs/${faqId}/like" in content or "/api/v1/faqs/${item.id}/like" in content, "Like API endpoint missing"

    print("ALL VERIFICATIONS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    verify_chat_html()
