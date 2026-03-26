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

_MODEL_NAME = "gemini-3-flash-preview"

_SYSTEM_PROMPT = """\
Tu es un assistant d'entretien technique discret.
Écoute l'audio et détecte s'il contient une question technique.

Si une question technique est détectée :
- "detected" = true
- "question" = la question détectée
- "answer" = réponse concise (3-5 phrases, en français)
- "bullets" = exactement 4 bullet points concis
- Repondez avec la langue d'origine de la question

Si aucune question claire n'est détectée :
- "detected" = false (les autres champs peuvent être vides)
"""

_RESPONSE_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "detected": types.Schema(type=types.Type.BOOLEAN),
        "question": types.Schema(type=types.Type.STRING),
        "answer": types.Schema(type=types.Type.STRING),
        "bullets": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(type=types.Type.STRING),
        ),
    },
    required=["detected"],
)


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
        self._config = types.GenerateContentConfig(
            system_instruction=_SYSTEM_PROMPT,
            temperature=0.3,
            max_output_tokens=2048,
            response_mime_type="application/json",
            response_schema=_RESPONSE_SCHEMA,
        )

    def analyze_audio(self, wav_bytes: bytes) -> Optional[AnalysisResult]:
        """Send WAV audio to Gemini and return structured result or None."""
        start = time.perf_counter()
        try:
            response = self._client.models.generate_content(
                model=_MODEL_NAME,
                contents=[
                    types.Part.from_bytes(data=wav_bytes, mime_type="audio/wav"),
                ],
                config=self._config,
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
        """Parse Gemini JSON response into an AnalysisResult."""
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            print(f"[gemini] Réponse non-JSON: {text[:100]}")
            return None

        if not data.get("detected", False):
            print("[gemini] Pas de question détectée")
            return None

        result = AnalysisResult(
            question=data.get("question", "Question détectée"),
            answer=data.get("answer", ""),
            bullets=data.get("bullets", []),
            latency=latency,
        )
        print(f"[gemini] Question détectée : {result.question}")
        return result
