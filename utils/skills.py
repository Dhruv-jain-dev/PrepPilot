from __future__ import annotations

import re

SKILL_CATALOG = {
    "python", "java", "c++", "c", "javascript", "typescript", "sql", "html", "css",
    "react", "node", "fastapi", "django", "flask", "streamlit", "mongodb", "mysql",
    "postgresql", "docker", "kubernetes", "aws", "azure", "gcp", "git", "github",
    "linux", "rest", "api", "redis", "kafka", "spark", "pandas", "numpy", "tensorflow",
    "pytorch", "machine learning", "data structures", "algorithms", "dsa", "oop", "dbms",
    "operating systems", "computer networks", "ci/cd", "agile", "figma",
}


def extract_skills(text: str) -> list[str]:
    normalised = re.sub(r"\s+", " ", text.lower())
    return sorted(skill for skill in SKILL_CATALOG if re.search(rf"(?<!\w){re.escape(skill)}(?!\w)", normalised))


def match_resume_to_job(resume_text: str, job_text: str) -> dict:
    resume_skills, job_skills = set(extract_skills(resume_text)), set(extract_skills(job_text))
    required = sorted(job_skills)
    strong = sorted(resume_skills & job_skills)
    missing = sorted(job_skills - resume_skills)
    score = round((len(strong) / len(required)) * 100) if required else 0
    return {
        "score": score,
        "required_skills": required,
        "strong_skills": strong,
        "missing_skills": missing,
        "suggestions": [f"Build a small project demonstrating {skill.title()}." for skill in missing[:5]],
    }
