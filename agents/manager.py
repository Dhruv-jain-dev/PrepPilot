from __future__ import annotations

from agents.question_agent import generate_questions
from utils.skills import match_resume_to_job


def build_interview_plan(resume_text: str, job_text: str, company: str, difficulty: str) -> dict:
    match = match_resume_to_job(resume_text, job_text)
    questions = generate_questions(resume_text, job_text, company, difficulty)
    readiness = round(match["score"] * 0.7 + min(30, len(match["strong_skills"]) * 5))
    return {"match": match, "questions": questions, "readiness": min(100, readiness)}
