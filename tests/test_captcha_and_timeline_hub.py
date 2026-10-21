"""
Test Suite for:
1. Exam Timeline Hub & All-Exam Horizontal Timelines Endpoint
2. Bot Shield Math CAPTCHA Generation & Verification
3. Rate Limiter Reset & Token Bypass Integration
4. Chat Interface Sticky Bottom Menu Bar & Captcha Modal DOM Assertions
"""

import pytest
import os
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient
from backend.app import app
from backend.services.captcha_service import captcha_service, normalize_digits, to_bn_digits
from backend.rate_limiter import rate_limiter

client = TestClient(app)

def test_captcha_service_math_challenge():
    challenge = captcha_service.generate_challenge()
    assert "captcha_id" in challenge
    assert "question" in challenge
    assert "=" in challenge["question"]
    assert challenge["expires_in"] == 300

    cid = challenge["captcha_id"]
    # Check internal solution exists
    assert cid in captcha_service._challenges
    correct_ans = captcha_service._challenges[cid]["answer"]

    # Test incorrect answer
    res_fail = captcha_service.verify_answer(cid, "99999")
    assert res_fail["verified"] is False
    assert res_fail["status"] == "incorrect"

    # Generate a fresh challenge
    ch2 = captcha_service.generate_challenge()
    cid2 = ch2["captcha_id"]
    sol2 = captcha_service._challenges[cid2]["answer"]

    # Test Bengali digits submission
    sol2_bn = to_bn_digits(int(sol2))
    res_succ = captcha_service.verify_answer(cid2, sol2_bn)
    assert res_succ["verified"] is True
    assert res_succ["status"] == "success"
    assert "verification_token" in res_succ
    tok = res_succ["verification_token"]
    assert captcha_service.is_token_valid(tok) is True


def test_api_captcha_challenge_and_verify():
    # 1. Challenge API
    res = client.get("/api/v1/captcha/challenge")
    assert res.status_code == 200
    data = res.json()
    assert "captcha_id" in data
    assert "question" in data

    cid = data["captcha_id"]
    expected_ans = captcha_service._challenges[cid]["answer"]

    # 2. Verify API with correct answer
    v_res = client.post("/api/v1/captcha/verify", json={
        "captcha_id": cid,
        "answer": expected_ans
    })
    assert v_res.status_code == 200
    v_data = v_res.json()
    assert v_data["verified"] is True
    assert "verification_token" in v_data
    token = v_data["verification_token"]

    # 3. Status API
    s_res = client.get(f"/api/v1/captcha/status?token={token}")
    assert s_res.status_code == 200
    assert s_res.json()["valid"] is True


def test_rate_limiter_captcha_token_bypass():
    test_ip = "192.168.1.99"
    rate_limiter.reset_ip(test_ip)

    # Issue a valid token
    ch = captcha_service.generate_challenge()
    cid = ch["captcha_id"]
    ans = captcha_service._challenges[cid]["answer"]
    v_res = captcha_service.verify_answer(cid, ans, client_ip=test_ip)
    tok = v_res["verification_token"]

    # Should pass without throwing HTTPException
    rate_limiter.check_rate_limit(test_ip, captcha_token=tok)


def test_api_all_academic_exam_timelines_endpoint():
    res = client.get("/api/v1/academic-exams/all-timelines")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "items" in data
    assert isinstance(data["items"], list)

    if len(data["items"]) > 0:
        first = data["items"][0]
        assert "record" in first
        assert "timeline" in first
        assert "phases" in first["timeline"]
        assert len(first["timeline"]["phases"]) == 5


def test_chat_html_exam_timeline_tab_and_sticky_bottom():
    chat_path = os.path.join("static", "chat.html")
    assert os.path.exists(chat_path)
    with open(chat_path, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    # 1. Header Exam Timeline Button
    timeline_btn = soup.find("button", id="nav-exam-timeline-btn")
    assert timeline_btn is not None, "Missing #nav-exam-timeline-btn in static/chat.html"
    assert "openAllExamTimelinesHub" in timeline_btn.get("onclick", "")
    assert "Exam Timeline" in timeline_btn.text

    # 2. View container for all exam timelines
    all_timelines_view = soup.find("div", id="all-exam-timelines-view")
    assert all_timelines_view is not None, "Missing #all-exam-timelines-view in static/chat.html"

    # 3. Bottom controls wrapper sticky at screen bottom
    bottom_bar = soup.find("div", id="bottom-controls-bar")
    assert bottom_bar is not None, "Missing #bottom-controls-bar in static/chat.html"
    classes = bottom_bar.get("class", [])
    assert "sticky" in classes, "Bottom controls wrapper should have sticky class"
    assert "bottom-0" in classes, "Bottom controls wrapper should be pinned to bottom-0"

    # 4. Chips bar present inside bottom bar
    chips_bar = bottom_bar.find("div", id="chips-bar")
    assert chips_bar is not None, "Missing #chips-bar inside bottom controls bar"

    # 5. Captcha modal present
    captcha_modal = soup.find("div", id="captcha-modal")
    assert captcha_modal is not None, "Missing #captcha-modal in static/chat.html"
    assert soup.find("input", id="captcha-answer-input") is not None
    assert soup.find("button", id="captcha-submit-btn") is not None

    # 6. JavaScript functions exposed
    assert "openAllExamTimelinesHub" in html
    assert "renderAllExamTimelinesHub" in html
    assert "openCaptchaModal" in html
    assert "submitCaptchaVerification" in html
    assert "loadNewCaptchaChallenge" in html
    assert "X-Captcha-Token" in html
