import os
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("gnews_service")

# Keywords for automatic company tagging
COMPANY_KEYWORDS = {
    "NVIDIA": ["nvidia", "nvda", "geforce", "cuda", "blackwell", "hopper", "h100", "b200"],
    "Google": ["google", "alphabet", "deepmind", "gemini", "tpu", "waymo"],
    "AMD": ["amd", "ryzen", "radeon", "instinct", "mi300", "lisa su"],
    "Microsoft": ["microsoft", "azure", "copilot", "satya nadella"],
    "OpenAI": ["openai", "chatgpt", "gpt-4", "gpt-5", "sam altman", "sora", "o1"],
    "Intel": ["intel", "pat gelsinger", "xeon", "gaudi", "core ultra"],
    "Apple": ["apple", "m3", "m4", "apple intelligence", "tim cook", "iphone"],
    "Broadcom": ["broadcom", "avago", "hock tan"],
    "TSMC": ["tsmc", "taiwan semiconductor", "foundry", "2nm", "3nm"],
    "Meta": ["meta", "facebook", "llama", "zuckerberg"],
    "Amazon": ["amazon", "aws", "trainium", "inferentia", "bedrock"],
    "Qualcomm": ["qualcomm", "snapdragon", "oryon"],
    "Arm": ["arm holdings", "arm architecture", "cortex"],
}

CATEGORY_KEYWORDS = {
    "Artificial Intelligence": ["artificial intelligence", "ai model", "llm", "deep learning", "neural network", "machine learning", "deepmind", "gemini", "chatgpt", "generative ai", "copilot"],
    "Semiconductors": ["semiconductor", "chip", "silicon", "foundry", "wafer", "gpu", "cpu", "interconnect", "tpu", "asic", "processor"],
    "Cloud & Infrastructure": ["cloud", "data center", "server", "aws", "azure", "infrastructure"],
    "Strategic Alliances": ["partnership", "deal", "acquisition", "merger", "joint venture", "investment"],
    "Patents & Tech": ["patent", "architecture", "breakthrough", "benchmark", "research paper"],
}


def detect_company(text: str) -> Optional[str]:
    """Detect prominent technology company mentioned in article text."""
    lower_text = text.lower()
    for company, keywords in COMPANY_KEYWORDS.items():
        for kw in keywords:
            if kw in lower_text:
                return company
    return None


def detect_category(text: str) -> str:
    """Detect intelligence category from article text."""
    lower_text = text.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in lower_text:
                return category
    return "Technology"


class GNewsService:
    """
    Service for fetching real-time news articles from GNews API v4.
    """

    BASE_URL = "https://gnews.io/api/v4"

    def __init__(self):
        pass

    def get_api_key(self) -> str:
        """Dynamically retrieve GNEWS_API_KEY from environment."""
        load_dotenv(override=True)
        return os.getenv("GNEWS_API_KEY", "").strip()

    def is_configured(self) -> bool:
        """Check whether GNEWS_API_KEY is present."""
        key = self.get_api_key()
        return bool(key and not key.startswith("your_") and len(key) > 5)

    async def fetch_latest_news(
        self, query: Optional[str] = None, max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fetch real news articles from GNews API and normalize them.
        Returns a list of structured article dictionaries ready for database storage.
        """
        if not self.is_configured():
            logger.warning(
                "GNEWS_API_KEY is not set or invalid in environment. Skipping external GNews fetch."
            )
            return []

        api_key = self.get_api_key()
        endpoint = f"{self.BASE_URL}/top-headlines"
        params: Dict[str, Any] = {
            "apikey": api_key,
            "lang": "en",
            "max": str(min(max_results, 10)),
        }

        if query:
            endpoint = f"{self.BASE_URL}/search"
            params["q"] = query
        else:
            params["category"] = "technology"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(endpoint, params=params)

                if response.status_code == 200:
                    data = response.json()
                    articles_raw = data.get("articles", [])
                    return self._normalize_articles(articles_raw)
                else:
                    logger.error(
                        f"GNews API returned status {response.status_code}: {response.text}"
                    )
                    return []

        except httpx.RequestError as exc:
            logger.error(f"Network error while connecting to GNews API: {exc}")
            return []
        except Exception as exc:
            logger.error(f"Unexpected error while fetching GNews articles: {exc}")
            return []

    def _normalize_articles(
        self, articles_raw: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Normalize raw GNews articles into our database schema structure.
        """
        normalized: List[Dict[str, Any]] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        for art in articles_raw:
            url = art.get("url", "").strip()
            title = art.get("title", "").strip()

            if not url or not title:
                continue

            description = art.get("description", "") or ""
            source_info = art.get("source", {})
            source_name = source_info.get("name", "GNews") if isinstance(source_info, dict) else "GNews"
            image_url = art.get("image") or None
            published_at = art.get("publishedAt") or now_iso

            combined_text = f"{title} {description} {source_name}"
            company = detect_company(combined_text)
            category = detect_category(combined_text)

            normalized.append(
                {
                    "title": title,
                    "description": description,
                    "source_name": source_name,
                    "source_url": url,
                    "image_url": image_url,
                    "published_at": published_at,
                    "fetched_at": now_iso,
                    "category": category,
                    "company": company,
                    "created_at": now_iso,
                }
            )

        return normalized

    async def fetch_company_news(
        self, company_name: str, max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fetch company-specific news articles from GNews API.
        """
        clean_name = company_name.strip()
        if not clean_name:
            return []

        articles = await self.fetch_latest_news(query=f'"{clean_name}"', max_results=max_results)
        # If strict quotes return 0, fallback to standard query
        if not articles:
            articles = await self.fetch_latest_news(query=clean_name, max_results=max_results)

        # Ensure company tag is accurately associated
        for art in articles:
            if not art.get("company"):
                art["company"] = clean_name

        return articles


# Global service instance
gnews_service = GNewsService()

