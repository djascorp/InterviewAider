"""Gemini API client for audio analysis."""

import os
from typing import Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

_MODEL_NAME = "gemini-3.1-flash-lite-preview"

_SYSTEM_PROMPT = """
Tu es un assistant d'entretien technique discret.
Si tu entends une question technique dans l'audio, fournis une réponse
concise et directement utilisable (3 à 5 phrases max), en français.
Si tu n'entends aucune question claire, réponds uniquement : NO_QUESTION
"""


class GeminiClient:
    """Client for Gemini API interactions."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        """Initialize Gemini client with API key."""
        self._api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not self._api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")

        self._client = genai.Client(api_key=self._api_key)

    def analyze_audio(self, wav_bytes: bytes) -> Optional[str]:
        """Send WAV audio to Gemini and return response or None if no question detected."""
        response = self._client.models.generate_content(
            model=_MODEL_NAME,
            contents=[
                types.Part.from_bytes(data=wav_bytes, mime_type="audio/wav"),
                _SYSTEM_PROMPT,
            ],
        )

        text = response.text.strip()
        return None if text == "NO_QUESTION" else text
