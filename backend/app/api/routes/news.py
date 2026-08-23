import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query, status
from pydantic import BaseModel, Field
from app.database.supabase_client import news_repository
from app.services.scheduler import sync_news_job, get_scheduler_status
from app.services.gnews_service import gnews_service

logger = logging.getLogger("news_routes")

router = APIRouter(prefix="/news", tags=["Latest News"])


class NewsArticleOut(BaseModel):
    id: Optional[str] = None
    title: str
    description: Optional[str] = None
    source_name: Optional[str] = Field(default=None, alias="source")
    source_url: Optional[str] = Field(default=None, alias="url")
    image_url: Optional[str] = None
    published_at: Optional[str] = None
    fetched_at: Optional[str] = None
    category: Optional[str] = "Technology"
    company: Optional[str] = Field(default=None, alias="company_tag")
    created_at: Optional[str] = None

    class Config:
        populate_by_name = True


class NewsListResponse(BaseModel):
    articles: List[Dict[str, Any]]
    total_count: int
    last_updated: Optional[str] = None
    schedule_notice: str = "Updates daily at 10:00 AM & 10:00 PM IST"
    is_supabase_connected: bool = False


class NewsRefreshResponse(BaseModel):
    success: bool
    message: str
    articles_fetched: int = 0
    articles_inserted: int = 0
    total_saved: int = 0
    last_updated: Optional[str] = None


@router.get("", response_model=NewsListResponse)
async def get_latest_news(
    limit: int = Query(default=20, ge=1, le=100, description="Max articles to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
):
    """
    Retrieve persistent saved news articles ordered by published_at DESC.
    Always reads from Supabase / database storage.
    """
    saved_articles = await news_repository.get_saved_articles(limit=limit, offset=offset)
    metadata = await news_repository.get_latest_sync_metadata()

    # Normalize fields for frontend component compatibility
    formatted = []
    for art in saved_articles:
        article_id = (
            str(art.get("id"))
            if art.get("id")
            else (art.get("source_url") or art.get("url") or f"news-{art.get('title', '')[:30]}")
        )
        formatted.append({
            "id": article_id,
            "title": art.get("title", ""),
            "description": art.get("description", ""),
            "source": art.get("source_name") or art.get("source") or "News",
            "source_name": art.get("source_name") or art.get("source") or "News",
            "url": art.get("source_url") or art.get("url"),
            "source_url": art.get("source_url") or art.get("url"),
            "image_url": art.get("image_url"),
            "published_at": art.get("published_at"),
            "fetched_at": art.get("fetched_at"),
            "category": art.get("category") or "Technology",
            "company": art.get("company"),
            "company_tag": art.get("company"),
            "created_at": art.get("created_at"),
        })

    return NewsListResponse(
        articles=formatted,
        total_count=metadata.get("total_count", len(formatted)),
        last_updated=metadata.get("last_updated"),
        schedule_notice="Updates daily at 10:00 AM & 10:00 PM IST",
        is_supabase_connected=metadata.get("is_supabase_connected", False),
    )


@router.post("/refresh", response_model=NewsRefreshResponse)
async def trigger_news_refresh():
    """
    Manual trigger endpoint to fetch fresh real news from GNews,
    deduplicate, and persist to Supabase PostgreSQL.
    """
    res = await sync_news_job()
    metadata = await news_repository.get_latest_sync_metadata()

    if res.get("success"):
        return NewsRefreshResponse(
            success=True,
            message="News synchronization completed successfully.",
            articles_fetched=res.get("articles_fetched", 0),
            articles_inserted=res.get("articles_inserted", 0),
            total_saved=metadata.get("total_count", 0),
            last_updated=metadata.get("last_updated"),
        )
    else:
        return NewsRefreshResponse(
            success=False,
            message=f"Sync encountered an issue: {res.get('error', 'Unknown')}. Preserved previously saved news.",
            articles_fetched=0,
            articles_inserted=0,
            total_saved=metadata.get("total_count", 0),
            last_updated=metadata.get("last_updated"),
        )


@router.get("/status")
async def get_news_pipeline_status():
    """
    Get runtime health and configuration status of the news pipeline,
    including scheduler status, next run time in IST, and database statistics.
    """
    scheduler_info = get_scheduler_status()
    db_metadata = await news_repository.get_latest_sync_metadata()

    return {
        "status": "active",
        "scheduler": scheduler_info,
        "database": {
            "supabase_connected": db_metadata.get("is_supabase_connected", False),
            "total_articles": db_metadata.get("total_count", 0),
            "last_updated": db_metadata.get("last_updated"),
        },
        "gnews_configured": gnews_service.is_configured(),
    }
