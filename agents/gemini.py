from __future__ import annotations

import os

from google import genai
from google.genai import types


def generate(instructions: str, prompt: str) -> str | None:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return None
    client = genai.Client(api_key=key)
    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
        contents=prompt,
        config=types.GenerateContentConfig(system_instruction=instructions),
    )
    return response.text
