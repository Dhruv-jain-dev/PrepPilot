from __future__ import annotations

from .company_profiles import company_interview_focus
from .gemini import generate


def generate_questions(resume: str, job_description: str, company: str, difficulty: str) -> list[str]:
    prompt = f"""Role/company: {company or 'General software role'}
Company interview focus: {company_interview_focus(company)}
Difficulty: {difficulty}
Resume: {resume[:7000]}
Job description: {job_description[:7000]}

Create exactly 9 concise interview questions: 3 technical, 3 behavioural, and 3 company/role-specific. Prefix every item with its category."""
    answer = generate("You are an expert technical-interview coach. Personalise questions only from supplied candidate and role information.", prompt)
    if answer:
        return [line.lstrip("-0123456789. ").strip() for line in answer.splitlines() if line.strip()][:9]
    return [
        "Explain a project from your resume and its trade-offs.",
        "How would you test and debug a production issue?",
        "Which data structure best fits a recently solved problem?",
        "Tell me about yourself.",
        "Describe a challenging project and what you learned.",
        "Describe a time you received difficult feedback.",
        f"Why do you want to work at {company or 'this company'}?",
        "Why are you a good fit for this role?",
        "What would you aim to learn in your first 90 days?",
    ]


def generate_adaptive_question(question: str, answer: str, evaluation: dict, company: str, difficulty: str) -> str:
    """Generate the interviewer’s next turn, responding to the candidate's performance."""
    score = float(evaluation.get("score", 5))
    target = "Hard" if score >= 8 else "Easy" if score <= 4 else difficulty
    direction = (
        "The candidate is struggling. Ask a fresh, simpler foundational question; do not repeat the prior question."
        if score <= 4
        else "The candidate performed strongly. Ask a more challenging question or probe the trade-offs."
        if score >= 8
        else "Ask one focused follow-up that checks a gap or requests a concrete example."
    )
    prompt = f"""Company: {company or 'General'}
Company focus: {company_interview_focus(company)}
Current difficulty: {difficulty}; next difficulty: {target}
Previous question: {question}
Candidate answer: {answer[:3500]}
Evaluation: {evaluation.get('feedback', '')[:2500]}
Interview direction: {direction}

Ask exactly one concise, natural next interview question. It must stay grounded in the supplied candidate and role information. Return only the question; do not add labels, feedback, or commentary."""
    generated = generate("You are an adaptive technical interviewer.", prompt)
    if generated:
        return generated.splitlines()[0].strip().lstrip("- ")
    if score <= 4:
        return "Let's take a simpler example: what is the difference between a list and a dictionary, and when would you use each?"
    if score >= 8:
        return "How would your approach change at ten times the scale, and what trade-offs would you make?"
    return "Can you give one concrete example that demonstrates your approach?"
