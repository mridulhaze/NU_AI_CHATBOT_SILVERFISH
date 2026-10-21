import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend.app import app
from backend.services.notice_service import parse_notice_date
from crawler.notices_scraper import NoticesScraper, _slice_table_html
from crawler.scheduler import sync_recent_notices, get_crawler_status, _crawler_state, start_scheduler, stop_scheduler
from db.sql_store import get_sql_store


class TestRecentNoticesSync:
    """
    Test suite for recent notices scraping, parsing, scheduling, and admin synchronization endpoint.
    """

    def test_parse_notice_date_various_formats(self):
        # 1. Standard English formats
        dt1 = parse_notice_date("October 20, 2026")
        assert dt1.year == 2026 and dt1.month == 10 and dt1.day == 20

        # 2. Bengali month and Bengali digits
        dt2 = parse_notice_date("২০ অক্টোবর ২০২৬")
        assert dt2.year == 2026 and dt2.month == 10 and dt2.day == 20

        # 3. Bengali digits with slashes and hyphens
        dt3 = parse_notice_date("২০/১০/২০২৬")
        assert dt3.year == 2026 and dt3.month == 10 and dt3.day == 20

        dt4 = parse_notice_date("২০-১০-২০২৬")
        assert dt4.year == 2026 and dt4.month == 10 and dt4.day == 20

        # 4. URL pub_date pattern
        dt5 = parse_notice_date("", "", "https://www.nu.ac.bd/uploads/notices/notice_2126_pub_date_20102026.pdf")
        assert dt5.year == 2026 and dt5.month == 10 and dt5.day == 20

        # 5. Filename hyphenated date pattern (e.g. press release)
        dt6 = parse_notice_date("", "", "https://www.nu.ac.bd/uploads/notices/NU_Press_Release_001_19-10-2026.pdf")
        assert dt6.year == 2026 and dt6.month == 10 and dt6.day == 19

    def test_slice_table_html(self):
        # Build mock HTML with 200 table rows
        rows = "".join(f"<tr><td>Notice {i}</td><td>October {i%28 + 1}, 2026</td></tr>\n" for i in range(200))
        big_html = f"<html><body><div style='padding:10px;'>{'x'*300000}</div><table>{rows}</table></body></html>"
        
        sliced = _slice_table_html(big_html, target_rows=50)
        assert len(sliced) < len(big_html)
        assert sliced.endswith("</tbody></table></body></html>")

    def test_scrape_recent_notices_mock(self):
        mock_html = """
        <html><body><table>
            <tr><td>Sl</td><td>Title</td><td>Publish Date</td><td>Download</td></tr>
            <tr><td>1</td><td><a href="uploads/notices/test_notice_2026.pdf">জাতীয় বিশ্ববিদ্যালয় নতুন নোটিশ</a></td><td>October 21, 2026</td><td>Download</td></tr>
            <tr><td>2</td><td><a href="uploads/notices/test_notice_2025.pdf">পুরাতন পরীক্ষা বিজ্ঞপ্তি</a></td><td>October 15, 2026</td><td>Download</td></tr>
        </table></body></html>
        """
        scraper = NoticesScraper()
        with patch.object(scraper, "fetch_url", return_value=mock_html):
            docs, pages, new_items, all_items = scraper.scrape_recent_notices(max_rows=10)
            assert pages >= 1
            assert len(all_items) >= 2
            assert all_items[0]["title"] == "জাতীয় বিশ্ববিদ্যালয় নতুন নোটিশ"
            assert all_items[0]["date"] == "October 21, 2026"

    def test_scrape_recent_notices_offline_fallback(self):
        # When network fails completely (returns None for all URLs)
        scraper = NoticesScraper()
        with patch.object(scraper, "fetch_url", return_value=None):
            docs, pages, new_items, all_items = scraper.scrape_recent_notices(max_rows=5)
            # Should not raise exception and should fallback to cached SQLite notices
            assert pages == 0
            assert isinstance(all_items, list)

    def test_admin_update_recent_notices_endpoint(self):
        client = TestClient(app)
        
        # Test successful immediate update call
        mock_items = [{"title": "Live Notice Test", "date": "October 21, 2026", "url": "https://nu.ac.bd/test"}]
        with patch("crawler.scheduler.NoticesScraper.scrape_recent_notices", return_value=([], 1, 1, mock_items)):
            response = client.post("/api/v1/admin/update-recent-notices", json={"max_rows": 20})
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["latest_notice"]["title"] == "Live Notice Test"

    def test_admin_update_busy_lock(self):
        client = TestClient(app)
        
        # Simulate crawler currently running
        _crawler_state["is_running"] = True
        try:
            response = client.post("/api/v1/admin/update-recent-notices")
            assert response.status_code == 409
            data = response.json()
            assert data["status"] == "busy"
        finally:
            _crawler_state["is_running"] = False

    def test_hourly_cron_job_configured(self):
        import crawler.scheduler as sched
        sched.stop_scheduler()
        try:
            sched.start_scheduler(crawl_interval_minutes=60)
            scheduler_instance = sched._scheduler
            assert scheduler_instance is not None
            job = scheduler_instance.get_job("nu_recent_sync_hourly_job")
            assert job is not None
            assert job.trigger.interval.total_seconds() == 3600  # 60 minutes
        finally:
            sched.stop_scheduler()
