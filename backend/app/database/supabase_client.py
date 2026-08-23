import os
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("news_supabase")


class SupabaseNewsRepository:
    """
    Repository for managing persistent news articles in Supabase PostgreSQL,
    with local fallback storage to ensure zero downtime and seamless testing.
    """

    def __init__(self, local_storage_file: Optional[str] = None):
        self.supabase_url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
        self.supabase_key = os.getenv("SUPABASE_KEY", "").strip()
        self._local_storage_file = (
            local_storage_file
            or os.path.join(
                os.path.dirname(__file__), "..", "..", "data", "saved_news.json"
            )
        )
        self._ensure_local_storage_dir()

    def is_configured(self) -> bool:
        """Check if active Supabase configuration is present."""
        return bool(
            self.supabase_url
            and self.supabase_key
            and not self.supabase_url.startswith("https://your-project")
        )

    def _ensure_local_storage_dir(self):
        storage_dir = os.path.dirname(self._local_storage_file)
        if not os.path.exists(storage_dir):
            try:
                os.makedirs(storage_dir, exist_ok=True)
            except Exception as e:
                logger.warning(f"Could not create data directory: {e}")

    def _read_local_articles(self) -> List[Dict[str, Any]]:
        if os.path.exists(self._local_storage_file):
            try:
                with open(self._local_storage_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
            except Exception as e:
                logger.error(f"Error reading local articles file: {e}")
        return []

    def _write_local_articles(self, articles: List[Dict[str, Any]]) -> None:
        try:
            with open(self._local_storage_file, "w", encoding="utf-8") as f:
                json.dump(articles, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving local articles: {e}")

    def _get_headers(self) -> Dict[str, str]:
        return {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation,resolution=ignore-duplicates",
        }

    async def get_saved_articles(
        self, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Fetch saved articles ordered by published_at descending.
        """
        if self.is_configured():
            try:
                url = f"{self.supabase_url}/rest/v1/news_articles"
                params = {
                    "select": "*",
                    "order": "published_at.desc.nullslast,created_at.desc",
                    "limit": str(limit),
                    "offset": str(offset),
                }
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(
                        url, headers=self._get_headers(), params=params
                    )
                    if response.status_code == 200:
                        return response.json()
                    else:
                        logger.warning(
                            f"Supabase REST returned {response.status_code}: {response.text}. Falling back to local store."
                        )
            except Exception as e:
                logger.error(
                    f"Failed to query Supabase REST: {e}. Falling back to local store."
                )

        # Fallback / Local persistent store
        articles = self._read_local_articles()
        # Sort by published_at descending
        articles.sort(
            key=lambda x: (
                x.get("published_at") or x.get("created_at") or ""
            ),
            reverse=True,
        )
        return articles[offset : offset + limit]

    async def upsert_articles(
        self, articles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Deduplicate and insert new articles using source_url unique constraint.
        Keeps existing articles and does not overwrite existing data.
        """
        if not articles:
            return {"inserted": 0, "total": len(await self.get_saved_articles())}

        inserted_count = 0

        # Attempt Supabase cloud insertion first if configured
        if self.is_configured():
            try:
                url = f"{self.supabase_url}/rest/v1/news_articles"
                headers = self._get_headers()
                # Use on_conflict for deduplication
                headers["Prefer"] = "resolution=ignore-duplicates,return=representation"
                async with httpx.AsyncClient(timeout=15.0) as client:
                    response = await client.post(
                        url,
                        headers=headers,
                        json=articles,
                    )
                    if response.status_code in (200, 201):
                        inserted = response.json()
                        inserted_count = len(inserted) if isinstance(inserted, list) else 0
                        logger.info(
                            f"Successfully synced {inserted_count} new articles to Supabase PostgreSQL."
                        )
                    else:
                        logger.warning(
                            f"Supabase upsert status {response.status_code}: {response.text}"
                        )
            except Exception as e:
                logger.error(f"Error upserting articles to Supabase: {e}")

        # Always update local storage mirror to ensure persistent fallback and resilience
        local_existing = self._read_local_articles()
        existing_urls = {
            a.get("source_url")
            for a in local_existing
            if a.get("source_url")
        }

        new_local_items = []
        now_iso = datetime.now(timezone.utc).isoformat()
        for article in articles:
            url = article.get("source_url")
            if url and url not in existing_urls:
                existing_urls.add(url)
                if not article.get("created_at"):
                    article["created_at"] = now_iso
                if not article.get("fetched_at"):
                    article["fetched_at"] = now_iso
                new_local_items.append(article)

        if new_local_items:
            combined = new_local_items + local_existing
            self._write_local_articles(combined)
            if not self.is_configured():
                inserted_count = len(new_local_items)

        total_saved = len(self._read_local_articles())
        return {
            "inserted": inserted_count,
            "total": total_saved,
            "storage": "supabase" if self.is_configured() else "local_resilient_store",
        }

    async def get_latest_sync_metadata(self) -> Dict[str, Any]:
        """
        Get the most recent fetched_at timestamp and article count.
        """
        articles = await self.get_saved_articles(limit=1)
        total_articles = await self.get_saved_articles(limit=500)
        
        last_updated = None
        if articles:
            last_updated = (
                articles[0].get("fetched_at")
                or articles[0].get("published_at")
                or articles[0].get("created_at")
            )

        return {
            "last_updated": last_updated,
            "total_count": len(total_articles),
            "is_supabase_connected": self.is_configured(),
        }


# Global repository instance
news_repository = SupabaseNewsRepository()
