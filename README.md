# PrepPilot AI

PrepPilot AI is a multi-agent interview preparation platform built with Python, Streamlit, Gemini API, and MongoDB Atlas.

## Features

- Resume PDF upload and text extraction
- Job-description analysis and skill matching
- Resume Match Agent: match percentage, strong skills, missing skills, suggestions
- Question Agent: personalised technical, behavioural, and company-focused questions
- Evaluation Agent: answer scoring and targeted feedback
- Structured interview scoring: technical, communication, and confidence dimensions
- Adaptive follow-up questions that respond to the latest answer
- ElevenLabs voice interview mode: spoken interviewer turns and recorded-answer transcription
- Company-aware interview context (Amazon, Google, Microsoft, JP Morgan, NVIDIA)
- ATS keyword-gap analysis and truthful resume-bullet rewriting
- Interactive dashboard, weak-topic trends, and progress chart
- PDF report download
- MongoDB session history; resumes are saved in GridFS

## Architecture

```text
Streamlit UI -> Interview Manager
                    |- Resume/JD Match Agent
                    |- Resume / ATS Agent
                    |- Question Generator Agent (company-aware Gemini)
                    |- Answer Evaluation Agent (structured Gemini output)
                    `- Adaptive Follow-up Agent
                    `- MongoDB / GridFS persistence
```

## Setup

```powershell
cd preppilot_ai
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Set these values in `.env`:

```env
GEMINI_API_KEY=your_key
MONGODB_URI=your_mongodb_atlas_connection_string
MONGODB_DATABASE=preppilot
ELEVENLABS_API_KEY=your_elevenlabs_key
# Optional: a default ElevenLabs voice is used if this is not set.
ELEVENLABS_VOICE_ID=your_voice_id
```

In **Mock interview**, turn on **Voice conversation** to hear interviewer turns and record your answer. ElevenLabs Scribe transcribes the recording before it follows the same evaluation path as a typed answer.

Run the app:

```powershell
streamlit run app.py
```

## MongoDB data model

- GridFS (`fs.files`, `fs.chunks`): uploaded resume PDFs
- `sessions`: resume text, job description, match analysis, questions, readiness score
- `evaluations`: answer, score, and feedback

## Disclaimer

PrepPilot AI provides practice feedback, not a hiring decision or guarantee of interview outcomes.
