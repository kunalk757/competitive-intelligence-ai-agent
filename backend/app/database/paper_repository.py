"""
Repository for managing persistent Research Papers in Supabase PostgreSQL,
with local JSON fallback storage to ensure resilience and zero downtime.
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("paper_repository")


class PaperRepository:
    """
    Repository for managing persistent academic and research papers
    in Supabase PostgreSQL, with local JSON file fallback.
    """

    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
        self.supabase_key = os.getenv("SUPABASE_KEY", "").strip()
        self._local_storage_file = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", "saved_papers.json"
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
                logger.warning(f"Could not create paper data directory: {e}")

    def _read_local_papers(self) -> List[Dict[str, Any]]:
        if os.path.exists(self._local_storage_file):
            try:
                with open(self._local_storage_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
            except Exception as e:
                logger.error(f"Error reading local research papers file: {e}")
        return []

    def _write_local_papers(self, papers: List[Dict[str, Any]]) -> None:
        try:
            with open(self._local_storage_file, "w", encoding="utf-8") as f:
                json.dump(papers, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving local research papers: {e}")

    def _get_headers(self) -> Dict[str, str]:
        return {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation,resolution=merge-duplicates",
        }

    async def get_saved_papers(
        self, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Fetch saved research papers ordered by citation_count and year descending.
        """
        if self.is_configured():
            try:
                url = f"{self.supabase_url}/rest/v1/research_papers"
                params = {
                    "select": "*",
                    "order": "citation_count.desc.nullslast,year.desc.nullslast,fetched_at.desc",
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
                    f"Failed to query Supabase REST for research papers: {e}. Falling back to local store."
                )

        # Fallback to local store
        papers = self._read_local_papers()
        # Sort by citation count or year
        papers.sort(
            key=lambda x: (
                x.get("citation_count") or 0,
                x.get("year") or 0,
                x.get("fetched_at") or "",
            ),
            reverse=True,
        )
        return papers[offset : offset + limit]

    async def save_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Save or upsert multiple research papers, preventing duplicates by external_id / URL.
        """
        if not papers:
            return []

        now_iso = datetime.now(timezone.utc).isoformat()
        clean_papers = []

        for p in papers:
            title = p.get("title", "").strip()
            if not title:
                continue

            external_id = p.get("external_id") or p.get("paperId") or p.get("id")
            if not external_id:
                # Generate deterministic fallback ID from title
                external_id = f"custom_{abs(hash(title.lower()))}"

            clean_papers.append(
                {
                    "external_id": str(external_id),
                    "title": title,
                    "authors": p.get("authors") or [],
                    "abstract": p.get("abstract") or "",
                    "year": p.get("year"),
                    "venue": p.get("venue") or "",
                    "url": p.get("url") or "",
                    "citation_count": p.get("citation_count") or p.get("citationCount") or 0,
                    "fields_of_study": p.get("fields_of_study") or p.get("fieldsOfStudy") or [],
                    "source": p.get("source") or "Semantic Scholar",
                    "fetched_at": p.get("fetched_at") or now_iso,
                }
            )

        if not clean_papers:
            return []

        # 1. Save to Supabase if configured
        if self.is_configured():
            try:
                url = f"{self.supabase_url}/rest/v1/research_papers?on_conflict=external_id"
                async with httpx.AsyncClient(timeout=12.0) as client:
                    response = await client.post(
                        url,
                        headers=self._get_headers(),
                        json=clean_papers,
                    )
                    if response.status_code in [200, 201]:
                        logger.info(f"Successfully saved {len(clean_papers)} papers to Supabase.")
                    else:
                        logger.warning(
                            f"Supabase upsert returned {response.status_code}: {response.text}. Saving locally."
                        )
            except Exception as e:
                logger.error(f"Failed to upsert papers in Supabase: {e}. Saving locally.")

        # 2. Always maintain local cache for offline resilience and fast queries
        existing = self._read_local_papers()
        paper_map = {item.get("external_id"): item for item in existing if item.get("external_id")}
        
        # Also map by title lower for deduplication
        title_map = {item.get("title", "").lower().strip(): item for item in existing if item.get("title")}

        saved_count = 0
        for cp in clean_papers:
            ext_id = cp["external_id"]
            title_key = cp["title"].lower().strip()
            
            if ext_id in paper_map:
                paper_map[ext_id].update(cp)
            elif title_key in title_map:
                title_map[title_key].update(cp)
            else:
                paper_map[ext_id] = cp
                title_map[title_key] = cp
                saved_count += 1

        updated_list = list(paper_map.values())
        self._write_local_papers(updated_list)
        logger.info(f"Local storage updated with {len(updated_list)} total papers ({saved_count} new).")

        return clean_papers


# Global singleton instance
paper_repository = PaperRepository()
