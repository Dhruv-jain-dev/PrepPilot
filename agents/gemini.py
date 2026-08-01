from __future__ import annotations

import os
import logging
import time

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


def generate(instructions: str, prompt: str) -> str | None:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return None
    client = genai.Client(api_key=key)
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
                contents=prompt,
                config=types.GenerateContentConfig(system_instruction=instructions),
            )
            return response.text
        except Exception as exc:
            logger.warning("Gemini request failed (attempt %s/3): %s", attempt + 1, exc)
            if attempt == 2:
                return None
            time.sleep(2 ** attempt)
    return None
