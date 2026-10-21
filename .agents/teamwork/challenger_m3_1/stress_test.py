import sys
import os
sys.path.insert(0, os.path.abspath("."))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
import re
from datetime import date
from backend.services.academic_exam_service import (
    evaluate_milestone_status,
    render_exam_card_timeline_bar,
    format_exam_card_markdown,
    process_academic_exam_query,
    render_professional_courses_selection_cards,
    render_professional_semesters_cards,
    find_professional_course,
    find_semester
)
from db.sql_store import get_sql_store

def run_stress_tests():
    print("====================================================")
    print("CHALLENGER 1 ADVERSARIAL STRESS TEST SUITE")
    print("====================================================")
    
    # ----------------------------------------------------
    # SECTION 1: Status Calculation & Accuracy Rules
    # ----------------------------------------------------
    print("\n--- SECTION 1: Status Calculation & Accuracy Rules ---")
    today_bd = date(2026, 10, 21)
    
    # Rule 1: Past date without confirmation MUST be passed_unconfirmed with 'তারিখ অতিক্রান্ত'
    past_dates = ["01-01-2023", "15 May 2024", "2025-12-31", "10/05/2026"]
    for p_date in past_dates:
        lbl, st_type, is_comp, desc = evaluate_milestone_status("exam_date", p_date, {}, today_bd)
        assert is_comp is False, f"Failed: past date {p_date} marked as completed!"
        assert st_type == "passed_unconfirmed", f"Failed: status_type for {p_date} should be 'passed_unconfirmed', got {st_type}"
        assert "তারিখ অতিক্রান্ত" in lbl, f"Failed: label for {p_date} does not contain 'তারিখ অতিক্রান্ত': {lbl}"
    print("[PASS] Past dates correctly marked as passed_unconfirmed / তারিখ অতিক্রান্ত (is_comp=False)")
    
    # Rule 2: Today's date MUST be 'today' with 'আজ'
    lbl, st_type, is_comp, desc = evaluate_milestone_status("exam_date", "21-10-2026", {}, today_bd)
    assert is_comp is False
    assert st_type == "today"
    assert "আজ" in lbl
    print("[PASS] Today's date correctly evaluated as 'today' / 'আজ'")
    
    # Rule 3: Future date MUST be 'upcoming' with 'আসন্ন'
    future_dates = ["22-10-2026", "15 November 2026", "2027-01-01"]
    for f_date in future_dates:
        lbl, st_type, is_comp, desc = evaluate_milestone_status("exam_date", f_date, {}, today_bd)
        assert is_comp is False
        assert st_type == "upcoming"
        assert "আসন্ন" in lbl
    print("[PASS] Future dates correctly evaluated as 'upcoming' / 'আসন্ন'")
    
    # Rule 4: Routine URL MUST be 'published' with 'প্রকাশিত'
    routine_urls = [
        "http://www.nu.ac.bd/routine_2026.pdf",
        "https://nu.edu.bd/uploads/routine.pdf"
    ]
    for r_url in routine_urls:
        lbl, st_type, is_comp, desc = evaluate_milestone_status("routine_publication_date", r_url, {}, today_bd)
        assert is_comp is True
        assert st_type == "published"
        assert "প্রকাশিত" in lbl
    print("[PASS] Live routine URLs correctly evaluated as 'published' / 'প্রকাশিত' (is_comp=True)")

    # ----------------------------------------------------
    # SECTION 2: Official Portal URLs & Prohibited URLs
    # ----------------------------------------------------
    print("\n--- SECTION 2: Portal URLs & Prohibited URLs ---")
    official_urls = [
        "http://103.113.200.68/nu-app/",
        "http://app11.nu.edu.bd/",
        "http://ems.nu.ac.bd/"
    ]
    prohibited_urls = [
        "services.nu.edu.bd",
        "103.113.200.36"
    ]
    
    # Test card markdown outputs for all program types
    test_records = [
        {"program_type": "Honours", "examination_year": "2025", "part": "Part 1"},
        {"program_type": "Degree Pass", "examination_year": "2024", "part": "Part 2"},
        {"program_type": "Master's", "examination_year": "2023", "part": "Final"},
        {"program_type": "Professional", "examination_year": "2025", "part": "CSE", "semester": "1st Semester", "course_name": "CSE"},
    ]
    for rec in test_records:
        card_md = format_exam_card_markdown(rec)
        for bad_url in prohibited_urls:
            assert bad_url not in card_md, f"CRITICAL SECURITY: Prohibited URL {bad_url} found in exam card markdown for {rec['program_type']}!"
        
        timeline_html = render_exam_card_timeline_bar(rec)
        for bad_url in prohibited_urls:
            assert bad_url not in timeline_html, f"CRITICAL SECURITY: Prohibited URL {bad_url} found in timeline HTML for {rec['program_type']}!"
    print("[PASS] Zero prohibited URLs found in generated cards or timeline HTML")
    
    # ----------------------------------------------------
    # SECTION 3: Multi-Program Compatibility
    # ----------------------------------------------------
    print("\n--- SECTION 3: Multi-Program Compatibility ---")
    all_programs = ["Honours", "Degree Pass", "Master's", "Professional"]
    for prog in all_programs:
        sample = {
            "program_type": prog,
            "examination_year": "2025",
            "part": "Part 1" if prog != "Master's" else "Final",
            "semester": "Semester 1" if prog == "Professional" else "N/A",
            "course_name": "BBA" if prog == "Professional" else "",
            "exam_date": "10-11-2025",
            "results_published": "No",
            "documents_printed": "No"
        }
        card = format_exam_card_markdown(sample)
        assert "📊 পরীক্ষার টাইমলাইন ও ধাপসমূহ দেখুন" in card, f"Toggle button missing for {prog}"
        assert 'class="hidden transition-all duration-300"' in card or 'class="hidden' in card, f"Hidden container missing for {prog}"
        
        timeline = render_exam_card_timeline_bar(sample)
        for title in ["ইনকোর্স পরীক্ষা", "ফরম পূরণ", "রুটিন ও প্রবেশপত্র", "মূল পরীক্ষা", "ফলাফল প্রকাশ", "সনদ ও মার্কশিট"]:
            assert title in timeline, f"Milestone {title} missing in timeline for {prog}"
        assert "h-1.5" in timeline, f"Slim progress track missing for {prog}"
        assert "১" in timeline or "✓" in timeline
        print(f"[PASS] {prog} program card and timeline generated correctly")
        
    # ----------------------------------------------------
    # SECTION 4: Professional Flow Query Testing
    # ----------------------------------------------------
    print("\n--- SECTION 4: Professional Flow Query Testing ---")
    store = get_sql_store()
    
    # 4.1: Category inquiry returns course selection cards
    resp_cat = process_academic_exam_query("প্রফেশনাল পরীক্ষা তথ্য")
    assert resp_cat is not None
    assert "প্রফেশনাল কোর্সসমূহ" in resp_cat.reply or "কোর্স নির্বাচন করুন" in resp_cat.reply
    print("[PASS] Professional general category returns course selection cards")
    
    # 4.2: Specific course without semester returns semester selection cards
    resp_cse = process_academic_exam_query("CSE পরীক্ষা তথ্য")
    assert resp_cse is not None
    assert "সেমিস্টার" in resp_cse.reply
    assert "১ম সেমিস্টার" in resp_cse.reply
    print("[PASS] Professional course without semester returns semester selection cards")
    
    # 4.3: Specific course + semester returns exam card with toggle button and timeline
    resp_sem = process_academic_exam_query("CSE ১ম সেমিস্টার ২০২৫ পরীক্ষা")
    assert resp_sem is not None
    assert "📊 পরীক্ষার টাইমলাইন ও ধাপসমূহ দেখুন" in resp_sem.reply, "Toggle button missing in CSE 1st semester reply"
    assert "hidden" in resp_sem.reply, "Hidden container missing in CSE 1st semester reply"
    assert "ইনকোর্স পরীক্ষা" in resp_sem.reply, "Apple timeline missing in CSE 1st semester reply"
    print("[PASS] Professional course + semester with year returns exam card with collapsible timeline")

    # 4.4: ADVERSARIAL STRESS TEST: Multiple years in DB for Professional course, query WITHOUT year
    print("\n--- ADVERSARIAL TEST: Multiple years in Professional without year specified ---")
    # Check what happens if 2024 and 2025 both exist
    rec_2024 = {
        "program_type": "Professional",
        "examination_year": "2024",
        "part": "CSE",
        "semester": "1st Semester",
        "course_name": "CSE",
        "exam_date": "15 May 2024",
        "results_published": "Yes"
    }
    rec_2025 = {
        "program_type": "Professional",
        "examination_year": "2025",
        "part": "CSE",
        "semester": "1st Semester",
        "course_name": "CSE",
        "exam_date": "10 Mar 2025",
        "results_published": "No"
    }
    store.upsert_academic_exam_info(rec_2024, user_name="Admin")
    store.upsert_academic_exam_info(rec_2025, user_name="Admin")
    
    resp_cse_no_year = process_academic_exam_query("CSE ১ম সেমিস্টার")
    print(f"Reply length: {len(resp_cse_no_year.reply)}")
    has_toggle = "📊 পরীক্ষার টাইমলাইন ও ধাপসমূহ দেখুন" in resp_cse_no_year.reply
    print(f"Has toggle button in multi-year Professional query: {has_toggle}")
    if not has_toggle:
        print(">>> POTENTIAL FINDING DETECTED: In Professional flow when multiple years exist and no year is specified in the prompt, format_exam_card_markdown(recent_record) was omitted in academic_exam_service.py line 1727!")
    
    print("\nALL STRESS TESTS COMPLETED.")

if __name__ == "__main__":
    run_stress_tests()
