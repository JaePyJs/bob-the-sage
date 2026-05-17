"""Lightweight Gemini REST API client using httpx.

Uses the Gemini 2.0 Flash REST API directly (no SDK required).
Falls back gracefully if GEMINI_API_KEY is not set.
"""

import httpx
from typing import Any
from backend.config import settings

GEMINI_API_KEY = settings.gemini_api_key or ""

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent"
)


async def generate_text(prompt: str, system: str = "", max_tokens: int = 2048) -> str:
    """Call Gemini 2.0 Flash and return the text response.

    Returns empty string if no API key is configured.
    Raises httpx.HTTPStatusError on API errors.
    """
    if not GEMINI_API_KEY:
        return ""

    contents: list[dict[str, Any]] = [{"role": "user", "parts": [{"text": prompt}]}]
    body: dict[str, Any] = {
        "contents": contents,
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": 0.7,
        },
    }
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            GEMINI_URL,
            params={"key": GEMINI_API_KEY},
            json=body,
        )
        resp.raise_for_status()
        data = resp.json()

    # Extract text from response
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        return ""
