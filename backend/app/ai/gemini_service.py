import os
from typing import Optional
from google import genai
from google.genai.errors import APIError


class GeminiService:
    """Service wrapper for interacting with the Google Gemini API using the official google-genai SDK."""

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or os.getenv("GEMINI_API_KEY")
        self._client: Optional[genai.Client] = None

    def _get_client(self) -> genai.Client:
        """Lazily initialize the Gemini client."""
        key = self._api_key or os.getenv("GEMINI_API_KEY")
        if not key or key.strip() == "" or key.strip() == "your_gemini_api_key_here":
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
        model: str = "gemini-3.6-flash",
    ) -> str:
        """
        Generate a text response from Gemini.
        
        Args:
            prompt: The input text prompt to send to Gemini.
            model: The Gemini model identifier (default: gemini-2.5-flash).
            
        Returns:
            The generated response string.
            
        Raises:
            ValueError: If prompt is invalid or API key is missing.
            RuntimeError: If the API call fails.
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        client = self._get_client()
        try:
            # Use async client in google-genai SDK
            response = await client.aio.models.generate_content(
                model=model,
                contents=prompt.strip(),
            )
            if not response or not response.text:
                raise RuntimeError("No text content returned from Gemini API.")
            return response.text
        except APIError as e:
            raise RuntimeError(f"Gemini API returned an error: {e.message or str(e)}")
        except Exception as e:
            raise RuntimeError(f"Failed to generate AI response: {str(e)}")


# Singleton instance
gemini_service = GeminiService()
