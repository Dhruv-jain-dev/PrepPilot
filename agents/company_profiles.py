from __future__ import annotations

COMPANY_PROFILES = {
    "Amazon": "Leadership Principles, especially Ownership, Customer Obsession, Bias for Action, and Dive Deep.",
    "Google": "clear problem solving, scalable systems, collaboration, and thoughtful technical trade-offs.",
    "Microsoft": "growth mindset, inclusive collaboration, customer focus, cloud engineering, and pragmatic delivery.",
    "JP Morgan": "reliable financial systems, risk awareness, security, Java/Python foundations, and teamwork.",
    "NVIDIA": "high-performance computing, systems thinking, parallelism, AI, and rigorous engineering.",
    "General": "role-relevant technical depth, communication, ownership, and measurable impact.",
}


def company_interview_focus(company: str) -> str:
    return COMPANY_PROFILES.get(company, COMPANY_PROFILES["General"])
