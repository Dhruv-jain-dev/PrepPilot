from __future__ import annotations

import re

from .gemini import generate


def evaluate_answer(question: str, answer: str) -> dict:
    prompt = f"""Question: {question}
Candidate answer: {answer}

Evaluate the answer in plain text. Include headings: Overall score (out of 10), Communication, Technical accuracy, Strengths, Improvements, and a rewritten STAR-style outline."""
    feedback = generate("You are a fair interview evaluator. Give specific, constructive feedback; do not invent candidate experience.", prompt)
    if feedback:
        score_match = re.search(r"(?:overall )?score[^0-9]*(10|[0-9](?:\.[0-9])?)", feedback.lower())
        score = float(score_match.group(1)) if score_match else 7.0
        return {"score": score, "feedback": feedback}
    word_count = len(answer.split())
    score = min(9.0, max(3.0, round(word_count / 28 + 4, 1)))
    return {"score": score, "feedback": "Gemini is not configured, so this is a length-based practice score. Add GEMINI_API_KEY for detailed coaching."}
