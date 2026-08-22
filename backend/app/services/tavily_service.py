import os
import logging
from typing import Any, Dict, List, Optional
import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("tavily_service")


class TavilyService:
    """
    Service for querying real-time web intelligence and company profiles via Tavily API.
    Used for objective company overview, business/tech facts, and source citations.
    """

    BASE_URL = "https://api.tavily.com/search"

    def __init__(self):
        pass

    def get_api_key(self) -> str:
        """Dynamically retrieve TAVILY_API_KEY from environment or instance."""
        inst_key = getattr(self, "api_key", None)
        if inst_key:
            return inst_key.strip()
        load_dotenv(override=True)
        return os.getenv("TAVILY_API_KEY", "").strip()

    def is_configured(self) -> bool:
        """Check whether TAVILY_API_KEY is present and valid."""
        key = self.get_api_key()
        return bool(
            key
            and not key.startswith("your_")
            and len(key) > 5
        )

    async def get_company_web_information(
        self, company_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Query Tavily for real-world overview, technology focus, and source URLs
        for the given company. Returns normalized dictionary or None if unconfigured/failed.
        """
        clean_name = company_name.strip()
        if not clean_name:
            return None

        if not self.is_configured():
            logger.warning(
                f"TAVILY_API_KEY is not configured in backend environment. Skipping live Tavily fetch for {clean_name}."
            )
            return None

        api_key = self.get_api_key()
        query = f"{clean_name} company overview business technology products website"

        payload = {
            "api_key": api_key,
            "query": query,
            "search_depth": "basic",
            "include_answer": True,
            "max_results": 5,
        }

        try:
            logger.info(f"Calling Tavily API for query: '{query}'")
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(self.BASE_URL, json=payload)
                if response.status_code != 200:
                    logger.error(
                        f"Tavily API returned {response.status_code}: {response.text}"
                    )
                    return None

                data = response.json()
                answer = data.get("answer") or ""
                results = data.get("results") or []

                # Extract sources
                sources: List[Dict[str, str]] = []
                extracted_website: Optional[str] = None

                for r in results:
                    url = r.get("url") or ""
                    title = r.get("title") or clean_name
                    snippet = r.get("content") or ""

                    if url:
                        sources.append({
                            "title": title,
                            "url": url,
                            "snippet": snippet[:280] if snippet else "",
                        })

                        # Identify likely official company website domain
                        lower_url = url.lower()
                        if not extracted_website:
                            sanitized = clean_name.lower().replace(" ", "").replace("-", "")
                            if (
                                f"{sanitized}.com" in lower_url
                                or f"{sanitized}.ai" in lower_url
                                or f"www.{sanitized}" in lower_url
                            ):
                                extracted_website = url

                # Fallback overview from top search result snippet if direct answer is empty
                if not answer and results:
                    top_content = results[0].get("content", "")
                    if top_content:
                        answer = top_content[:500].strip()

                logger.info(
                    f"Tavily successfully retrieved data for '{clean_name}': answer_len={len(answer)}, sources_count={len(sources)}"
                )

                return {
                    "name": clean_name,
                    "overview": answer if answer else None,
                    "website": extracted_website,
                    "sources": sources,
                }

        except httpx.TimeoutException:
            logger.error(f"Tavily API timed out while querying {clean_name}.")
            return None
        except Exception as e:
            logger.error(f"Error calling Tavily API for {clean_name}: {e}", exc_info=True)
            return None

    async def search(
        self, query: str, max_results: int = 5, include_answer: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a general search query on Tavily.
        Returns dict containing 'answer', 'results' (with title, url, content), or None.
        """
        clean_query = query.strip()
        if not clean_query:
            return None

        if not self.is_configured():
            logger.warning(
                f"TAVILY_API_KEY is not configured. Skipping Tavily search for '{clean_query}'."
            )
            return None

        api_key = self.get_api_key()
        payload = {
            "api_key": api_key,
            "query": clean_query,
            "search_depth": "basic",
            "include_answer": include_answer,
            "max_results": max(1, min(max_results, 10)),
        }

        try:
            logger.info(f"Calling Tavily Search API: '{clean_query}'")
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(self.BASE_URL, json=payload)
                if response.status_code != 200:
                    logger.error(
                        f"Tavily Search API returned {response.status_code}: {response.text}"
                    )
                    return None

                data = response.json()
                return {
                    "query": clean_query,
                    "answer": data.get("answer") or "",
                    "results": data.get("results") or [],
                }
        except Exception as e:
            logger.error(f"Error during Tavily search for '{clean_query}': {e}", exc_info=True)
            return None


tavily_service = TavilyService()

