from __future__ import annotations

import os

import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

from agents.evaluator_agent import evaluate_answer
from agents.manager import build_interview_plan
from database.mongodb import MongoRepository
from utils.pdf_reader import extract_pdf_text
from utils.report import build_report

load_dotenv()
st.set_page_config(page_title="PrepPilot AI", page_icon="🎯", layout="wide")


@st.cache_resource
def repository() -> MongoRepository:
    return MongoRepository()


def metric_card(label: str, value: str, help_text: str = "") -> None:
    st.metric(label, value, help=help_text)


def main() -> None:
    st.title("🎯 PrepPilot AI")
    st.caption("Multi-agent interview preparation powered by Gemini, Streamlit, and MongoDB.")
    try:
        repo = repository()
    except Exception as exc:
        st.error(f"MongoDB connection failed: {exc}")
        st.info("Copy .env.example to .env, add your Gemini API key and MongoDB Atlas URI, then restart Streamlit.")
        st.stop()

    with st.sidebar:
        st.header("Interview setup")
        resume = st.file_uploader("Resume (PDF)", type=["pdf"])
        role = st.text_input("Target role", placeholder="Software Engineer Intern")
        company = st.selectbox("Company", ["General", "Google", "Microsoft", "Amazon", "JP Morgan", "NVIDIA", "Other"])
        difficulty = st.select_slider("Difficulty", options=["Easy", "Medium", "Hard"], value="Medium")
        st.divider()
        st.caption("All uploaded data, sessions, and answer evaluations are stored in MongoDB. Resume PDFs are stored securely through GridFS.")

    tab_setup, tab_dashboard, tab_mock, tab_history = st.tabs(["Create plan", "Dashboard", "Mock interview", "History"])
    with tab_setup:
        job_description = st.text_area("Job description", height=220, placeholder="Paste the role responsibilities, requirements, and skills here…")
        if st.button("Analyse resume and create interview plan", type="primary", use_container_width=True):
            if not resume or not job_description.strip():
                st.warning("Upload a resume PDF and paste a job description first.")
            else:
                try:
                    with st.spinner("Resume, JD, matching, and question agents are working…"):
                        resume_bytes = resume.getvalue()
                        resume_text = extract_pdf_text(resume_bytes)
                        plan = build_interview_plan(resume_text, job_description, company, difficulty)
                        session_id = repo.create_session(resume.name, resume_bytes, resume_text, job_description, role, company, plan)
                        st.session_state.session_id = session_id
                    st.success("Interview plan created and stored in MongoDB.")
                except Exception as exc:
                    st.error(str(exc))

    session_id = st.session_state.get("session_id")
    session = repo.get_session(session_id) if session_id else None
    with tab_dashboard:
        if not session:
            st.info("Create an interview plan to view personalised analytics.")
        else:
            match = session["match"]
            c1, c2, c3 = st.columns(3)
            with c1: metric_card("Resume match", f"{match['score']}%")
            with c2: metric_card("Interview readiness", f"{session['readiness']}%")
            with c3: metric_card("Questions prepared", str(len(session["questions"])))
            st.subheader("Skills analysis")
            chart_data = {"Skill": match["strong_skills"] + match["missing_skills"], "Status": ["Strong"] * len(match["strong_skills"]) + ["Develop"] * len(match["missing_skills"])}
            if chart_data["Skill"]:
                st.plotly_chart(px.bar(chart_data, x="Skill", color="Status", title="Resume vs job requirements"), use_container_width=True)
            st.write("**Strong skills:**", ", ".join(match["strong_skills"]) or "None identified")
            st.write("**Skills to develop:**", ", ".join(match["missing_skills"]) or "None identified")
            if match["suggestions"]:
                st.write("**Recommended next steps:**")
                for suggestion in match["suggestions"]:
                    st.write(f"- {suggestion}")
            st.download_button("Download PDF report", build_report(session), "preppilot-report.pdf", "application/pdf")

    with tab_mock:
        if not session:
            st.info("Create an interview plan first.")
        else:
            question = st.selectbox("Choose a question", session["questions"])
            answer = st.text_area("Your answer", height=180, placeholder="Type your answer and get targeted feedback…")
            if st.button("Evaluate answer", use_container_width=True):
                if not answer.strip():
                    st.warning("Type an answer first.")
                else:
                    with st.spinner("Evaluation agent is reviewing your answer…"):
                        result = evaluate_answer(question, answer)
                        repo.add_evaluation(session_id, question, answer, result)
                    st.metric("Practice score", f"{result['score']}/10")
                    st.markdown(result["feedback"])
            evaluations = repo.evaluations(session_id)
            if evaluations:
                st.subheader("Recent answer scores")
                st.plotly_chart(px.line(list(reversed(evaluations)), y="score", markers=True, title="Practice progress"), use_container_width=True)

    with tab_history:
        sessions = repo.recent_sessions()
        if not sessions:
            st.info("No saved sessions yet.")
        for saved in sessions:
            label = f"{saved.get('role') or 'Interview plan'} - {saved.get('company', 'General')} ({saved['match']['score']}%)"
            if st.button(label, key=str(saved["_id"])):
                st.session_state.session_id = str(saved["_id"])
                st.rerun()


if __name__ == "__main__":
    main()
