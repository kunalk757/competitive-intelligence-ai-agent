"""
FastAPI route definitions for Research Papers exploration and Semantic Scholar search.
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field

from app.services.research_paper_service import research_paper_service
from app.database.paper_repository import paper_repository

logger = logging.getLogger("research_papers_api")

router = APIRouter(prefix="/research-papers", tags=["Research Papers"])


class ResearchPaperOut(BaseModel):
    id: Optional[str] = None
    external_id: Optional[str] = None
    title: str
    authors: List[str] = Field(default_factory=list)
    abstract: Optional[str] = None
    year: Optional[int] = None
    venue: Optional[str] = None
    url: Optional[str] = None
    citation_count: Optional[int] = 0
    fields_of_study: List[str] = Field(default_factory=list)
    source: Optional[str] = "Semantic Scholar"
    fetched_at: Optional[str] = None


class ResearchPaperSearchResponse(BaseModel):
    query: str
    total: int
    offset: int
    data: List[ResearchPaperOut]
    source: str


@router.get(
    "",
    response_model=ResearchPaperSearchResponse,
    summary="List saved research papers",
    description="Retrieve paginated list of research papers from Supabase and local cache.",
)
async def get_saved_research_papers(
    limit: int = Query(20, ge=1, le=100, description="Max papers to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
):
    try:
        papers = await paper_repository.get_saved_papers(limit=limit, offset=offset)
        return ResearchPaperSearchResponse(
            query="",
            total=len(papers),
            offset=offset,
            data=papers,
            source="database_repository",
        )
    except Exception as e:
        logger.error(f"Error fetching saved research papers: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch research papers")


@router.get(
    "/search",
    response_model=ResearchPaperSearchResponse,
    summary="Search Semantic Scholar research papers",
    description="Search across millions of academic and scientific papers via Semantic Scholar API.",
)
async def search_research_papers(
    q: str = Query(..., min_length=1, description="Search query string"),
    limit: int = Query(15, ge=1, le=30, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
):
    try:
        res = await research_paper_service.search_papers(
            query=q,
            limit=limit,
            offset=offset,
        )
        return ResearchPaperSearchResponse(
            query=res.get("query", q),
            total=res.get("total", 0),
            offset=res.get("offset", offset),
            data=res.get("data", []),
            source=res.get("source", "semantic_scholar"),
        )
    except Exception as e:
        logger.error(f"Error performing research paper search for '{q}': {e}")
        # Return graceful empty list with error handling
        return ResearchPaperSearchResponse(
            query=q,
            total=0,
            offset=offset,
            data=[],
            source="error_fallback",
        )


@router.get(
    "/{paper_id}",
    response_model=ResearchPaperOut,
    summary="Get single research paper details",
)
async def get_research_paper_by_id(paper_id: str):
    papers = await paper_repository.get_saved_papers(limit=200, offset=0)
    for p in papers:
        if p.get("external_id") == paper_id or p.get("id") == paper_id:
            return p
    raise HTTPException(status_code=404, detail=f"Research paper '{paper_id}' not found")
