from fastapi import APIRouter
from datetime import datetime, timezone
from app.database.supabase_client import news_repository
from app.database.company_repository import company_repository
from app.database.paper_repository import paper_repository

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "competitive-intelligence-agent-backend",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "0.1.0",
        "database_check": "/health/db",
    }


@router.get("/health/db")
async def db_health_check():
    """
    Safe, credential-free database configuration and live readiness status endpoint.
    """
    is_news_configured = news_repository.is_configured()
    is_company_configured = company_repository.is_configured()
    is_paper_configured = paper_repository.is_configured()
    is_configured = is_news_configured or is_company_configured or is_paper_configured

    supabase_connected = False
    if is_configured:
        try:
            # Perform a lightweight read probe against saved articles
            articles = await news_repository.get_saved_articles(limit=1)
            supabase_connected = True
        except Exception:
            supabase_connected = False

    return {
        "status": "healthy" if (supabase_connected or not is_configured) else "degraded",
        "storage_mode": "supabase_postgresql" if (is_configured and supabase_connected) else "local_resilient_store",
        "is_supabase_configured": is_configured,
        "is_supabase_connected": supabase_connected,
        "tables_supported": ["news_articles", "company_profiles", "research_papers"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
