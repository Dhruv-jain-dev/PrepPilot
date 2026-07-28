from __future__ import annotations

from .gemini import generate


def generate_questions(resume: str, job_description: str, company: str, difficulty: str) -> list[str]:
    prompt = f"""Role/company: {company or 'General software role'}
Difficulty: {difficulty}
Resume: {resume[:7000]}
Job description: {job_description[:7000]}

Create exactly 9 concise interview questions: 3 technical, 3 behavioural, and 3 company/role-specific. Prefix every item with its category."""
    answer = generate("You are an expert technical-interview coach. Personalise questions only from supplied candidate and role information.", prompt)
    if answer:
        return [line.lstrip("-0123456789. ").strip() for line in answer.splitlines() if line.strip()][:9]
    return [
        "Technical: Explain a project from your resume and its trade-offs.",
        "Technical: How would you test and debug a production issue?",
        "Technical: Which data structure best fits a recently solved problem?",
        "Behavioural: Tell me about yourself.",
        "Behavioural: Describe a challenging project and what you learned.",
        "Behavioural: Describe a time you received difficult feedback.",
        f"Company: Why do you want to work at {company or 'this company'}?",
        "Company: Why are you a good fit for this role?",
        "Company: What would you aim to learn in your first 90 days?",
    ]
