"""Gemini API client for audio analysis."""

import json
import os
import time
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

_MODEL_NAME = "gemini-2.0-flash-exp"

_SYSTEM_PROMPT = """\
Tu es un assistant d'entretien technique discret.
Écoute l'audio et détecte s'il contient une question technique.

Si tu détectes une question technique, réponds UNIQUEMENT avec ce JSON :
{"question": "la question détectée", "answer": "réponse concise (3-5 phrases)", "bullets": ["point clé 1", "point clé 2", "point clé 3", "point clé 4"]}

Si tu n'entends aucune question claire, réponds UNIQUEMENT : NO_QUESTION

Règles :
- Réponse en français
- 3 à 5 phrases max pour "answer"
- Exactement 4 bullet points concis pour "bullets"
- JSON valide, sans markdown ni backticks
"""


@dataclass
class AnalysisResult:
    question: str
    answer: str
    bullets: list[str]
    latency: str


class GeminiClient:
    """Client for Gemini API interactions."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        """Initialize Gemini client with API key."""
        self._api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not self._api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")

        self._client = genai.Client(api_key=self._api_key)

    def analyze_audio(self, wav_bytes: bytes) -> Optional[AnalysisResult]:
        """Send WAV audio to Gemini and return structured result or None."""
        start = time.perf_counter()
        try:
            response = self._client.models.generate_content(
                model=_MODEL_NAME,
                contents=[
                    types.Part.from_bytes(data=wav_bytes, mime_type="audio/wav"),
                    _SYSTEM_PROMPT,
                ],
            )
        except Exception as e:
            print(f"[gemini] Error: {e}")
            return None

        elapsed = time.perf_counter() - start
        latency = f"{elapsed:.1f}s"
        text = response.text.strip()
        print(f"[gemini] Réponse reçue en {latency} ({len(text)} chars)")
        return self._parse_response(text, latency)

    def _parse_response(self, text: str, latency: str) -> Optional[AnalysisResult]:
        """Parse Gemini response text into an AnalysisResult."""
        if "NO_QUESTION" in text:
            print("[gemini] Pas de question détectée (NO_QUESTION)")
            return None

        # Strip markdown code fences if present
        cleaned = text
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]
        cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
            result = AnalysisResult(
                question=data.get("question", "Question détectée"),
                answer=data.get("answer", ""),
                bullets=data.get("bullets", []),
                latency=latency,
            )
            print(f"[gemini] Question détectée : {result.question}")
            return result
        except json.JSONDecodeError:
            print(f"[gemini] Réponse non-JSON, texte brut utilisé")
            return AnalysisResult(
                question="Question détectée",
                answer=text,
                bullets=[],
                latency=latency,
            )
