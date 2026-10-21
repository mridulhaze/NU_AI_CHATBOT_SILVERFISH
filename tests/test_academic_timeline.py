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
    parse_date_str
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
