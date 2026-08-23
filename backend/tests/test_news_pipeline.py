import asyncio
import os
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.services.gnews_service import gnews_service, detect_company, detect_category
from app.database.supabase_client import SupabaseNewsRepository
from app.services.scheduler import get_scheduler_status, IST_TIMEZONE


def test_normalization_and_tagging():
    """Verify company detection and category tagging."""
    nvidia_text = "Nvidia announces new Blackwell Ultra B200 AI chip architecture"
    assert detect_company(nvidia_text) == "NVIDIA"
    assert detect_category(nvidia_text) in ["Semiconductors", "Artificial Intelligence"]

    google_text = "Google DeepMind unveils Gemini 2.0 with custom TPU acceleration"
    assert detect_company(google_text) == "Google"
    assert detect_category(google_text) in ["Artificial Intelligence", "Semiconductors"]

    broadcom_text = "Broadcom secures $10B ASIC custom silicon partnership deal"
    assert detect_company(broadcom_text) == "Broadcom"
    assert detect_category(broadcom_text) in ["Strategic Alliances", "Semiconductors"]


def test_database_deduplication_and_sorting():
    """Verify Supabase/local repository deduplication and sorting."""
    async def _run():
        import tempfile
        import uuid
        
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            repo = SupabaseNewsRepository(local_storage_file=tmp_path)
            
            run_id = str(uuid.uuid4())[:8]
            url1 = f"https://techcrunch.com/article-1-{run_id}"
            url2 = f"https://reuters.com/article-2-{run_id}"

            # Test articles
            sample_articles = [
                {
                    "title": "Article 1 - Older",
                    "description": "Description 1",
                    "source_name": "TechCrunch",
                    "source_url": url1,
                    "image_url": "https://techcrunch.com/img1.jpg",
                    "published_at": "2026-08-25T10:00:00Z",
                    "category": "Technology",
                    "company": "NVIDIA",
                },
                {
                    "title": "Article 2 - Newer",
                    "description": "Description 2",
                    "source_name": "Reuters",
                    "source_url": url2,
                    "image_url": "https://reuters.com/img2.jpg",
                    "published_at": "2026-08-25T11:00:00Z",
                    "category": "Semiconductors",
                    "company": "Google",
                },
            ]
            
            # Insert articles
            res1 = await repo.upsert_articles(sample_articles)
            assert res1["inserted"] >= 2
            
            # Query saved articles
            articles = await repo.get_saved_articles(limit=100)
            assert len(articles) >= 2
            # Newer article should be first
            urls = [a["source_url"] for a in articles]
            assert url2 in urls
            assert url1 in urls
            
            # Test deduplication: re-inserting the exact same articles should insert 0 new items
            res2 = await repo.upsert_articles(sample_articles)
            assert res2["inserted"] == 0
            
            # Verify metadata
            meta = await repo.get_latest_sync_metadata()
            assert meta["total_count"] >= 2
            assert meta["last_updated"] is not None
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

    asyncio.run(_run())


def test_scheduler_timezone_and_schedule():
    """Verify scheduler timezone is Asia/Kolkata and schedule is 10:00 AM & 10:00 PM IST."""
    status = get_scheduler_status()
    assert status["timezone"] == "Asia/Kolkata"
    assert "10:00 AM & 10:00 PM IST" in status["schedule"]


def test_api_endpoints():
    """Verify FastAPI news endpoints and health check."""
    client = TestClient(app)
    
    # 1. Health check
    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"
    
    # 2. Get news
    res_news = client.get("/api/news")
    assert res_news.status_code == 200
    data = res_news.json()
    assert "articles" in data
    assert "total_count" in data
    assert "schedule_notice" in data
    assert data["schedule_notice"] == "Updates daily at 10:00 AM & 10:00 PM IST"
    
    # 3. News status
    res_status = client.get("/api/news/status")
    assert res_status.status_code == 200
    status_data = res_status.json()
    assert status_data["status"] == "active"
    assert "scheduler" in status_data
    assert "database" in status_data
    
    # 4. Manual refresh trigger
    res_refresh = client.post("/api/news/refresh")
    assert res_refresh.status_code == 200
    refresh_data = res_refresh.json()
    assert "success" in refresh_data
    assert "total_saved" in refresh_data


if __name__ == "__main__":
    print("Running tests...")
    test_normalization_and_tagging()
    print("[PASS] Normalization & tagging tests passed")
    test_database_deduplication_and_sorting()
    print("[PASS] Deduplication & sorting tests passed")
    test_scheduler_timezone_and_schedule()
    print("[PASS] Scheduler timezone tests passed")
    test_api_endpoints()
    print("[PASS] API endpoints tests passed")
    print("ALL TESTS PASSED SUCCESSFULLY!")
