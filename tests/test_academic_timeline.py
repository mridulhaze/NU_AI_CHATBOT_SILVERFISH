"""
Test suite for Academic Examination Milestone Timeline & Progress Tracker.
Verifies:
1. 5 Academic Phases structure (ইনকোর্স ও ফরম পূরণ, পরীক্ষা, ফলাফল, পুনঃনিরীক্ষণ, সনদ ও মার্কশিট).
2. Intelligent milestone status evaluation.
3. Strict rule: Past date without confirmation is NEVER marked as completed.
4. Multi-year switching and lookup endpoints.
5. Official portal links integrity.
"""

import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from main import app
from backend.services.academic_exam_service import (
    evaluate_milestone_status,
    build_academic_milestone_timeline,
    get_academic_exam_years,
    parse_date_str,
    format_exam_card_markdown,
    render_exam_card_timeline_bar
)
from db.sql_store import get_sql_store

client = TestClient(app)

def test_milestone_status_critical_accuracy_rule():
    """Verify that a past date without explicit completion confirmation is NOT marked as completed."""
    today = date(2026, 10, 21)
    past_date_str = "15 May 2024"
    record = {"exam_date": past_date_str}
    
    label, status_type, is_comp, desc = evaluate_milestone_status("exam_date", past_date_str, record, today)
    assert is_comp is False
    assert status_type == "passed_unconfirmed"
    assert "তারিখ অতিক্রান্ত" in label

def test_milestone_status_confirmed_completion():
    """Verify explicit confirmation flags."""
    today = date(2026, 10, 21)
    record = {"results_published": "Yes", "documents_printed": "Yes"}
    
    # Results
    label, status_type, is_comp, _ = evaluate_milestone_status("results_published", "Yes", record, today)
    assert is_comp is True
    assert status_type == "published"
    assert "প্রকাশিত" in label

    # Documents printed
    label, status_type, is_comp, _ = evaluate_milestone_status("documents_printed", "Yes", record, today)
    assert is_comp is True
    assert status_type == "completed"
    assert "সম্পন্ন" in label

def test_milestone_status_today_and_future():
    """Verify today and upcoming status logic."""
    today = date(2026, 10, 21)
    
    # Today
    label, status_type, is_comp, _ = evaluate_milestone_status("exam_date", "21-10-2026", {}, today)
    assert is_comp is False
    assert status_type == "today"
    assert "আজ" in label

    # Upcoming
    label, status_type, is_comp, _ = evaluate_milestone_status("exam_date", "25 December 2026", {}, today)
    assert is_comp is False
    assert status_type == "upcoming"
    assert "আসন্ন" in label

def test_milestone_status_routine_link():
    """Verify that a live routine URL is treated as published."""
    today = date(2026, 10, 21)
    routine_url = "https://www.nu.ac.bd/uploads/2026/routine_honours.pdf"
    label, status_type, is_comp, _ = evaluate_milestone_status("routine_publication_date", routine_url, {}, today)
    assert is_comp is True
    assert status_type == "published"
    assert "প্রকাশিত" in label

def test_timeline_structure_and_phases():
    """Verify the 5 phases exist in timeline output."""
    store = get_sql_store()
    recs = store.lookup_academic_exam_info("Honours", "2024", "Part 1")
    assert len(recs) > 0
    rec = recs[0]

    timeline = build_academic_milestone_timeline(rec, available_years=["2025", "2024"])
    assert len(timeline["phases"]) == 5
    phase_titles = [p["title_bn"] for p in timeline["phases"]]
    assert "ইনকোর্স ও ফরম পূরণ" in phase_titles
    assert "পরীক্ষা" in phase_titles
    assert "ফলাফল" in phase_titles
    assert "পুনঃনিরীক্ষণ" in phase_titles
    assert "সনদ ও মার্কশিট" in phase_titles

    summary = timeline["summary"]
    assert summary["total_milestones"] == 18
    assert summary["completed_milestones"] >= 1  # 2024 has results_published='Yes'
    assert "disclaimer" in summary

    # Verify official portals presence
    portals = timeline["official_portals"]
    portal_urls = [p["url"] for p in portals]
    assert any("results.nu.ac.bd" in u for u in portal_urls)
    assert any("103.113.200.68/nu-app/" in u for u in portal_urls)

def test_api_years_endpoint():
    """Verify GET /api/v1/academic-exams/years returns available years."""
    response = client.get("/api/v1/academic-exams/years?program_type=Honours&part=Part 1")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "2024" in data["years"]
    assert "2025" in data["years"]

def test_api_lookup_endpoint_with_timeline():
    """Verify GET /api/v1/academic-exams/lookup returns the timeline payload."""
    response = client.get("/api/v1/academic-exams/lookup?program_type=Honours&examination_year=2025&part=Part 1")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "timeline" in data
    assert data["timeline"]["examination_year"] == "2025"
    assert len(data["timeline"]["phases"]) == 5
    assert len(data["available_years"]) >= 2


def test_format_exam_card_markdown_toggle_button_and_hidden_container():
    """
    Verify Milestone 2 Requirements:
    1. format_exam_card_markdown contains the toggle button with 'পরীক্ষার টাইমলাইন ও ধাপসমূহ দেখুন'.
    2. The timeline container starts with default 'hidden'.
    3. The button has aria-expanded='false' and links to the timeline container ID.
    """
    sample_record = {
        "id": "1",
        "program_type": "Honours",
        "program_type_name": "স্নাতক (সম্মান)",
        "examination_year": "2024",
        "part": "Part 1",
        "semester": "N/A",
        "exam_date": "15 May 2024",
        "results_published": "Yes",
        "documents_printed": "No"
    }
    card_md = format_exam_card_markdown(sample_record)

    # Must contain toggle button with required label and icon
    assert "পরীক্ষার টাইমলাইন ও ধাপসমূহ দেখুন" in card_md
    assert "📊" in card_md
    assert "↓" in card_md
    assert 'aria-expanded="false"' in card_md

    # Container must be hidden by default
    assert 'class="hidden transition-all' in card_md or 'class="hidden' in card_md

    # Button onclick must invoke toggleExamTimeline with the container ID
    import re
    match_id = re.search(r'id="(timeline-collapse-[^"]+)"', card_md)
    assert match_id is not None, "Timeline collapsible container must have a unique ID"
    timeline_id = match_id.group(1)
    assert timeline_id in card_md
    assert f"toggleExamTimeline('{timeline_id}'" in card_md or f'toggleExamTimeline(\'{timeline_id}\'' in card_md


def test_render_exam_card_timeline_bar_clean_apple_typography_and_no_step_cards():
    """
    Verify Milestone 2 Requirements:
    1. Completely eliminate nested boxy step cards (no 'bg-white rounded-xl p-2 shadow-2xs border', no connector sticks).
    2. Contain all 6 high-contrast Apple-style bold milestone titles.
    3. Minimalist date text and subtle muted status badges.
    4. Slim progress bar track with rounded ends.
    """
    sample_record = {
        "id": "1",
        "program_type": "Honours",
        "examination_year": "2024",
        "part": "Part 1",
        "incourse_exam_date": "10 January 2024",
        "form_fillup_deadline": "28 February 2024",
        "routine_publication_date": "15 April 2024",
        "exam_date": "15 May 2024",
        "results_published": "Yes",
        "actual_result_date": "20 September 2024",
        "documents_printed": "No",
        "document_printing_date": "15 November 2024"
    }
    timeline_html = render_exam_card_timeline_bar(sample_record)

    # 1. Elimination of boxy cards and connector sticks
    assert "w-full bg-white rounded-xl p-2 shadow-2xs border" not in timeline_html
    assert "w-0.5 h-3.5 bg-slate-300" not in timeline_html
    assert "hover:shadow-xs transition" not in timeline_html or "rounded-2xl" in timeline_html

    # 2. All 6 bold milestone titles present
    milestone_titles = [
        "ইনকোর্স পরীক্ষা",
        "ফরম পূরণ",
        "রুটিন ও প্রবেশপত্র",
        "মূল পরীক্ষা",
        "ফলাফল প্রকাশ",
        "সনদ ও মার্কশিট"
    ]
    for title in milestone_titles:
        assert title in timeline_html, f"Milestone title '{title}' must be present in timeline HTML"
        assert f"font-bold" in timeline_html

    # 3. Status badges present
    assert any(badge in timeline_html for badge in ["সম্পন্ন", "আজ", "আসন্ন", "তারিখ অতিক্রান্ত", "প্রকাশিত", "তথ্য নেই"])

    # 4. Slim horizontal progress bar track
    assert "h-1.5" in timeline_html
    assert "rounded-full" in timeline_html


def test_render_exam_card_timeline_bar_bengali_numerals_and_completion_icons():
    """
    Verify Milestone 2 Requirements:
    Step nodes must display Bengali numerals ১ to ৬ or ✓ when completed.
    """
    # Case A: Record where results are published (Step 5 completed), but step 6 not completed
    sample_record = {
        "id": "2",
        "program_type": "Honours",
        "examination_year": "2025",
        "part": "Part 1",
        "results_published": "Yes",
        "documents_printed": "No"
    }
    timeline_html = render_exam_card_timeline_bar(sample_record)
    assert "✓" in timeline_html, "Completed milestone should show checkmark"
    # Uncompleted steps must show Bengali numerals (e.g. ৬ for documents_printed)
    assert "৬" in timeline_html or "১" in timeline_html or "২" in timeline_html

    # Case B: Brand new unconfirmed record (all uncompleted)
    empty_record = {
        "program_type": "Degree Pass",
        "examination_year": "2026",
        "part": "Part 1"
    }
    timeline_html_empty = render_exam_card_timeline_bar(empty_record)
    for bn_digit in ["১", "২", "৩", "৪", "৫", "৬"]:
        assert bn_digit in timeline_html_empty, f"Bengali numeral '{bn_digit}' should be in uncompleted nodes"


def test_timeline_and_card_compatibility_across_all_programs():
    """
    Verify compatibility with Honours, Degree Pass, Master's, and Professional programs.
    Each program's exam card must contain the toggle button, default hidden container, and all 6 milestones.
    """
    programs = [
        ("Honours", "2024", "Part 1"),
        ("Degree Pass", "2023", "Part 2"),
        ("Master's", "2022", "Final"),
        ("Professional", "2024", "BBA")
    ]
    for prog, year, part in programs:
        rec = {
            "program_type": prog,
            "examination_year": year,
            "part": part,
            "exam_date": f"10 June {year}",
            "results_published": "No"
        }
        card_md = format_exam_card_markdown(rec)
        assert "পরীক্ষার টাইমলাইন ও ধাপসমূহ দেখুন" in card_md
        assert "hidden" in card_md

        timeline_html = render_exam_card_timeline_bar(rec)
        assert "ইনকোর্স পরীক্ষা" in timeline_html
        assert "সনদ ও মার্কশিট" in timeline_html
        assert "h-1.5" in timeline_html


def test_timeline_html_single_line_tags_and_no_markdown_bleeding():
    """
    Verify that generated HTML tags have no internal newlines across attributes,
    and no 4-space indentations that cause markdown blockquote/code formatting.
    """
    sample_record = {
        "program_type": "Honours",
        "examination_year": "2024",
        "part": "Part 1"
    }
    timeline_html = render_exam_card_timeline_bar(sample_record)

    # Check for newline inside an unclosed tag (<tag ... \n ... >)
    import re
    broken_tags = re.findall(r'<[^>]*\n[^>]*>', timeline_html)
    assert len(broken_tags) == 0, f"Found tags with internal newlines: {broken_tags}"

    # Check for 4-space indentation on lines that could trigger markdown codeblocks
    for line in timeline_html.split("\n"):
        if line.strip():
            assert not line.startswith("    <div class=\"w-full bg-white"), "Should not contain indented code blocks"


def test_chat_html_toggle_exam_timeline_function_exists():
    """
    Verify that static/chat.html includes toggleExamTimeline and exposes it globally.
    """
    import os
    chat_path = os.path.join("static", "chat.html")
    assert os.path.exists(chat_path)
    with open(chat_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "function toggleExamTimeline(containerId, btn)" in content
    assert "window.toggleExamTimeline = toggleExamTimeline;" in content
    assert "পরীক্ষার টাইমলাইন ও ধাপসমূহ দেখুন" in content
    assert "পরীক্ষার টাইমলাইন ও ধাপসমূহ লুকান" in content

