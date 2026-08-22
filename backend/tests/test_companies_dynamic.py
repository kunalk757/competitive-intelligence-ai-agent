import asyncio
import os
import sys
import httpx
from unittest.mock import patch
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.services.company_service import (
    CompanyDataService,
    company_data_service,
    CompanyDetailsResponse,
)
from app.services.tavily_service import TavilyService
from app.services.gnews_service import GNewsService
from app.database.company_repository import CompanyRepository


def test_tavily_service_mock():
    print("\n--- Test 1: Tavily Web Intelligence Service Parsing ---")
    tavily = TavilyService()
    
    mock_response_data = {
        "answer": "NVIDIA Corporation is an American multinational corporation and technology company that designs GPUs and AI accelerators.",
        "results": [
            {
                "title": "NVIDIA Official Site",
                "url": "https://www.nvidia.com",
                "content": "NVIDIA is the pioneer of GPU computing and accelerated AI infrastructure.",
            },
            {
                "title": "NVIDIA - Wikipedia",
                "url": "https://en.wikipedia.org/wiki/Nvidia",
                "content": "Nvidia Corporation is a global leader in AI hardware and software systems.",
            }
        ]
    }

    mock_resp = httpx.Response(
        status_code=200,
        json=mock_response_data,
        request=httpx.Request("POST", "https://api.tavily.com/search"),
    )

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        tavily.api_key = "mock_tavily_key_123"

        res = asyncio.run(tavily.get_company_web_information("NVIDIA"))
        assert res is not None
        assert res["name"] == "NVIDIA"
        assert "NVIDIA Corporation" in res["overview"]
        assert len(res["sources"]) == 2
        assert res["sources"][0]["url"] == "https://www.nvidia.com"
        assert res["website"] == "https://www.nvidia.com"
        print("[OK] Tavily service parsed overview and sources accurately.")


def test_gnews_company_news_mock():
    print("\n--- Test 2: GNews Company News Parsing & Tagging ---")
    gnews = GNewsService()
    
    mock_gnews_data = {
        "articles": [
            {
                "title": "NVIDIA Unveils Next-Gen AI Silicon",
                "description": "NVIDIA announced high performance AI chip architectures for data centers.",
                "url": "https://example.com/nvidia-silicon",
                "image": "https://example.com/nvidia.jpg",
                "publishedAt": "2026-08-22T10:00:00Z",
                "source": {"name": "Tech Times", "url": "https://techtimes.com"},
            }
        ]
    }

    mock_resp = httpx.Response(
        status_code=200,
        json=mock_gnews_data,
        request=httpx.Request("GET", "https://gnews.io/api/v4/search"),
    )

    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        gnews.api_key = "mock_gnews_key_123"

        articles = asyncio.run(gnews.fetch_company_news("NVIDIA"))
        assert len(articles) == 1
        assert articles[0]["title"] == "NVIDIA Unveils Next-Gen AI Silicon"
        assert articles[0]["company"] == "NVIDIA"
        assert articles[0]["source_name"] == "Tech Times"
        print("[OK] GNews company news successfully normalized and tagged.")


def test_combined_company_service_and_caching():
    print("\n--- Test 3: Combined Company Service & Caching Orchestration ---")
    service = CompanyDataService()

    # Pre-populate mock cache with both profile and news
    asyncio.run(
        service.repository.save_company_profile({
            "company_name": "Tesla",
            "overview": "Tesla designs electric vehicles, energy systems, and AI robotics.",
            "website": "https://www.tesla.com",
            "sources": [{"title": "Tesla Official", "url": "https://www.tesla.com"}],
        })
    )
    asyncio.run(
        service.news_repo.upsert_articles([
            {
                "title": "Tesla Supercharger Network Expansion",
                "description": "Tesla continues expansion of fast chargers.",
                "source_url": "https://tesla.com/news/expansion",
                "source_name": "Tesla Press",
                "company": "Tesla",
                "published_at": "2026-08-22T08:00:00Z",
            }
        ])
    )

    # Initial query should return from cache without external API call
    res_cached: CompanyDetailsResponse = asyncio.run(
        service.get_company_details("Tesla", force_refresh=False)
    )
    assert res_cached.company.name == "Tesla"
    assert res_cached.cached is True
    assert "Tesla designs electric vehicles" in (res_cached.company.overview or "")
    assert len(res_cached.news) >= 1
    print("[OK] Cached profile returned without redundant network calls.")


def test_api_endpoints():
    print("\n--- Test 4: FastAPI Company Endpoints ---")
    client = TestClient(app)

    # GET /api/companies/NVIDIA
    resp = client.get("/api/companies/NVIDIA")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()
    assert "company" in data
    assert "name" in data["company"]
    assert data["company"]["name"] == "NVIDIA"
    assert "news" in data
    assert isinstance(data["news"], list)
    print("[OK] GET /api/companies/NVIDIA passed:", {
        "company": data["company"]["name"],
        "news_count": len(data["news"]),
        "has_data": data["has_data"],
        "cached": data["cached"],
    })

    # POST /api/companies/NVIDIA/refresh
    resp_refresh = client.post("/api/companies/NVIDIA/refresh")
    assert resp_refresh.status_code == 200
    assert resp_refresh.json()["company"]["name"] == "NVIDIA"
    print("[OK] POST /api/companies/NVIDIA/refresh passed.")

    # POST /api/companies/refresh-all
    resp_all = client.post("/api/companies/refresh-all")
    assert resp_all.status_code == 200
    all_data = resp_all.json()
    assert "successful_count" in all_data
    assert "total_companies" in all_data
    print("[OK] POST /api/companies/refresh-all passed:", {
        "total": all_data["total_companies"],
        "successful": all_data["successful_count"],
    })


if __name__ == "__main__":
    test_tavily_service_mock()
    test_gnews_company_news_mock()
    test_combined_company_service_and_caching()
    test_api_endpoints()
    print("\n=== ALL DYNAMIC COMPANY TESTS PASSED ===")
