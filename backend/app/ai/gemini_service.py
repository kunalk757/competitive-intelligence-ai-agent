import os
import logging
from typing import Optional
from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError

load_dotenv()
logger = logging.getLogger("gemini_service")


class GeminiService:
    """Service wrapper for interacting with the Google Gemini API using the official google-genai SDK."""

    def __init__(self, api_key: Optional[str] = None):
        load_dotenv(override=True)
        self._api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self._client: Optional[genai.Client] = None

    def get_api_key(self) -> str:
        """Dynamically retrieve GEMINI_API_KEY or GOOGLE_API_KEY."""
        if self._api_key and self._api_key.strip() and not self._api_key.startswith("your_"):
            return self._api_key.strip()
        load_dotenv(override=True)
        key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
        return key.strip()

    def is_configured(self) -> bool:
        """Check whether a valid Gemini API key is configured."""
        key = self.get_api_key()
        return bool(key and not key.startswith("your_") and len(key) > 5)

    def _get_client(self) -> genai.Client:
        """Lazily initialize the Gemini client."""
        key = self.get_api_key()
        if not self.is_configured():
            raise ValueError(
                "GEMINI_API_KEY environment variable is not configured. Please set a valid Gemini API key."
            )
        if self._client is None or self._api_key != key:
            self._api_key = key
            self._client = genai.Client(api_key=key)
        return self._client

    async def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
    ) -> str:
        """
        Generate a text response from Gemini.
        
        Args:
            prompt: The input text prompt to send to Gemini.
            model: The Gemini model identifier (default: GEMINI_MODEL env or gemini-2.5-flash).
            
        Returns:
            The generated response string.
            
        Raises:
            ValueError: If prompt is invalid or API key is missing.
            RuntimeError: If the API call fails.
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        target_model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        client = self._get_client()

        # Try target model, fallback to alternative models if model name is invalid
        candidate_models = [target_model]
        for fallback in ["gemini-2.0-flash", "gemini-1.5-flash"]:
            if fallback not in candidate_models:
                candidate_models.append(fallback)

        last_error = None
        for m in candidate_models:
            try:
                logger.info(f"Generating content with Gemini model: {m}")
                response = await client.aio.models.generate_content(
                    model=m,
                    contents=prompt.strip(),
                )
                if response and response.text:
                    return response.text
            except APIError as e:
                logger.warning(f"Gemini API error with model {m}: {e.message or str(e)}")
                last_error = e
            except Exception as e:
                logger.warning(f"Gemini execution error with model {m}: {str(e)}")
                last_error = e

        error_detail = getattr(last_error, "message", str(last_error)) if last_error else "Unknown error"
        logger.error(f"All Gemini models failed. Last error: {error_detail}", exc_info=True)
        raise RuntimeError(f"Gemini API error: {error_detail}")


# Singleton instance
gemini_service = GeminiService()

