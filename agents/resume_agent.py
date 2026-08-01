from __future__ import annotations

import json

from .gemini import generate


def rewrite_resume_bullet(bullet: str, target_role: str, missing_skills: list[str]) -> str:
    """Return an ATS-friendly rewrite without inventing experience."""
    if not bullet.strip():
        return ""
    prompt = f"""Target role: {target_role or 'software engineer'}
Candidate bullet: {bullet}
Relevant missing job keywords: {', '.join(missing_skills[:6]) or 'none'}

Rewrite this as one concise, impact-oriented resume bullet. Preserve facts exactly; do not claim tools, metrics, or outcomes not present in the original. If a keyword is unsupported by the bullet, do not insert it. Return only the rewritten bullet."""
    rewritten = generate("You are a precise ATS resume editor. Never invent candidate experience.", prompt)
    return rewritten.strip().lstrip("- ") if rewritten else bullet.strip()


def ats_summary(match: dict) -> dict:
    missing = match.get("missing_skills", [])
    return {
        "keyword_coverage": match.get("score", 0),
        "matched_keywords": match.get("strong_skills", []),
        "missing_keywords": missing,
        "priority_keywords": missing[:5],
        "next_action": "Use only truthful evidence when adding missing keywords to your resume.",
    }
