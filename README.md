# PrepPilot AI

PrepPilot AI is a multi-agent interview preparation platform built with Python, Streamlit, Gemini API, and MongoDB Atlas.

## Features

- Resume PDF upload and text extraction
- Job-description analysis and skill matching
- Resume Match Agent: match percentage, strong skills, missing skills, suggestions
- Question Agent: personalised technical, behavioural, and company-focused questions
- Evaluation Agent: answer scoring and targeted feedback
- Interactive dashboard and progress chart
- PDF report download
- MongoDB session history; resumes are saved in GridFS

## Architecture

```text
Streamlit UI -> Interview Manager
                    |- Resume/JD Match Agent
                    |- Question Generator Agent (Gemini)
                    |- Answer Evaluation Agent (Gemini)
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
```

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
