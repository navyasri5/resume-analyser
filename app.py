import streamlit as st
import PyPDF2
import docx
import io
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

st.set_page_config(page_title="JD & Resume Analyzer", layout="wide")

st.markdown("""
<style>
    .metric-card {
        background: #f8f9fa; border-radius: 12px;
        padding: 20px; text-align: center; border: 1px solid #e9ecef;
    }
    .metric-big { font-size: 3rem; font-weight: 700; line-height: 1; }
    .metric-label { font-size: 0.85rem; color: #6c757d; margin-top: 6px; }
    .score-green { color: #1D9E75; }
    .score-amber { color: #BA7517; }
    .score-red   { color: #E24B4A; }
    .tag {
        display: inline-block; background: #E1F5EE; color: #085041;
        border-radius: 6px; padding: 3px 10px; font-size: 0.8rem; margin: 3px 2px;
    }
    .tag-missing { background: #FCEBEB; color: #A32D2D; }
    .tag-skill   { background: #E6F1FB; color: #0C447C; }
    .tag-soft    { background: #EEEDFE; color: #3C3489; }
    .ats-badge { display: inline-block; padding: 6px 18px; border-radius: 20px; font-weight: 600; font-size: 1rem; }
    .ats-yes     { background: #E1F5EE; color: #085041; }
    .ats-no      { background: #FCEBEB; color: #A32D2D; }
    .ats-partial { background: #FAEEDA; color: #633806; }
</style>
""", unsafe_allow_html=True)

# ── Common tech & soft skill keywords ────────────────────────────────────────
TECH_SKILLS = [
    "python","java","javascript","typescript","sql","nosql","react","angular","vue",
    "node","django","flask","fastapi","spring","docker","kubernetes","aws","azure","gcp",
    "machine learning","deep learning","nlp","tensorflow","pytorch","scikit-learn",
    "pandas","numpy","power bi","tableau","excel","r","scala","spark","hadoop",
    "mongodb","postgresql","mysql","redis","kafka","airflow","dbt","llm","generative ai",
    "prompt engineering","langchain","openai","claude","gemini","chatgpt",
    "rest api","graphql","microservices","ci/cd","git","agile","scrum","jira",
    "salesforce","hubspot","zoho","ats","crm","zapier","notion","airtable",
    "recruiting","sourcing","talent acquisition","boolean search","linkedin recruiter",
    "business development","lead generation","cold outreach","crm management",
    "workflow automation","process improvement","sop","kpi","data analysis",
    "communication","stakeholder management","project management","product management"
]

SOFT_SKILLS = [
    "communication","leadership","teamwork","problem solving","critical thinking",
    "adaptability","time management","creativity","collaboration","analytical",
    "attention to detail","interpersonal","organized","self-motivated","proactive",
    "strategic","innovative","detail-oriented","multitasking","presentation"
]

ATS_BAD_PATTERNS = [
    (r"(header|footer)", "Headers/footers may be ignored by ATS parsers"),
    (r"table", "Tables can confuse ATS systems"),
    (r"\.(jpg|jpeg|png|gif)", "Images/logos are invisible to ATS"),
    (r"[^\x00-\x7F]", "Special/non-ASCII characters may cause parsing issues"),
]

ATS_GOOD_PATTERNS = [
    (r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|\d{4})\b", "Includes dates — good for timeline parsing"),
    (r"\b\d+[\+]?\s*(years?|yrs?)\b", "Mentions years of experience explicitly"),
    (r"(education|experience|skills|summary|objective|certifications|projects)", "Contains standard ATS section headers"),
    (r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b", "Proper name formatting detected"),
    (r"(linkedin|github|portfolio)", "Includes professional profile links"),
]

# ── Text extraction ───────────────────────────────────────────────────────────
def extract_text_from_pdf(file_bytes):
    reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    return "".join(page.extract_text() or "" for page in reader.pages)

def extract_text_from_docx(file_bytes):
    d = docx.Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in d.paragraphs)

def extract_text(uploaded_file):
    if not uploaded_file:
        return None
    file_bytes = uploaded_file.read()
    name = uploaded_file.name.lower()
    if name.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    if name.endswith(".docx") or name.endswith(".doc"):
        return extract_text_from_docx(file_bytes)
    return file_bytes.decode("utf-8", errors="ignore")

# ── Core analysis (no AI needed) ─────────────────────────────────────────────
def find_skills(text, skill_list):
    text_lower = text.lower()
    return [s for s in skill_list if re.search(r'\b' + re.escape(s) + r'\b', text_lower)]

def extract_experience(text):
    patterns = [
        r'(\d+)\+?\s*(?:to\s*\d+\s*)?years?\s+of\s+experience',
        r'(\d+)\+?\s*(?:to\s*\d+\s*)?years?\s+experience',
        r'experience\s+of\s+(\d+)\+?\s*years?',
        r'minimum\s+(\d+)\+?\s*years?',
        r'(\d+)\s*-\s*(\d+)\s*years?',
        r'two|three|four|five|six|seven|eight|nine|ten',
    ]
    word_map = {"two":"2","three":"3","four":"4","five":"5","six":"6","seven":"7","eight":"8","nine":"9","ten":"10"}
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            found = match.group(0)
            for w, n in word_map.items():
                found = found.replace(w, n)
            return found.strip().capitalize()
    return "Not specified"

def extract_education(text):
    degrees = ["phd","ph.d","doctorate","master","mba","msc","m.sc","m.tech","bachelor",
               "b.tech","b.e","bsc","b.sc","b.com","degree","graduate","postgraduate","diploma"]
    text_lower = text.lower()
    for deg in degrees:
        if deg in text_lower:
            sentences = re.split(r'[.\n]', text)
            for s in sentences:
                if deg in s.lower():
                    return s.strip()[:120]
    return "Not specified"

def extract_responsibilities(text):
    lines = text.split('\n')
    resp = []
    keywords = ["responsible","manage","develop","lead","implement","design","build",
                "create","analyze","support","coordinate","maintain","drive","ensure",
                "collaborate","identify","deliver","oversee","execute","track"]
    for line in lines:
        line = line.strip()
        line = re.sub(r'^[\*\-\•▪◦➢➤→]+\s*', '', line)
        if len(line) > 30 and any(kw in line.lower() for kw in keywords):
            resp.append(line[:150])
        if len(resp) >= 6:
            break
    return resp if resp else ["No specific responsibilities found"]

def compute_match_score(jd_text, resume_text):
    vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1,2))
    try:
        tfidf = vectorizer.fit_transform([jd_text, resume_text])
        score = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
        return round(score * 100)
    except:
        return 0

def ats_check(resume_text):
    text_lower = resume_text.lower()
    good, issues, suggestions = [], [], []

    for pattern, msg in ATS_GOOD_PATTERNS:
        if re.search(pattern, text_lower):
            good.append(msg)

    for pattern, msg in ATS_BAD_PATTERNS:
        if re.search(pattern, text_lower):
            issues.append(msg)

    word_count = len(resume_text.split())
    if word_count < 200:
        issues.append("Resume seems too short — ATS may rank it lower")
        suggestions.append("Expand resume to at least 400–600 words with detailed experience")
    elif word_count > 1000:
        good.append("Resume has sufficient detail and content length")

    sections = ["experience","education","skills","summary","objective","certifications","projects"]
    found_sections = [s for s in sections if s in text_lower]
    missing_sections = [s for s in ["experience","education","skills"] if s not in text_lower]

    if len(found_sections) >= 3:
        good.append(f"Has clear sections: {', '.join(found_sections)}")
    if missing_sections:
        issues.append(f"Missing key sections: {', '.join(missing_sections)}")
        suggestions.append(f"Add clearly labelled sections: {', '.join(missing_sections)}")

    if re.search(r'\b[\w.]+@[\w.]+\.\w+\b', resume_text):
        good.append("Email address detected — good for contact parsing")
    else:
        issues.append("No email address found")
        suggestions.append("Add a professional email address at the top")

    if re.search(r'\b\d{10}\b|\+\d{1,3}[\s\-]\d+', resume_text):
        good.append("Phone number detected")
    else:
        suggestions.append("Add a phone number for recruiter contact")

    if not issues:
        good.append("No major ATS issues detected")

    if not suggestions:
        suggestions.append("Use standard fonts (Arial, Calibri) and avoid graphics")
        suggestions.append("Save as .docx or plain PDF for best ATS compatibility")

    score = min(100, max(10, 40 + len(good) * 10 - len(issues) * 8))
    status = "Yes" if score >= 70 else ("Partially" if score >= 45 else "No")
    return {"score": score, "status": status, "good": good, "issues": issues, "suggestions": suggestions}

def analyze(jd_text, resume_text):
    jd_skills      = find_skills(jd_text, TECH_SKILLS)
    resume_skills  = find_skills(resume_text, TECH_SKILLS)
    jd_soft        = find_skills(jd_text, SOFT_SKILLS)

    matched   = [s for s in jd_skills if s in resume_skills]
    missing   = [s for s in jd_skills if s not in resume_skills]
    extra     = [s for s in resume_skills if s not in jd_skills]

    tfidf_score   = compute_match_score(jd_text, resume_text)
    skill_ratio   = (len(matched) / len(jd_skills) * 100) if jd_skills else tfidf_score
    final_score   = round((tfidf_score * 0.5) + (skill_ratio * 0.5))

    ats = ats_check(resume_text)

    strengths, gaps = [], []
    if matched:
        strengths.append(f"Matches {len(matched)} of {len(jd_skills)} required skills")
    if extra:
        strengths.append(f"Has additional skills: {', '.join(extra[:4])}")
    if re.search(r'\d+\s*(?:years?|yrs?)', resume_text, re.I):
        strengths.append("Demonstrates quantified experience")
    if re.search(r'\d+%|\$\d+|\d+x', resume_text):
        strengths.append("Includes measurable achievements with numbers")

    if missing:
        gaps.append(f"Missing skills: {', '.join(missing[:5])}")
    if len(resume_text.split()) < 300:
        gaps.append("Resume may lack sufficient detail to score well in ATS")

    if final_score >= 75:
        verdict = "Strong match — resume aligns well with the job requirements."
    elif final_score >= 50:
        verdict = "Moderate match — resume covers some requirements but has gaps to address."
    else:
        verdict = "Weak match — significant skill or experience gaps compared to the JD."

    return {
        "jd": {
            "required_skills": jd_skills[:12],
            "soft_skills": jd_soft[:6],
            "experience": extract_experience(jd_text),
            "education": extract_education(jd_text),
            "responsibilities": extract_responsibilities(jd_text),
        },
        "ats": ats,
        "relevance": {
            "score": final_score,
            "matched": matched,
            "missing": missing,
            "strengths": strengths,
            "gaps": gaps,
            "verdict": verdict,
        }
    }

def score_color(s):
    return "score-green" if s >= 70 else ("score-amber" if s >= 45 else "score-red")

def render_tags(items, cls="tag"):
    return " ".join(f'<span class="{cls}">{i}</span>' for i in items) or "_None found_"

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("ℹ About")
    st.success("**No API key needed!**\nThis app uses local NLP — works fully offline.")
    st.divider()
    st.markdown("**How it works:**")
    st.markdown("- Keyword extraction from JD\n- TF-IDF similarity scoring\n- ATS pattern checks\n- Skill gap analysis")
    st.divider()
    st.caption("Supports PDF, DOCX, or plain text paste")

# ── Main ──────────────────────────────────────────────────────────────────────
st.title(" JD & Resume Analyzer")
st.caption("No API key needed · Fully local · Paste or upload JD and Resume")

col1, col2 = st.columns(2)

with col1:
    st.subheader(" Job Description")
    t1, t2 = st.tabs(["Paste Text", "Upload File"])
    with t1:
        jd_input = st.text_area("Paste JD here", height=280, placeholder="Paste the full job description...")
    with t2:
        jd_file = st.file_uploader("Upload JD", type=["pdf","docx","txt"], key="jd")

with col2:
    st.subheader(" Resume")
    t3, t4 = st.tabs(["Paste Text", "Upload File"])
    with t3:
        res_input = st.text_area("Paste resume here", height=280, placeholder="Paste the full resume text...")
    with t4:
        res_file = st.file_uploader("Upload Resume", type=["pdf","docx","txt"], key="res")

jd_final  = extract_text(jd_file)  if jd_file  else jd_input.strip()
res_final = extract_text(res_file) if res_file else res_input.strip()

st.divider()

if st.button(" Analyze Now", type="primary", use_container_width=True):
    if not jd_final:
        st.error("Please provide the Job Description.")
    elif not res_final:
        st.error("Please provide the Resume.")
    else:
        with st.spinner("Analyzing..."):
            result = analyze(jd_final, res_final)

        jd  = result["jd"]
        ats = result["ats"]
        rel = result["relevance"]

        st.success("✅ Analysis complete!")
        st.divider()

        # Score cards
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-big {score_color(rel['score'])}">{rel['score']}%</div>
                <div class="metric-label">JD–Resume Match</div>
            </div>""", unsafe_allow_html=True)
        with m2:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-big {score_color(ats['score'])}">{ats['score']}%</div>
                <div class="metric-label">ATS Score</div>
            </div>""", unsafe_allow_html=True)
        with m3:
            cls = {"Yes":"ats-yes","No":"ats-no","Partially":"ats-partial"}.get(ats['status'],"ats-partial")
            st.markdown(f"""<div class="metric-card" style="padding-top:28px;">
                <span class="ats-badge {cls}">ATS {ats['status']}</span>
                <div class="metric-label" style="margin-top:10px;">ATS Friendliness</div>
            </div>""", unsafe_allow_html=True)

        st.write("")
        r1, r2, r3 = st.columns(3)

        with r1:
            st.markdown("### 📌 JD Key Points")
            with st.expander("Required Skills", expanded=True):
                st.markdown(render_tags(jd["required_skills"], "tag tag-skill"), unsafe_allow_html=True)
            with st.expander("Soft Skills"):
                st.markdown(render_tags(jd["soft_skills"], "tag tag-soft"), unsafe_allow_html=True)
            with st.expander("Key Responsibilities"):
                for r in jd["responsibilities"]:
                    st.markdown(f"• {r}")
            with st.expander("Experience & Education"):
                st.markdown(f"**Experience:** {jd['experience']}")
                st.markdown(f"**Education:** {jd['education']}")

        with r2:
            st.markdown("### ✅ ATS Analysis")
            with st.expander("What's working", expanded=True):
                for p in ats["good"]:
                    st.markdown(f"✅ {p}")
            with st.expander("Issues found"):
                for i in ats["issues"]:
                    st.markdown(f"❌ {i}")
            with st.expander("Suggestions"):
                for s in ats["suggestions"]:
                    st.markdown(f"💡 {s}")

        with r3:
            st.markdown("### 📊 Relevance Breakdown")
            st.info(rel["verdict"])
            with st.expander("Matched skills", expanded=True):
                st.markdown(render_tags(rel["matched"]), unsafe_allow_html=True)
            with st.expander("Missing skills"):
                st.markdown(render_tags(rel["missing"], "tag tag-missing"), unsafe_allow_html=True)
            with st.expander("Your strengths"):
                for s in rel["strengths"]:
                    st.markdown(f"⭐ {s}")
            with st.expander("Gaps to address"):
                for g in rel["gaps"]:
                    st.markdown(f"⚠️ {g}")
