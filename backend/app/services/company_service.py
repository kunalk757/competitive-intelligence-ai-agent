import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from app.services.tavily_service import tavily_service
from app.services.gnews_service import gnews_service
from app.database.company_repository import company_repository
from app.database.supabase_client import news_repository

logger = logging.getLogger("company_service")


DEFAULT_TRACKED_COMPANIES: List[str] = [
    "NVIDIA",
    "AMD",
    "Intel",
    "Microsoft",
    "Google",
    "Apple",
    "Amazon",
    "Meta",
    "OpenAI",
    "Anthropic",
    "Tesla",
    "Samsung",
    "Qualcomm",
    "TSMC",
    "Broadcom",
    "IBM",
    "Oracle",
    "Salesforce",
    "Adobe",
    "Cisco",
]


class CompanySource(BaseModel):
    title: str
    url: str
    snippet: Optional[str] = None


class CompanyWebInfo(BaseModel):
    name: str
    overview: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    sources: List[CompanySource] = Field(default_factory=list)


class CompanyNewsItem(BaseModel):
    title: str
    description: Optional[str] = None
    source: str
    published_at: str
    url: str
    image_url: Optional[str] = None


class CompanyDetailsResponse(BaseModel):
    company: CompanyWebInfo
    news: List[CompanyNewsItem] = Field(default_factory=list)
    last_updated: Optional[str] = None
    cached: bool = False
    has_data: bool = False
    message: Optional[str] = None


class CompanyDataService:
    """
    Modular Company Data Service combining real-time Tavily web intelligence
    and real-time GNews articles with persistent Supabase/local caching.
    """

    def __init__(self):
        self.tavily = tavily_service
        self.gnews = gnews_service
        self.repository = company_repository
        self.news_repo = news_repository

    async def refresh_all_companies(
        self, companies: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Refresh intelligence and news for all specified companies (or default 20 companies).
        Updates persistent cache for each company.
        """
        targets = companies if companies and len(companies) > 0 else DEFAULT_TRACKED_COMPANIES
        now_iso = datetime.now(timezone.utc).isoformat()
        successful: List[str] = []
        failed: List[Dict[str, str]] = []

        logger.info(f"Starting batch company intelligence refresh for {len(targets)} companies...")

        for company_name in targets:
            clean_name = company_name.strip()
            if not clean_name:
                continue
            try:
                logger.info(f"Batch refreshing: {clean_name}")
                await self.get_company_details(company_name=clean_name, force_refresh=True)
                successful.append(clean_name)
            except Exception as e:
                logger.error(f"Error refreshing intelligence for '{clean_name}': {e}")
                failed.append({"company": clean_name, "error": str(e)})

        logger.info(
            f"Batch company refresh completed: {len(successful)} successful, {len(failed)} failed."
        )

        return {
            "success": len(successful) > 0 or len(failed) == 0,
            "message": f"Refreshed {len(successful)} of {len(targets)} companies.",
            "total_companies": len(targets),
            "successful_count": len(successful),
            "failed_count": len(failed),
            "successful_companies": successful,
            "failed_companies": failed,
            "timestamp": now_iso,
        }

    async def get_company_web_information(
        self, company_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Query Tavily for company overview, website, and source citations.
        """
        return await self.tavily.get_company_web_information(company_name)

    async def get_company_news(
        self, company_name: str, max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Query GNews for recent company news articles.
        """
        return await self.gnews.fetch_company_news(company_name, max_results=max_results)

    async def get_company_details(
        self, company_name: str, force_refresh: bool = False
    ) -> CompanyDetailsResponse:
        """
        Retrieve combined company intelligence & news.
        Utilizes caching to avoid repetitive API consumption on standard page loads,
        while automatically fetching missing components (Tavily overview or GNews news).
        """
        clean_name = company_name.strip()
        now_iso = datetime.now(timezone.utc).isoformat()

        # 1. Retrieve existing cached data
        cached_profile = await self.repository.get_company_profile(clean_name)
        cached_news = await self.repository.get_saved_company_news(clean_name, limit=10)

        has_cached_overview = bool(cached_profile and cached_profile.get("overview"))
        has_cached_news = bool(cached_news and len(cached_news) > 0)

        # If both overview and news exist in cache and not forcing refresh, return immediately
        if not force_refresh and has_cached_overview and has_cached_news:
            logger.info(f"Returning full cached company intelligence for: {clean_name}")
            return self._build_response(
                company_name=clean_name,
                profile=cached_profile,
                news_articles=cached_news,
                cached=True,
            )

        final_profile = cached_profile or {}
        final_news = cached_news or []

        # 2. Fetch fresh Tavily Overview if missing or refresh requested
        if force_refresh or not has_cached_overview:
            logger.info(f"Querying Tavily for company overview: '{clean_name}'...")
            tavily_result = await self.get_company_web_information(clean_name)

            if tavily_result and tavily_result.get("overview"):
                profile_payload = {
                    "company_name": clean_name,
                    "overview": tavily_result.get("overview"),
                    "website": tavily_result.get("website"),
                    "industry": tavily_result.get("industry") or final_profile.get("industry"),
                    "sources": tavily_result.get("sources") or [],
                    "fetched_at": now_iso,
                }
                saved_profile = await self.repository.save_company_profile(profile_payload)
                final_profile = saved_profile
            elif not final_profile.get("company_name"):
                final_profile = {
                    "company_name": clean_name,
                    "overview": None,
                    "website": None,
                    "industry": None,
                    "sources": [],
                    "fetched_at": None,
                }

        # 3. Fetch fresh GNews articles if missing or refresh requested
        if force_refresh or not has_cached_news:
            logger.info(f"Querying GNews for company news: '{clean_name}'...")
            gnews_articles = await self.get_company_news(clean_name, max_results=10)
            if gnews_articles:
                await self.news_repo.upsert_articles(gnews_articles)
                final_news = await self.repository.get_saved_company_news(clean_name, limit=10)

        return self._build_response(
            company_name=clean_name,
            profile=final_profile,
            news_articles=final_news,
            cached=False,
        )

    def _build_response(
        self,
        company_name: str,
        profile: Optional[Dict[str, Any]],
        news_articles: List[Dict[str, Any]],
        cached: bool = False,
    ) -> CompanyDetailsResponse:
        """
        Normalize internal structures into the official CompanyDetailsResponse.
        """
        prof = profile or {}
        raw_sources = prof.get("sources") or []
        sources: List[CompanySource] = []

        if isinstance(raw_sources, list):
            for s in raw_sources:
                if isinstance(s, dict) and s.get("url"):
                    sources.append(
                        CompanySource(
                            title=s.get("title") or company_name,
                            url=s.get("url"),
                            snippet=s.get("snippet"),
                        )
                    )

        company_info = CompanyWebInfo(
            name=company_name,
            overview=prof.get("overview"),
            website=prof.get("website"),
            industry=prof.get("industry"),
            sources=sources,
        )

        formatted_news: List[CompanyNewsItem] = []
        for art in news_articles:
            url = art.get("source_url") or art.get("url")
            title = art.get("title")
            if not url or not title:
                continue

            formatted_news.append(
                CompanyNewsItem(
                    title=title,
                    description=art.get("description"),
                    source=art.get("source_name") or art.get("source") or "News",
                    published_at=art.get("published_at") or art.get("fetched_at") or "",
                    url=url,
                    image_url=art.get("image_url") or art.get("image"),
                )
            )

        has_data = bool(company_info.overview or len(formatted_news) > 0)
        last_updated = prof.get("fetched_at")
        if not last_updated and formatted_news:
            last_updated = formatted_news[0].published_at

        return CompanyDetailsResponse(
            company=company_info,
            news=formatted_news,
            last_updated=last_updated,
            cached=cached,
            has_data=has_data,
            message="Live company intelligence retrieved." if has_data else "No company information found currently.",
        )


company_data_service = CompanyDataService()
