# JD & Resume Analyzer

An AI-powered Streamlit app that evaluates a Job Description and Resume using Claude AI.

## Features
- **JD Key Points** — extracts required skills, responsibilities, experience, education
- **ATS Friendliness** — checks if resume is ATS-friendly with a score and suggestions
- **Match Score** — percentage relevance between resume and JD, with matched/missing skills

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Get a free Anthropic API key
Go to https://console.anthropic.com and sign up. New accounts get free credits.

### 3. Run the app
```bash
streamlit run app.py
```

### 4. Use the app
- Enter your Anthropic API key in the sidebar
- Paste or upload the Job Description (PDF, DOCX, or plain text)
- Paste or upload the Resume (PDF, DOCX, or plain text)
- Click **Analyze Now**

## File Structure
```
├── app.py            # Main Streamlit application
├── requirements.txt  # Python dependencies
└── README.md         # This file
```
