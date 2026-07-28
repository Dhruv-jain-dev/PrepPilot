from __future__ import annotations

from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def build_report(session: dict) -> bytes:
    """Create a shareable PDF summary for one interview-prep session."""
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, leftMargin=42, rightMargin=42, topMargin=42, bottomMargin=42)
    styles = getSampleStyleSheet()
    match = session.get("match", {})
    story = [Paragraph("PrepPilot AI - Interview Preparation Report", styles["Title"]), Spacer(1, 16)]
    story += [Paragraph(f"<b>Target role:</b> {session.get('role', 'Not specified')}", styles["BodyText"])]
    story += [Paragraph(f"<b>Resume match:</b> {match.get('score', 0)}%", styles["BodyText"]), Spacer(1, 10)]
    for heading, values in (("Strong skills", match.get("strong_skills", [])), ("Skills to develop", match.get("missing_skills", []))):
        story += [Paragraph(f"<b>{heading}</b>: {', '.join(values) or 'None identified'}", styles["BodyText"]), Spacer(1, 8)]
    questions = session.get("questions", [])
    if questions:
        story += [Paragraph("<b>Suggested interview questions</b>", styles["Heading2"])]
        story += [Paragraph(question.replace("\n", "<br/>"), styles["BodyText"]) for question in questions]
    doc.build(story)
    return output.getvalue()
