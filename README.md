# JD & Resume Analyzer

A fully local, **no API key required** Streamlit app that analyzes a Job Description and Resume using Python NLP techniques. No external AI services, no quotas, no cost.

---

##  Features

- ** JD Key Points** — extracts required skills, soft skills, responsibilities, experience, and education from the job description
- ** ATS Friendliness Check** — checks if your resume passes common ATS (Applicant Tracking System) filters, with a score and fix suggestions
- ** Match Score** — calculates how relevant your resume is to the JD using TF-IDF similarity + skill matching
- ** Skill Gap Analysis** — shows matched skills (green), missing skills (red), strengths, and gaps
- ** File Support** — accepts PDF, DOCX, or plain text paste for both JD and Resume

---

##  How to Run

### Step 1 — Make sure Python is installed
Download from [python.org](https://python.org) if not already installed.
During installation, check  **"Add Python to PATH"**

### Step 2 — Install dependencies
Open your terminal (or VSCode terminal) and run:
```bash
pip install -r requirements.txt
```

### Step 3 — Run the app
```bash
streamlit run app.py
```

The app will automatically open in your browser at `http://localhost:8501`

---

##  Running on VSCode

1. Install [VSCode](https://code.visualstudio.com)
2. Install the **Python extension** from the Extensions panel (`Ctrl+Shift+X`)
3. Open your project folder: `File → Open Folder`
4. Open the terminal: `` Ctrl + ` ``
5. Run:
```bash
pip install -r requirements.txt
streamlit run app.py
```

---

##  Deploying on Streamlit Cloud (Free Hosting)

1. Push your code to a **public GitHub repository**
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
3. Click **New App** → select your repo → set main file as `app.py`
4. Click **Deploy** — your app will be live in ~2 minutes at a public URL

> No API keys or secrets needed since this app runs fully locally.

---

##  File Structure

```
resume-analyser/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

---

##  How It Works (No AI Used)

| Feature | Technique |
|---|---|
| Match Score | TF-IDF vectorization + cosine similarity |
| Skill Extraction | Regex keyword matching against 60+ skill list |
| ATS Check | Pattern matching for common ATS red flags |
| Experience & Education | Regex extraction from raw text |

---

##  Dependencies

| Package | Purpose |
|---|---|
| `streamlit` | Web app UI |
| `PyPDF2` | Read PDF files |
| `python-docx` | Read DOCX files |
| `scikit-learn` | TF-IDF similarity scoring |

---

##  Tips for Best Results

- Paste the **full** job description including responsibilities and requirements
- Use a **text-based PDF** resume (not a scanned image)
- The more detailed your resume, the better the analysis
- DOCX format resumes give the most accurate ATS results

---

##  Common Issues

**`streamlit` not found after install**
→ Restart your terminal and try again, or use `python -m streamlit run app.py`

**PDF shows empty text**
→ Your PDF may be image-based (scanned). Copy-paste the text manually instead.

**Low match score even for a good resume**
→ Try including more keywords from the JD directly in your resume — ATS systems are keyword-driven.
