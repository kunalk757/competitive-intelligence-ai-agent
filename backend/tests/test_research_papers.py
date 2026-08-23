"""
Unit and Integration Tests for Research Papers feature and Semantic Scholar integration.

Tests:
1. Research paper response normalization.
2. PaperRepository deduplication and local persistence.
3. ResearchPaperService search execution and resilient fallbacks.
4. FastAPI REST API endpoints (/api/research-papers, /api/research-papers/search).
"""

import os
import sys
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.services.research_paper_service import ResearchPaperService, research_paper_service
from app.database.paper_repository import PaperRepository, paper_repository

client = TestClient(app)


def test_research_paper_normalization():
    """Verify normalization of Semantic Scholar API paper payloads."""
    service = ResearchPaperService()

    raw_papers = [
        {
            "paperId": "abc123xyz",
            "title": "Quantum Error Correction in Superconducting Qubits",
            "abstract": "We demonstrate surface-code logical qubits exceeding physical breakeven thresholds.",
            "year": 2024,
            "venue": "Nature",
            "authors": [{"name": "John Preskill"}, {"name": "Hartmut Neven"}],
            "citationCount": 420,
            "fieldsOfStudy": ["Physics", "Computer Science"],
            "url": "https://www.semanticscholar.org/paper/abc123xyz",
            "openAccessPdf": {"url": "https://arxiv.org/pdf/2401.00001.pdf"},
        }
    ]

    normalized = service._normalize_semantic_scholar_response(raw_papers)
    assert len(normalized) == 1
    paper = normalized[0]

    assert paper["external_id"] == "abc123xyz"
    assert paper["title"] == "Quantum Error Correction in Superconducting Qubits"
    assert paper["authors"] == ["John Preskill", "Hartmut Neven"]
    assert paper["year"] == 2024
    assert paper["venue"] == "Nature"
    assert paper["citation_count"] == 420
    assert "Physics" in paper["fields_of_study"]
    assert paper["url"] == "https://arxiv.org/pdf/2401.00001.pdf"
    assert paper["source"] == "Semantic Scholar"


@pytest.mark.asyncio
async def test_paper_repository_deduplication():
    """Verify that duplicate papers with same external_id or title are deduplicated."""
    test_papers = [
        {
            "external_id": "test_paper_001",
            "title": "Scaling Laws for Autoregressive Transformers",
            "authors": ["Jared Kaplan", "Sam McCandlish"],
            "year": 2020,
            "citation_count": 3500,
        },
        {
            "external_id": "test_paper_001",  # Same ID
            "title": "Scaling Laws for Autoregressive Transformers (Updated)",
            "authors": ["Jared Kaplan", "Sam McCandlish", "Tom Henighan"],
            "year": 2020,
            "citation_count": 3600,
        },
    ]

    await paper_repository.save_papers(test_papers)
    saved = await paper_repository.get_saved_papers(limit=100)

    matching = [p for p in saved if p.get("external_id") == "test_paper_001"]
    assert len(matching) == 1, f"Expected 1 deduplicated entry, found {len(matching)}"
    assert matching[0]["citation_count"] == 3600


@pytest.mark.asyncio
async def test_research_paper_service_search_and_fallback():
    """Verify search execution and fallback mechanism for relevant keywords."""
    # Search for NVIDIA Blackwell
    res = await research_paper_service.search_papers(query="NVIDIA Blackwell architecture", limit=5)
    assert "data" in res
    assert len(res["data"]) >= 1
    assert any("blackwell" in p["title"].lower() or "gpu" in p["title"].lower() for p in res["data"])

    # Search with empty query returns saved/cached papers
    res_empty = await research_paper_service.search_papers(query="", limit=10)
    assert len(res_empty["data"]) >= 1


def test_research_papers_api_endpoints():
    """Verify FastAPI endpoints /api/research-papers and /api/research-papers/search."""
    # 1. GET /api/research-papers
    resp = client.get("/api/research-papers?limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert len(data["data"]) >= 1

    # 2. GET /api/research-papers/search
    search_resp = client.get("/api/research-papers/search?q=AMD&limit=5")
    assert search_resp.status_code == 200
    search_data = search_resp.json()
    assert "data" in search_data
    assert search_data["query"] == "AMD"

    # 3. GET /api/research-papers/{paper_id}
    first_paper = data["data"][0]
    ext_id = first_paper.get("external_id")
    if ext_id:
        single_resp = client.get(f"/api/research-papers/{ext_id}")
        assert single_resp.status_code == 200
        assert single_resp.json()["title"] == first_paper["title"]
