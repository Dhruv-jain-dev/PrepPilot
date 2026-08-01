from __future__ import annotations

import re
import json

from .gemini import generate


def evaluate_answer(question: str, answer: str) -> dict:
    prompt = f"""Question: {question}
Candidate answer: {answer}

Return valid JSON only with this schema:
{{"score": 0-10, "technical_score": 0-10, "communication_score": 0-10,
"confidence_score": 0-10, "strengths": ["..."], "improvements": ["..."],
"weak_topics": ["..."], "feedback": "...", "star_outline": "..."}}
Do not invent experience or facts. Scores may use one decimal place."""
    feedback = generate("You are a fair interview evaluator. Give specific, constructive feedback; do not invent candidate experience.", prompt)
    if feedback:
        parsed = _parse_evaluation(feedback)
        if parsed:
            return parsed
        score_match = re.search(r"(?:overall )?score[^0-9]*(10|[0-9](?:\.[0-9])?)", feedback.lower())
        score = float(score_match.group(1)) if score_match else 7.0
        return _normalise({"score": score, "feedback": feedback})
    word_count = len(answer.split())
    score = min(9.0, max(3.0, round(word_count / 28 + 4, 1)))
    return _normalise({"score": score, "feedback": "Gemini is not configured, so this is a length-based practice score. Add GEMINI_API_KEY for detailed coaching."})


def _parse_evaluation(raw: str) -> dict | None:
    try:
        candidate = raw.strip()
        if candidate.startswith("```"):
            candidate = candidate.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        return _normalise(json.loads(candidate))
    except (json.JSONDecodeError, TypeError, ValueError):
        return None


def _normalise(result: dict) -> dict:
    score = max(0.0, min(10.0, float(result.get("score", 5))))
    result["score"] = score
    for key in ("technical_score", "communication_score", "confidence_score"):
        result[key] = max(0.0, min(10.0, float(result.get(key, score))))
    for key in ("strengths", "improvements", "weak_topics"):
        value = result.get(key, [])
        result[key] = value if isinstance(value, list) else [str(value)]
    result.setdefault("feedback", "No written feedback was returned.")
    result.setdefault("star_outline", "Use Situation, Task, Action, and Result to make the answer concrete.")
    return result
