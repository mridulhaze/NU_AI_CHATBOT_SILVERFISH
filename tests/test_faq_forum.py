"""
Unit & Integration Tests for NU Academic FAQ Forum & Like Management
"""

import pytest
from fastapi.testclient import TestClient
from backend.app import app
from backend.services.faq_service import get_faq_service


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def faq_service():
    service = get_faq_service()
    service.ensure_seeded()
    return service


def test_faq_file_parsing(faq_service):
    """Verifies that FAQ/faq.txt is parsed into at least 650 valid items across multiple categories."""
    items = faq_service.parse_faq_file()
    assert len(items) >= 650
    categories = set(i["category"] for i in items)
    assert len(categories) >= 20
    # Verify Bengali characters and structure
    sample = items[0]
    assert "question" in sample and len(sample["question"]) > 5
    assert "answer" in sample and len(sample["answer"]) > 5
    assert "category" in sample and len(sample["category"]) > 0


def test_faq_sync_idempotent(faq_service):
    """Ensures syncing twice does not duplicate records or crash."""
    res1 = faq_service.sync_from_file()
    assert res1["status"] == "success"
    assert res1["synced"] >= 650

    # Second sync should update/maintain existing records idempotently
    res2 = faq_service.sync_from_file()
    assert res2["status"] == "success"
    assert res2["synced"] == res1["synced"]


def test_faq_listing_and_filtering(client):
    """Tests GET /api/v1/faqs with pagination, categories, and search."""
    # 1. Basic list
    r = client.get("/api/v1/faqs?limit=10&page=1")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "success"
    assert len(data["items"]) == 10
    assert data["total"] >= 650

    # 2. Category list
    r_cats = client.get("/api/v1/faqs/categories")
    assert r_cats.status_code == 200
    cats_data = r_cats.json()["categories"]
    assert len(cats_data) >= 10
    test_cat = cats_data[0]["category"]

    # Filter by that category
    r_filt = client.get(f"/api/v1/faqs?category={test_cat}&limit=50")
    assert r_filt.status_code == 200
    filt_items = r_filt.json()["items"]
    assert len(filt_items) > 0
    for item in filt_items:
        assert item["category"] == test_cat


def test_faq_search(client):
    """Tests searching in Bengali and English."""
    # Search for "ভর্তি"
    r_bn = client.get("/api/v1/faqs?search=ভর্তি&limit=10")
    assert r_bn.status_code == 200
    items_bn = r_bn.json()["items"]
    assert len(items_bn) > 0

    # Search for "certificate" or "TC"
    r_en = client.get("/api/v1/faqs?search=TC&limit=10")
    assert r_en.status_code == 200
    assert "items" in r_en.json()


def test_faq_like_toggle_and_anti_duplicate(client):
    """Tests atomic like toggle, duplicate prevention, and session isolation."""
    # Get first FAQ
    r_list = client.get("/api/v1/faqs?limit=1")
    faq_id = r_list.json()["items"][0]["id"]
    initial_likes = r_list.json()["items"][0]["likes_count"]

    session_a = "test_user_session_alpha"
    session_b = "test_user_session_beta"

    # User A likes
    r_like1 = client.post(f"/api/v1/faqs/{faq_id}/like", json={"session_id": session_a})
    assert r_like1.status_code == 200
    d1 = r_like1.json()
    assert d1["has_liked"] is True
    assert d1["likes_count"] == initial_likes + 1

    # User A likes again -> should UNLIKE
    r_like2 = client.post(f"/api/v1/faqs/{faq_id}/like", json={"session_id": session_a})
    assert r_like2.status_code == 200
    d2 = r_like2.json()
    assert d2["has_liked"] is False
    assert d2["likes_count"] == initial_likes

    # User A likes again -> LIKED
    r_like3 = client.post(f"/api/v1/faqs/{faq_id}/like", json={"session_id": session_a})
    assert r_like3.json()["has_liked"] is True

    # User B likes -> LIKED and count becomes initial_likes + 2
    r_like4 = client.post(f"/api/v1/faqs/{faq_id}/like", json={"session_id": session_b})
    assert r_like4.json()["has_liked"] is True
    assert r_like4.json()["likes_count"] == initial_likes + 2

    # Clean up test likes
    client.post(f"/api/v1/faqs/{faq_id}/like", json={"session_id": session_a})
    client.post(f"/api/v1/faqs/{faq_id}/like", json={"session_id": session_b})


def test_top_liked_faqs(client):
    """Tests GET /api/v1/faqs/top-liked returns items in descending order of likes."""
    r = client.get("/api/v1/faqs/top-liked?limit=10")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "success"
    items = data["items"]
    assert len(items) <= 10

    # Verify descending ordering
    for i in range(len(items) - 1):
        assert items[i]["likes_count"] >= items[i + 1]["likes_count"]
