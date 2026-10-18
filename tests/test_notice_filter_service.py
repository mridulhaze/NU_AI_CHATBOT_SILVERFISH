import pytest
from datetime import datetime
from backend.services.notice_service import get_notice_filter_service, NoticeFilterService, parse_notice_date
from backend.rag_engine import RAGEngine
from backend.models import ChatResponse

@pytest.fixture
def notice_service():
    return get_notice_filter_service()

@pytest.fixture
def rag_engine():
    return RAGEngine()

class TestNoticeFilterService:
    def test_filter_extraction_llb(self, notice_service):
        q = "LLB formfillup notice dekhan"
        filters = notice_service.extract_filters(q)
        subject_ids = [s["id"] for s in filters.subjects]
        action_ids = [a["id"] for a in filters.actions]
        
        assert "LLB" in subject_ids
        assert "FORM_FILLUP" in action_ids

    def test_filter_extraction_cse_sem_year(self, notice_service):
        q = "CSE 8th semester 2024 form fill up notice"
        filters = notice_service.extract_filters(q)
        subject_ids = [s["id"] for s in filters.subjects]
        action_ids = [a["id"] for a in filters.actions]
        
        assert "CSE" in subject_ids
        assert "FORM_FILLUP" in action_ids
        assert "2024" in filters.years or "২০২৪" in filters.years
        assert any("৮ম" in s or "8th" in s for s in filters.semesters)

    def test_date_parser_formats(self):
        # Bengali date string
        d1 = parse_notice_date("২৩ আগস্ট ২০২৬")
        assert d1.year == 2026 and d1.month == 8 and d1.day == 23

        # English date string
        d2 = parse_notice_date("August 25, 2026")
        assert d2.year == 2026 and d2.month == 8 and d2.day == 25

        # URL pub_date
        d3 = parse_notice_date("2026", url_str="https://www.nu.ac.bd/uploads/2026/08/pub_date_23082026.pdf")
        assert d3.year == 2026 and d3.month == 8 and d3.day == 23

        # Dot format URL
        d4 = parse_notice_date("Notice", url_str="https://www.nu.ac.bd/uploads/pub_date_06.01.2016.pdf")
        assert d4.year == 2016 and d4.month == 1 and d4.day == 6

    def test_strict_isolation_llb_no_unrelated_notices(self, notice_service):
        res = notice_service.process_notice_query("show me all LLB recent notice", limit=6)
        assert res.has_subject_filter is True
        assert len(res.matched_notices) > 0
        
        # Verify that EVERY matched notice explicitly mentions LLB in title and NO admin contract notices
        for n in res.matched_notices:
            title_lower = n["title"].lower()
            assert any(term in title_lower for term in ["llb", "ll.b", "এলএলবি", "এল.এল.বি", "আইন বিভাগ", "আইন কোর্স"])
            assert "কর্মসম্পাদন চুক্তি" not in title_lower
            assert "cse" not in title_lower

    def test_chrono_sorting_descending(self, notice_service):
        res = notice_service.process_notice_query("show me all LLB recent notice", limit=8)
        assert len(res.matched_notices) > 1
        
        dates = [n.get("parsed_date", datetime(2000, 1, 1)) for n in res.matched_notices]
        # Verify descending order (each date is >= the next date)
        for i in range(len(dates) - 1):
            assert dates[i] >= dates[i+1], f"Notices not chronologically sorted: {dates[i]} vs {dates[i+1]}"

    def test_strict_isolation_cse(self, notice_service):
        res = notice_service.process_notice_query("CSE 8th semester form fillup notice", limit=5)
        assert res.has_subject_filter is True
        assert len(res.matched_notices) > 0
        
        for n in res.matched_notices:
            combined = (n["title"] + " " + n["raw_text"]).lower()
            assert any(term in combined for term in ["cse", "কম্পিউটার সায়েন্স", "কম্পিউটার সায়েন্স", "computer science"])

    def test_strict_isolation_degree(self, notice_service):
        res = notice_service.process_notice_query("২০২৪ সালের ডিগ্রি নোটিশ দেখাও", limit=5)
        assert res.has_subject_filter is True
        assert len(res.matched_notices) > 0
        
        for n in res.matched_notices:
            combined = (n["title"] + " " + n["raw_text"]).lower()
            assert any(term in combined for term in ["ডিগ্রি", "ডিগ্রী", "degree"])

    def test_fallback_zero_unrelated_dumping(self, notice_service):
        # Query with an uncommon subject that has no notices in DB
        res = notice_service.process_notice_query("মহাকাশ বিজ্ঞান বিভাগের ২০২৬ সালের নোটিশ", limit=5)
        assert res.has_subject_filter is True
        assert res.is_empty_subject_result is True
        assert len(res.matched_notices) == 0
        # Check polite fallback text
        assert "নোটিশ পাওয়া যায়নি" in res.formatted_reply or "সক্রিয় নেই" in res.formatted_reply
        assert "nu.ac.bd" in res.formatted_reply
        # Ensure zero unrelated notices dumped
        assert len(res.citations) == 0 or all("nu.ac.bd" in c.url for c in res.citations)

    def test_general_notices(self, notice_service):
        res = notice_service.process_notice_query("সাম্প্রতিক নোটিশ কি?", limit=4)
        assert res.filters.is_general_notice_query is True
        assert len(res.matched_notices) > 0
        assert "জাতীয় বিশ্ববিদ্যালয়ের সাম্প্রতিক নোটিশসমূহ" in res.formatted_reply

    def test_rag_engine_integration_llb(self, rag_engine):
        response: ChatResponse = rag_engine.answer_query("show me all notice on LLB formfillup", history=[])
        assert response.intent == "notices"
        assert response.confidence >= 0.90
        assert "এলএলবি" in response.reply or "LLB" in response.reply
        assert "CSE" not in response.reply
        assert "কর্মসম্পাদন চুক্তি" not in response.reply

    def test_rag_engine_integration_recent(self, rag_engine):
        response: ChatResponse = rag_engine.answer_query("Recent notices", history=[])
        assert response.intent == "notices"
        assert response.confidence >= 0.90
        assert len(response.citations) > 0

