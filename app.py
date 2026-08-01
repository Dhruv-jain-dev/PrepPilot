from __future__ import annotations

from collections import Counter
import re

import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

from agents.evaluator_agent import evaluate_answer
from agents.manager import build_interview_plan
from agents.question_agent import generate_adaptive_question
from agents.resume_agent import ats_summary, rewrite_resume_bullet
from database.mongodb import InMemoryRepository, MongoRepository
from utils.pdf_reader import extract_pdf_text
from utils.report import build_report
from utils.elevenlabs_audio import ElevenLabsAudioError, synthesize_speech, transcribe_audio

load_dotenv()
st.set_page_config(page_title="PrepPilot AI", page_icon="🎯", layout="wide")


def apply_theme() -> None:
    """Apply a compact, interview-focused visual system to the Streamlit app."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
        /* Senthora.ai-matched visual system: near-black plum background, violet glow, pill controls. */
        :root {
            --bg: #110F14; --bg-deep: #0B0A0E; --panel: #1E1C26; --panel-soft: #17161C;
            --text: #EAEAF0; --muted: #A49DB5;
            --violet: #9A8AFB; --violet-bright: #BCA9FF; --violet-deep: #6A4EE8; --violet-dim: rgba(154,138,251,.14);
            --pink: #CC3366; --line: rgba(234,234,240,.10);
        }
        html, body, .stApp, [class*="css"] { font-family: 'Plus Jakarta Sans', -apple-system, 'Segoe UI', sans-serif; }
        .stApp {
            background:
                radial-gradient(110% 60% at 50% -12%, rgba(154, 138, 251, 0.16), transparent 60%),
                radial-gradient(55% 55% at -8% 28%, rgba(154, 138, 251, 0.10), transparent 55%),
                radial-gradient(55% 55% at 108% 55%, rgba(154, 138, 251, 0.08), transparent 55%),
                radial-gradient(70% 45% at 50% 108%, rgba(204, 51, 102, 0.06), transparent 60%),
                var(--bg);
            color: var(--text);
        }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, var(--panel) 0%, var(--bg-deep) 100%);
            border-right: 1px solid var(--line);
        }
        [data-testid="stSidebar"] [data-testid="stSidebarContent"] { padding-top: 1rem; }
        h1, h2, h3, [data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3 {
            color: var(--text); font-weight: 700; letter-spacing: -0.03em;
        }
        [data-testid="stMarkdownContainer"] p, [data-testid="stCaptionContainer"] { color: var(--muted); }
        [data-testid="stMetric"] {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 20px;
            padding: 1.1rem 1.2rem;
        }
        [data-testid="stMetricLabel"] { color: var(--muted); font-size: 0.76rem; letter-spacing: 0.08em; text-transform: uppercase; }
        [data-testid="stMetricValue"] { color: var(--violet-bright); font-weight: 700; }
        [data-testid="stTabs"] [role="tablist"] { gap: 0.4rem; border-bottom: 1px solid var(--line); }
        [data-testid="stTabs"] [role="tab"] {
            background: transparent; color: var(--muted); border: 1px solid transparent;
            border-radius: 100px; padding: 0.6rem 1.1rem; font-weight: 600;
        }
        [data-testid="stTabs"] [role="tab"][aria-selected="true"] { color: var(--text); background: var(--violet-dim); border-color: rgba(154,138,251,.35); }
        [data-testid="stChatMessage"] {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 18px;
            margin: 0.55rem 0;
            padding: 0.25rem 0.6rem;
        }
        [data-testid="stChatInput"] {
            background: var(--panel-soft);
            border: 1px solid rgba(154, 138, 251, 0.4);
            border-radius: 100px;
        }
        .block-container { max-width: 1240px; padding-top: 1.55rem; padding-bottom: 4rem; }
        [data-testid="stFileUploader"], [data-testid="stTextInput"], [data-testid="stTextArea"], [data-testid="stSelectbox"] {
            border-radius: 14px;
        }
        [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea, [data-testid="stSelectbox"] div[data-baseweb="select"] > div, [data-testid="stFileUploader"] section {
            background: rgba(255, 255, 255, 0.03) !important; color: var(--text) !important; border-color: var(--line) !important; border-radius: 14px !important;
        }
        [data-testid="stTextInput"] label, [data-testid="stTextArea"] label, [data-testid="stSelectbox"] label, [data-testid="stFileUploader"] label, [data-testid="stSlider"] label { color: #cfc9dc !important; font-size: 0.82rem !important; }
        [data-testid="stTextInput"] input::placeholder, [data-testid="stTextArea"] textarea::placeholder { color: #6f6a80; }
        [data-testid="stButton"] button, [data-testid="stDownloadButton"] button {
            background: transparent; color: var(--text); border: 1px solid rgba(154, 138, 251, 0.4);
            border-radius: 100px; font-weight: 600; min-height: 2.7rem;
            transition: transform 0.18s ease, background 0.18s ease, border-color 0.18s ease;
        }
        [data-testid="stButton"] button:hover, [data-testid="stDownloadButton"] button:hover {
            background: var(--violet-dim); border-color: var(--violet-bright); transform: translateY(-1px);
        }
        [data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"], [data-testid="stButton"] button[kind="primary"] {
            background: linear-gradient(145deg, #BCA9FF 0%, #8F7BF7 45%, #6A4EE8 100%) !important;
            color: #110F14 !important; border: 0 !important; font-weight: 700 !important;
        }
        [data-testid="stExpander"] {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 16px;
        }
        .hero-copy { padding: 3rem 0 2rem; max-width: 53rem; }
        .hero-kicker { color: var(--violet-bright); font-size: 0.76rem; font-weight: 700; letter-spacing: 0.16em; text-transform: uppercase; margin-bottom: 0.5rem; }
        .hero-title { color: var(--text); font-size: clamp(2.6rem, 6vw, 5rem); font-weight: 800; line-height: 0.98; letter-spacing: -0.04em; margin: 0; }
        .hero-title .gradient { background: linear-gradient(120deg, var(--violet-bright), var(--violet) 50%, var(--pink)); -webkit-background-clip: text; background-clip: text; color: transparent; }
        .hero-subtitle { color: var(--muted); max-width: 39rem; font-size: 1.05rem; line-height: 1.65; margin-top: 0.85rem; }
        .hero-pills { display: flex; flex-wrap: wrap; gap: 0.55rem; margin-top: 1.25rem; }
        .hero-pill { color: var(--text); background: var(--panel); border: 1px solid var(--line); border-radius: 100px; padding: 0.4rem 0.85rem; font-size: 0.8rem; }
        .info-card {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 20px; padding: 1.2rem 1.25rem; margin: 0.7rem 0;
        }
        .info-card h4 { color: var(--violet-bright); margin: 0 0 0.35rem; font-size: 1rem; font-weight: 700; }
        .info-card p { color: var(--muted); margin: 0; line-height: 1.5; font-size: 0.9rem; }
        .interview-status { color: var(--violet-bright); font-size: 0.85rem; font-weight: 600; letter-spacing: 0.03em; text-transform: uppercase; }
        .auth-shell { max-width: 1180px; margin: 0 auto; padding: 2.4rem 0 1.5rem; }
        .auth-card {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 24px; padding: 1.6rem;
            box-shadow: 0 2rem 6rem rgba(0, 0, 0, 0.35);
        }
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--panel) !important; border-color: var(--line) !important;
            border-radius: 24px !important; box-shadow: 0 2rem 6rem rgba(0, 0, 0, 0.35);
        }
        .stMarkdown p.auth-heading { color: var(--text); font-size: 1.6rem !important; font-weight: 700; letter-spacing: -0.03em; margin: 0; }
        .auth-copy { color: var(--muted); font-size: 0.92rem; line-height: 1.55; margin: 0.45rem 0 1.2rem; }
        button[kind="primary"], button[kind="primaryFormSubmit"], [data-testid="stBaseButton-primaryFormSubmit"] {
            background: linear-gradient(145deg, #BCA9FF 0%, #8F7BF7 45%, #6A4EE8 100%) !important;
            border: none !important; color: #110F14 !important; min-height: 2.8rem;
        }
        .landing-footnote { color: #726d80; font-size: 0.76rem; margin-top: 1rem; }
        .nav-rule { border-top: 1px solid var(--line); margin-top: 0.8rem; }
        .top-nav { display: flex; align-items: center; justify-content: flex-start; gap: clamp(0.7rem, 1.9vw, 1.75rem); padding-top: 0.35rem; color: var(--muted); font-size: 0.86rem; }
        .top-nav span { white-space: nowrap; }
        .top-nav span:first-child { color: var(--text); }
        .profile-chip { margin-left: auto; width: fit-content; color: var(--text); font-size: 0.82rem; background: var(--panel); border: 1px solid var(--line); border-radius: 100px; padding: 0.42rem 0.85rem; }
        .landing-eyebrow { color: var(--violet-bright); font-size: 0.72rem; font-weight: 700; letter-spacing: 0.17em; text-transform: uppercase; margin-bottom: 1.1rem; }
        .stMarkdown p.landing-title { max-width: 12ch; color: var(--text); font-size: clamp(3rem, 5.6vw, 5.3rem) !important; font-weight: 800; letter-spacing: -0.04em; line-height: 0.92 !important; margin: 0; }
        .landing-title em { font-style: normal; font-weight: 800; background: linear-gradient(120deg, var(--violet-bright), var(--violet) 50%, var(--pink)); -webkit-background-clip: text; background-clip: text; color: transparent; }
        .landing-copy { max-width: 29rem; color: var(--muted); font-size: 1.04rem; line-height: 1.7; margin: 1.55rem 0 1.8rem; }
        .landing-proof { display: flex; align-items: center; gap: 0.75rem; color: var(--text); font-size: 0.82rem; }
        .landing-proof::before { content: ''; height: 1.65rem; width: 1.65rem; border-radius: 50%; background: linear-gradient(145deg, var(--violet-bright), var(--violet-deep)); box-shadow: 0 0 0 5px var(--violet-dim); }
        @media (max-width: 740px) {
            .auth-shell { padding-top: 1rem; }
            .stMarkdown p.landing-title { font-size: clamp(3rem, 17vw, 4.8rem); }
            .top-nav { justify-content: center; gap: 0.65rem; font-size: 0.7rem; }
        }
        /* Nav bar */
        .nav-bar { display: flex; align-items: center; justify-content: center; gap: clamp(1rem, 3vw, 2.5rem); }
        .nav-links { display: flex; align-items: center; gap: clamp(0.6rem, 1.8vw, 1.6rem); background: var(--panel); border: 1px solid var(--line); border-radius: 100px; padding: 0.55rem 1.4rem; }
        .nav-links span { color: var(--muted); font-size: 0.85rem; font-weight: 600; white-space: nowrap; }
        .nav-links span:first-child { color: var(--text); }
        /* Centered hero (landing + app) */
        .hero-center { text-align: center; max-width: 46rem; margin: 0 auto; padding: clamp(2.5rem, 6vw, 4.5rem) 0 2rem; }
        .hero-center .hero-kicker { justify-content: center; }
        .hero-center .hero-pills, .hero-center .landing-proof { justify-content: center; }
        .hero-badge { display: inline-flex; align-items: center; gap: 0.5rem; color: var(--violet-bright); background: var(--violet-dim); border: 1px solid rgba(154,138,251,.3); border-radius: 100px; padding: 0.35rem 0.9rem 0.35rem 0.5rem; font-size: 0.78rem; font-weight: 600; margin-bottom: 1.1rem; }
        .hero-badge .dot { width: 0.5rem; height: 0.5rem; border-radius: 50%; background: var(--pink); box-shadow: 0 0 10px var(--pink); }
        /* Feature strip */
        .feature-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: 1.5rem; }
        .feature-card { background: var(--panel); border: 1px solid var(--line); border-radius: 20px; padding: 1.4rem 1.3rem; }
        .feature-card .feature-icon { width: 2.6rem; height: 2.6rem; border-radius: 12px; display: grid; place-items: center; font-size: 1.25rem; margin-bottom: 0.9rem; background: linear-gradient(145deg, var(--violet-bright), var(--violet-deep)); box-shadow: 0 8px 24px rgba(154,138,251,.25); }
        .feature-card h4 { color: var(--text); margin: 0 0 0.35rem; font-size: 0.98rem; font-weight: 700; }
        .feature-card p { color: var(--muted); margin: 0; font-size: 0.86rem; line-height: 1.5; }
        .step-card { display: flex; gap: 0.9rem; align-items: flex-start; }
        .step-number { flex-shrink: 0; width: 2.1rem; height: 2.1rem; border-radius: 50%; display: grid; place-items: center; font-weight: 700; font-size: 0.9rem; color: #110F14; background: linear-gradient(145deg, var(--violet-bright), var(--violet-deep)); }
        @media (max-width: 900px) {
            .feature-grid { grid-template-columns: 1fr; }
            .nav-links span { display: none; }
            .nav-links span:first-child { display: inline; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource
def repository() -> tuple[MongoRepository | InMemoryRepository, str | None]:
    try:
        return MongoRepository(), None
    except Exception:
        return InMemoryRepository(), (
            "MongoDB Atlas is unreachable, so PrepPilot is running in temporary local mode. "
            "Your interviews will work, but saved sessions will be lost when the app restarts."
        )


def metric_card(label: str, value: str, help_text: str = "") -> None:
    st.metric(label, value, help=help_text)


def render_authentication(repo: MongoRepository | InMemoryRepository, database_notice: str | None) -> None:
    """Render the entry screen and store a signed-in user in Streamlit session state."""
    st.markdown('<div class="auth-shell">', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="nav-bar">
            <div class="nav-links">
                <span>PrepPilot</span>
                <span>How it works</span>
                <span>Features</span>
                <span>Pricing</span>
                <span>FAQ</span>
            </div>
        </div>
        <div class="hero-center">
            <div class="hero-badge"><span class="dot"></span>Only in PrepPilot &mdash; adaptive difficulty</div>
            <p class="landing-title" style="margin:0 auto;">Make your next <em>yes</em> inevitable.</p>
            <p class="hero-subtitle" style="margin:1.1rem auto 0;">
                A calmer, smarter way to prepare. Build a plan from your real experience, rehearse the
                conversation with an AI interviewer, and improve with feedback that meets you where you are.
            </p>
            <div class="landing-proof">Tailored practice for the opportunity in front of you.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _, account, _ = st.columns([0.62, 1.0, 0.62])
    with account:
        with st.container(border=True):
            st.markdown('<p class="auth-heading">Start your practice</p>', unsafe_allow_html=True)
            st.markdown('<p class="auth-copy">Create an account to save plans, feedback, and progress.</p>', unsafe_allow_html=True)
            sign_up, sign_in = st.tabs(["Create account", "Sign in"])
            with sign_up:
                with st.form("sign_up_form"):
                    name = st.text_input("Full name", placeholder="Alex Morgan")
                    email = st.text_input("Email address", placeholder="alex@example.com")
                    password = st.text_input("Password", type="password", help="Use at least 8 characters.")
                    confirm_password = st.text_input("Confirm password", type="password")
                    submitted = st.form_submit_button("Create my account", type="primary", use_container_width=True)
                if submitted:
                    if not name.strip():
                        st.error("Enter your name to continue.")
                    elif not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip()):
                        st.error("Enter a valid email address.")
                    elif len(password) < 8:
                        st.error("Your password must contain at least 8 characters.")
                    elif password != confirm_password:
                        st.error("The passwords do not match.")
                    else:
                        try:
                            st.session_state.user = repo.create_user(name, email, password)
                            st.rerun()
                        except ValueError as exc:
                            st.error(str(exc))
            with sign_in:
                with st.form("sign_in_form"):
                    email = st.text_input("Email address", key="sign_in_email", placeholder="alex@example.com")
                    password = st.text_input("Password", key="sign_in_password", type="password")
                    submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)
                if submitted:
                    user = repo.authenticate_user(email, password)
                    if not user:
                        st.error("We couldn't find an account with those credentials.")
                    else:
                        st.session_state.user = user
                        st.rerun()
            if database_notice:
                st.info("You can still explore PrepPilot in local mode, but accounts and sessions will reset when the app restarts.")
        st.markdown('<p class="landing-footnote" style="text-align:center;">Your practice is private, personal, and built around your goals.</p>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="feature-grid" style="margin-top:2.5rem;">
            <div class="feature-card">
                <div class="feature-icon">&#128196;</div>
                <h4>Match your profile</h4>
                <p>Compare your resume to the role and surface the highest-value skill gaps automatically.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">&#127908;</div>
                <h4>Practise naturally</h4>
                <p>Chat or speak with an interviewer that adapts difficulty after every single answer.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">&#128200;</div>
                <h4>Improve deliberately</h4>
                <p>Track strengths, weak topics, and practical next steps in one focused dashboard.</p>
            </div>
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def interview_state(session_id: str, questions: list[str]) -> dict:
    """Create or retrieve the live, conversational state for one mock interview."""
    key = f"mock_interview_{session_id}"
    if key not in st.session_state:
        opening_question = questions[0] if questions else "Tell me about yourself and the role you are seeking."
        st.session_state[key] = {
            "current_question": opening_question,
            "turn": 1,
            "messages": [
                {
                    "role": "assistant",
                    "content": (
                        "Hi, I'm your PrepPilot interviewer. I'll adapt the interview to your answers—"
                        "asking for depth when you do well and simplifying the next question if you get stuck.\n\n"
                        f"**Question 1:** {opening_question}"
                    ),
                }
            ],
        }
    return st.session_state[key]


def interviewer_intro(session: dict) -> str:
    role = session.get("role") or "the target role"
    company = session.get("company") or "your target company"
    required_skills = session.get("match", {}).get("required_skills", [])[:4]
    focus = f" We'll focus on {', '.join(required_skills)}." if required_skills else ""
    return (
        f"Hello! I'm PrepPilot, your AI interviewer for the **{role}** opportunity at **{company}**."
        f" I've reviewed the job description and will tailor the conversation to its responsibilities and requirements.{focus}\n\n"
        "When you're ready, say hello and we'll begin."
    )


def is_greeting(message: str) -> bool:
    cleaned = re.sub(r"[^a-z ]", "", message.lower()).strip()
    return bool(re.fullmatch(r"(hi|hello|hey|good morning|good afternoon|good evening)( there)?", cleaned))


def chatbot_interview_state(session_id: str, session: dict) -> dict:
    key = f"mock_interview_{session_id}"
    if key not in st.session_state:
        questions = session.get("questions", [])
        st.session_state[key] = {
            "current_question": questions[0] if questions else "Tell me about yourself and the role you are seeking.",
            "turn": 1,
            "started": False,
            "messages": [{"role": "assistant", "content": interviewer_intro(session)}],
        }
    return st.session_state[key]


def interviewer_audio_text(message: str) -> str:
    """Strip Markdown markers before sending an interviewer turn to TTS."""
    return re.sub(r"[*_`#]", "", message).replace("\n", " ")


def speak_interviewer_message(message: dict) -> bytes | None:
    """Generate audio once per message so Streamlit reruns do not bill again."""
    if "audio" not in message:
        try:
            message["audio"] = synthesize_speech(interviewer_audio_text(message["content"]))
        except ElevenLabsAudioError as exc:
            st.warning(str(exc))
            message["audio"] = b""
    return message["audio"] or None


def process_interview_answer(repo: MongoRepository, session_id: str, session: dict, difficulty: str, state: dict, answer: str) -> None:
    """Evaluate typed and transcribed answers through the same workflow."""
    state["messages"].append({"role": "user", "content": answer})
    if not state["started"]:
        state["started"] = True
        greeting = "Hello! Great to meet you." if is_greeting(answer) else "Great, let's get started."
        state["messages"].append({"role": "assistant", "content": f"{greeting}\n\n**Question 1:** {state['current_question']}"})
        st.rerun()
    if is_greeting(answer):
        state["messages"].append({"role": "assistant", "content": f"Hello again! Take your time—please answer **Question {state['turn']}** when you're ready."})
        st.rerun()
    question = state["current_question"]
    with st.spinner("Your interviewer is thinking..."):
        result = evaluate_answer(question, answer)
        repo.add_evaluation(session_id, question, answer, result)
        next_question = generate_adaptive_question(question, answer, result, session.get("company", "General"), difficulty)
    state["messages"].append({"role": "assistant", "content": (
        f"{result['feedback']}\n\n**What you did well:** {', '.join(result['strengths']) or 'Not specified'}\n\n"
        f"**Try next:** {', '.join(result['improvements']) or 'Use a concrete example and explain your reasoning.'}\n\n"
        f"**Question {state['turn'] + 1}:** {next_question}"
    )})
    state["turn"] += 1
    state["current_question"] = next_question
    repo.add_question(session_id, next_question)
    st.rerun()


def render_mock_interview(repo: MongoRepository, session_id: str, session: dict, difficulty: str) -> None:
    state_key = f"mock_interview_{session_id}"
    state = chatbot_interview_state(session_id, session)
    header, reset = st.columns([5, 1])
    with header:
        st.subheader("Live mock interview")
        st.markdown('<div class="interview-status">Adaptive interviewer online</div>', unsafe_allow_html=True)
    with reset:
        if st.button("Restart", use_container_width=True):
            del st.session_state[state_key]
            st.rerun()

    voice_column, record_column = st.columns(2)
    with voice_column:
        voice_mode = st.toggle(
            "Voice conversation",
            help="Hear each interviewer turn spoken aloud.",
            key=f"voice_mode_{session_id}",
        )
    with record_column:
        recording_mode = st.toggle(
            "Record answer with voice",
            help="Record an answer and convert it to text with ElevenLabs.",
            key=f"recording_mode_{session_id}",
        )
    if recording_mode:
        st.caption("Recorded answers are sent to ElevenLabs for transcription before evaluation.")

    for message in state["messages"]:
        with st.chat_message(message["role"], avatar="🤖" if message["role"] == "assistant" else "🧑"):
            st.markdown(message["content"])
            if voice_mode and message["role"] == "assistant":
                audio = speak_interviewer_message(message)
                if audio:
                    st.audio(audio, format="audio/mp3")

    recorded_answer = ""
    if recording_mode:
        recording = st.audio_input("Record your answer", key=f"recording_{session_id}_{state['turn']}")
        if st.button("Transcribe and send recorded answer", type="primary", use_container_width=True):
            if recording is None:
                st.warning("Record an answer first.")
            else:
                try:
                    with st.spinner("Transcribing your answer..."):
                        recorded_answer = transcribe_audio(recording.getvalue(), recording.name or "answer.wav")
                    st.toast("Answer transcribed and sent to the interviewer.")
                except ElevenLabsAudioError as exc:
                    st.error(str(exc))

    answer = recorded_answer or st.chat_input("Type an answer to PrepPilot...")
    if not answer:
        return

    state["messages"].append({"role": "user", "content": answer})
    if not state["started"]:
        state["started"] = True
        greeting = "Hello! Great to meet you." if is_greeting(answer) else "Great, let's get started."
        state["messages"].append(
            {
                "role": "assistant",
                "content": f"{greeting}\n\n**Question 1:** {state['current_question']}",
            }
        )
        st.rerun()

    if is_greeting(answer):
        state["messages"].append(
            {
                "role": "assistant",
                "content": f"Hello again! Take your time—please answer **Question {state['turn']}** when you're ready.",
            }
        )
        st.rerun()

    question = state["current_question"]
    with st.spinner("Your interviewer is thinking..."):
        result = evaluate_answer(question, answer)
        repo.add_evaluation(session_id, question, answer, result)
        next_question = generate_adaptive_question(
            question,
            answer,
            result,
            session.get("company", "General"),
            difficulty,
        )

    state["messages"].append(
        {
            "role": "assistant",
            "content": (
                f"{result['feedback']}\n\n"
                f"**What you did well:** {', '.join(result['strengths']) or 'Not specified'}\n\n"
                f"**Try next:** {', '.join(result['improvements']) or 'Use a concrete example and explain your reasoning.'}\n\n"
                f"**Question {state['turn'] + 1}:** {next_question}"
            ),
        }
    )
    state["turn"] += 1
    state["current_question"] = next_question
    repo.add_question(session_id, next_question)
    st.rerun()


def main() -> None:
    apply_theme()
    st.markdown("<style>h1 { display: none; }</style>", unsafe_allow_html=True)
    repo, database_notice = repository()
    if "user" not in st.session_state:
        render_authentication(repo, database_notice)
        return

    user = st.session_state.user
    _, nav_profile = st.columns([3.2, 1], vertical_alignment="center")
    with nav_profile:
        st.markdown(f'<div class="profile-chip">&#9679;&nbsp; {user["name"]}</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="nav-bar" style="margin-top:-2.3rem;">
            <div class="nav-links">
                <span>PrepPilot</span>
                <span>How it works</span>
                <span>Practice</span>
                <span>Insights</span>
                <span>History</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="hero-center">
            <div class="hero-badge"><span class="dot"></span>Your AI interview room</div>
            <div class="hero-title">Prepare for<br><span class="gradient">your next yes.</span></div>
            <div class="hero-subtitle" style="margin-left:auto; margin-right:auto;">
                Speak naturally, get thoughtful feedback, and walk into every interview ready to make your case.
            </div>
            <div class="hero-pills" style="justify-content:center;">
                <span class="hero-pill">Resume intelligence</span>
                <span class="hero-pill">Adaptive coaching</span>
                <span class="hero-pill">Progress insights</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.title("🎯 PrepPilot AI")
    if database_notice:
        st.warning(database_notice, icon="⚠️")

    with st.sidebar:
        st.image("assets/preppilot-wordmark.png", width=190)
        st.caption(f"Signed in as **{user['name']}**")
        if st.button("Sign out", use_container_width=True):
            st.session_state.pop("user", None)
            st.session_state.pop("session_id", None)
            st.rerun()
        st.divider()
        st.header("Interview setup")
        resume = st.file_uploader("Resume (PDF)", type=["pdf"])
        role = st.text_input("Target role", placeholder="Software Engineer Intern")
        company = st.selectbox("Company", ["General", "Google", "Microsoft", "Amazon", "JP Morgan", "NVIDIA", "Other"])
        difficulty = st.select_slider("Difficulty", options=["Easy", "Medium", "Hard"], value="Medium")
        st.divider()
        st.caption("All uploaded data, sessions, and answer evaluations are stored in MongoDB. Resume PDFs are stored through GridFS.")

    tab_setup, tab_dashboard, tab_mock, tab_history = st.tabs(["Create plan", "Dashboard", "Mock interview", "History"])
    with tab_setup:
        st.subheader("Create your interview plan")
        st.caption("Upload your resume, describe the role, then let PrepPilot map the interview around your real skill gaps.")
        plan_form, plan_preview = st.columns([1.35, 0.85], vertical_alignment="top")
        with plan_form:
            job_description = st.text_area(
                "Job description",
                height=435,
                placeholder="Paste the role responsibilities, requirements, and skills here...",
            )
        with plan_preview:
            st.markdown(
                """
                <div class="info-card step-card">
                    <div class="step-number">1</div>
                    <div><h4>Match your profile</h4><p>Compare your resume to the role and surface the highest-value skill gaps.</p></div>
                </div>
                <div class="info-card step-card">
                    <div class="step-number">2</div>
                    <div><h4>Practise naturally</h4><p>Chat with an interviewer that adjusts difficulty after every answer.</p></div>
                </div>
                <div class="info-card step-card">
                    <div class="step-number">3</div>
                    <div><h4>Improve deliberately</h4><p>Track strengths, weak topics, and practical next steps in one dashboard.</p></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        if st.button("Analyse resume and create interview plan", type="primary", use_container_width=True):
            if not resume or not job_description.strip():
                st.warning("Upload a resume PDF and paste a job description first.")
            else:
                try:
                    with st.spinner("Resume, matching, and question agents are working..."):
                        resume_bytes = resume.getvalue()
                        resume_text = extract_pdf_text(resume_bytes)
                        plan = build_interview_plan(resume_text, job_description, company, difficulty)
                        session_id = repo.create_session(
                            resume.name, resume_bytes, resume_text, job_description, role, company, plan, user["id"]
                        )
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
            with c1:
                metric_card("Resume match", f"{match['score']}%")
            with c2:
                metric_card("Interview readiness", f"{session['readiness']}%")
            with c3:
                metric_card("Questions prepared", str(len(session["questions"])))
            st.subheader("Skills analysis")
            chart_data = {
                "Skill": match["strong_skills"] + match["missing_skills"],
                "Status": ["Strong"] * len(match["strong_skills"]) + ["Develop"] * len(match["missing_skills"]),
            }
            if chart_data["Skill"]:
                st.plotly_chart(px.bar(chart_data, x="Skill", color="Status", title="Resume vs job requirements"), use_container_width=True)
            st.write("**Strong skills:**", ", ".join(match["strong_skills"]) or "None identified")
            st.write("**Skills to develop:**", ", ".join(match["missing_skills"]) or "None identified")
            ats = ats_summary(match)
            st.subheader("ATS keyword gap analysis")
            st.caption(f"Keyword coverage: {ats['keyword_coverage']}%. Add keywords only where your experience genuinely supports them.")
            st.write("**Priority keywords:**", ", ".join(ats["priority_keywords"]) or "No gaps identified")
            if match["suggestions"]:
                st.write("**Recommended next steps:**")
                for suggestion in match["suggestions"]:
                    st.write(f"- {suggestion}")
            evaluations = repo.evaluations(session_id)
            if evaluations:
                latest = evaluations[0]
                weak_topics = Counter(topic for evaluation in evaluations for topic in evaluation.get("weak_topics", []))
                dimension_data = {
                    "Dimension": ["Technical", "Communication", "Confidence"],
                    "Score": [
                        latest.get("technical_score", latest["score"]),
                        latest.get("communication_score", latest["score"]),
                        latest.get("confidence_score", latest["score"]),
                    ],
                }
                left, right = st.columns(2)
                with left:
                    st.plotly_chart(px.bar(dimension_data, x="Dimension", y="Score", range_y=[0, 10], title="Latest interview dimensions"), use_container_width=True)
                with right:
                    st.write("**Most common weak topics:**", ", ".join(topic for topic, _ in weak_topics.most_common(5)) or "Complete a practice answer to identify gaps.")
                    average = sum(item["score"] for item in evaluations) / len(evaluations)
                    st.caption(f"Practice attempts: {len(evaluations)} · Average score: {average:.1f}/10")
            st.download_button("Download PDF report", build_report(session), "preppilot-report.pdf", "application/pdf")
            st.divider()
            st.subheader("ATS bullet rewriter")
            bullet = st.text_input(
                "Paste one existing resume bullet",
                placeholder="Built a Streamlit app for interview preparation",
                key="ats_bullet",
            )
            if st.button("Rewrite truthfully for ATS", key="rewrite_ats"):
                if not bullet.strip():
                    st.warning("Paste a resume bullet first.")
                else:
                    rewritten = rewrite_resume_bullet(bullet, session.get("role", ""), session["match"].get("missing_skills", []))
                    st.code(rewritten, language=None)

    with tab_mock:
        if not session:
            st.info("Create an interview plan first.")
        else:
            render_mock_interview(repo, session_id, session, difficulty)

    with tab_history:
        sessions = repo.recent_sessions(user["id"])
        if not sessions:
            st.info("No saved sessions yet.")
        for saved in sessions:
            label = f"{saved.get('role') or 'Interview plan'} - {saved.get('company', 'General')} ({saved['match']['score']}%)"
            if st.button(label, key=str(saved["_id"])):
                st.session_state.session_id = str(saved["_id"])
                st.rerun()


if __name__ == "__main__":
    main()
