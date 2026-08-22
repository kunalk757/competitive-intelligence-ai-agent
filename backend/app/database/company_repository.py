import os
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import httpx
from dotenv import load_dotenv
from app.database.supabase_client import news_repository

load_dotenv()

logger = logging.getLogger("company_repository")


class CompanyRepository:
    """
    Repository for managing persistent company profiles and company-specific
    intelligence in Supabase PostgreSQL, with local JSON file fallback.
    """

    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
        self.supabase_key = os.getenv("SUPABASE_KEY", "").strip()
        self._local_storage_file = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", "saved_companies.json"
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
                logger.warning(f"Could not create company data directory: {e}")

    def _read_local_profiles(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self._local_storage_file):
            try:
                with open(self._local_storage_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
            except Exception as e:
                logger.error(f"Error reading local company profiles file: {e}")
        return {}

    def _write_local_profiles(self, profiles: Dict[str, Dict[str, Any]]) -> None:
        try:
            with open(self._local_storage_file, "w", encoding="utf-8") as f:
                json.dump(profiles, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving local company profiles: {e}")

    def _get_headers(self) -> Dict[str, str]:
        return {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation,resolution=merge-duplicates",
        }

    async def get_company_profile(self, company_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch saved company profile from Supabase or local fallback.
        """
        clean_name = company_name.strip()
        if not clean_name:
            return None

        if self.is_configured():
            try:
                url = f"{self.supabase_url}/rest/v1/company_profiles"
                params = {
                    "select": "*",
                    "company_name": f"eq.{clean_name}",
                    "limit": "1",
                }
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(
                        url, headers=self._get_headers(), params=params
                    )
                    if response.status_code == 200:
                        records = response.json()
                        if records and isinstance(records, list):
                            return records[0]
                    else:
                        logger.warning(
                            f"Supabase company query returned {response.status_code}. Falling back to local store."
                        )
            except Exception as e:
                logger.error(f"Supabase company query failed: {e}. Falling back to local store.")

        # Local fallback
        local_profiles = self._read_local_profiles()
        return local_profiles.get(clean_name.lower())

    async def save_company_profile(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upsert company profile to Supabase and local cache.
        """
        clean_name = profile.get("company_name", "").strip()
        if not clean_name:
            return profile

        now_iso = datetime.now(timezone.utc).isoformat()
        profile["fetched_at"] = profile.get("fetched_at") or now_iso
        profile["created_at"] = profile.get("created_at") or now_iso

        # Save to local store
        local_profiles = self._read_local_profiles()
        local_profiles[clean_name.lower()] = profile
        self._write_local_profiles(local_profiles)

        if self.is_configured():
            try:
                url = f"{self.supabase_url}/rest/v1/company_profiles"
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        url,
                        headers=self._get_headers(),
                        json=[profile],
                    )
                    if response.status_code in [200, 201]:
                        records = response.json()
                        if records and isinstance(records, list):
                            return records[0]
            except Exception as e:
                logger.error(f"Failed to upsert company profile to Supabase: {e}")

        return profile

    async def get_saved_company_news(
        self, company_name: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve saved news articles associated with this company.
        """
        clean_name = company_name.strip()
        all_articles = await news_repository.get_saved_articles(limit=100)

        # Filter by company tag or presence in title/description
        matched: List[Dict[str, Any]] = []
        lower_name = clean_name.lower()

        for art in all_articles:
            art_company = (art.get("company") or "").lower()
            title = (art.get("title") or "").lower()
            description = (art.get("description") or "").lower()

            if (
                art_company == lower_name
                or lower_name in title
                or lower_name in description
            ):
                matched.append(art)

            if len(matched) >= limit:
                break

        return matched


company_repository = CompanyRepository()
