import streamlit as st
import anthropic
import PyPDF2
import docx
import io
import json
import re

st.set_page_config(
    page_title="JD & Resume Analyzer",
    layout="wide"
)

st.markdown("""
<style>
    .metric-card {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        border: 1px solid #e9ecef;
    }
    .metric-big {
        font-size: 3rem;
        font-weight: 700;
        line-height: 1;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #6c757d;
        margin-top: 6px;
    }
    .score-green { color: #1D9E75; }
    .score-amber { color: #BA7517; }
    .score-red { color: #E24B4A; }
    .tag {
        display: inline-block;
        background: #E1F5EE;
        color: #085041;
        border-radius: 6px;
        padding: 3px 10px;
        font-size: 0.8rem;
        margin: 3px 2px;
    }
    .tag-missing {
        background: #FCEBEB;
        color: #A32D2D;
    }
    .tag-skill {
        background: #E6F1FB;
        color: #0C447C;
    }
    .section-header {
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 8px;
        color: #2C2C2A;
    }
    .result-box {
        background: white;
        border: 1px solid #e9ecef;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
    }
    .ats-badge {
        display: inline-block;
        padding: 6px 18px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 1rem;
    }
    .ats-yes { background: #E1F5EE; color: #085041; }
    .ats-no { background: #FCEBEB; color: #A32D2D; }
    .ats-partial { background: #FAEEDA; color: #633806; }
    div[data-testid="stExpander"] {
        border: 1px solid #e9ecef;
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)


def extract_text_from_pdf(file_bytes):
    reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def extract_text_from_docx(file_bytes):
    doc = docx.Document(io.BytesIO(file_bytes))
    return "\n".join([para.text for para in doc.paragraphs])


def extract_text(uploaded_file):
    if uploaded_file is None:
        return None
    file_bytes = uploaded_file.read()
    name = uploaded_file.name.lower()
    if name.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    elif name.endswith(".docx") or name.endswith(".doc"):
        return extract_text_from_docx(file_bytes)
    else:
        return file_bytes.decode("utf-8", errors="ignore")


def analyze_with_claude(api_key, jd_text, resume_text):
    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""You are an expert HR analyst and ATS specialist. Analyze the following Job Description and Resume.

JOB DESCRIPTION:
{jd_text}

RESUME:
{resume_text}

Return ONLY a valid JSON object (no markdown, no extra text) with this exact structure:
{{
  "jd_key_points": {{
    "required_skills": ["skill1", "skill2"],
    "preferred_skills": ["skill1", "skill2"],
    "experience_required": "X years in ...",
    "education": "Bachelor's in ...",
    "key_responsibilities": ["responsibility1", "responsibility2", "responsibility3"],
    "soft_skills": ["communication", "leadership"]
  }},
  "ats_analysis": {{
    "is_ats_friendly": "Yes" | "No" | "Partially",
    "score": 0-100,
    "good_points": ["point1", "point2"],
    "issues": ["issue1", "issue2"],
    "suggestions": ["suggestion1", "suggestion2"]
  }},
  "relevance": {{
    "score": 0-100,
    "matched_skills": ["skill1", "skill2"],
    "missing_skills": ["skill1", "skill2"],
    "strengths": ["strength1", "strength2"],
    "gaps": ["gap1", "gap2"],
    "overall_verdict": "one sentence summary"
  }}
}}"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"^```\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


def score_color(score):
    if score >= 70:
        return "score-green"
    elif score >= 45:
        return "score-amber"
    else:
        return "score-red"


# ── Header ──────────────────────────────────────────────────────────────────
st.title(" JD & Resume Analyzer")
st.caption("Powered by Claude AI · Paste or upload your JD and Resume to get instant analysis")

# ── API Key ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header(" Setup")
    api_key = st.text_input("Anthropic API Key", type="password", placeholder="sk-ant-...")
    st.caption("Get a free key at [console.anthropic.com](https://console.anthropic.com)")
    st.divider()
    st.markdown("**What this tool does:**")
    st.markdown("-  Extracts key points from JD\n-  Checks ATS friendliness\n-  Scores resume–JD match")
    st.divider()
    st.caption("Supports PDF, DOCX, or plain text paste")

# ── Input Section ────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader(" Job Description")
    jd_tab1, jd_tab2 = st.tabs(["Paste Text", "Upload File"])
    with jd_tab1:
        jd_text_input = st.text_area("Paste JD here", height=280, placeholder="Paste the full job description...")
    with jd_tab2:
        jd_file = st.file_uploader("Upload JD", type=["pdf", "docx", "txt"], key="jd_file")

with col2:
    st.subheader(" Resume")
    res_tab1, res_tab2 = st.tabs(["Paste Text", "Upload File"])
    with res_tab1:
        resume_text_input = st.text_area("Paste resume here", height=280, placeholder="Paste the full resume text...")
    with res_tab2:
        resume_file = st.file_uploader("Upload Resume", type=["pdf", "docx", "txt"], key="resume_file")

# Resolve final text
jd_final = extract_text(jd_file) if jd_file else jd_text_input.strip()
resume_final = extract_text(resume_file) if resume_file else resume_text_input.strip()

st.divider()

analyze_btn = st.button(" Analyze Now", type="primary", use_container_width=True)

# ── Analysis ─────────────────────────────────────────────────────────────────
if analyze_btn:
    if not api_key:
        st.error("Please enter your Anthropic API key in the sidebar.")
    elif not jd_final:
        st.error("Please provide the Job Description.")
    elif not resume_final:
        st.error("Please provide the Resume.")
    else:
        with st.spinner("Analyzing with Claude AI... this takes ~15 seconds"):
            try:
                result = analyze_with_claude(api_key, jd_final, resume_final)
            except json.JSONDecodeError as e:
                st.error(f"Failed to parse AI response. Try again. ({e})")
                st.stop()
            except Exception as e:
                st.error(f"API error: {e}")
                st.stop()

        jd_kp = result.get("jd_key_points", {})
        ats = result.get("ats_analysis", {})
        rel = result.get("relevance", {})

        st.success("Analysis complete!")
        st.divider()

        # ── Score Cards ───────────────────────────────────────────────────────
        m1, m2, m3 = st.columns(3)

        ats_score = ats.get("score", 0)
        rel_score = rel.get("score", 0)
        ats_friendly = ats.get("is_ats_friendly", "Partially")
        ats_badge_class = {"Yes": "ats-yes", "No": "ats-no", "Partially": "ats-partial"}.get(ats_friendly, "ats-partial")

        with m1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-big {score_color(rel_score)}">{rel_score}%</div>
                <div class="metric-label">JD–Resume Match</div>
            </div>""", unsafe_allow_html=True)

        with m2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-big {score_color(ats_score)}">{ats_score}%</div>
                <div class="metric-label">ATS Score</div>
            </div>""", unsafe_allow_html=True)

        with m3:
            st.markdown(f"""
            <div class="metric-card" style="padding-top:28px;">
                <span class="ats-badge {ats_badge_class}">ATS {ats_friendly}</span>
                <div class="metric-label" style="margin-top:10px;">ATS Friendliness</div>
            </div>""", unsafe_allow_html=True)

        st.write("")

        # ── Three columns of results ──────────────────────────────────────────
        r1, r2, r3 = st.columns(3)

        # JD Key Points
        with r1:
            st.markdown("###  JD Key Points")

            with st.expander("Required Skills", expanded=True):
                tags = " ".join([f'<span class="tag tag-skill">{s}</span>' for s in jd_kp.get("required_skills", [])])
                st.markdown(tags or "_None found_", unsafe_allow_html=True)

            with st.expander("Preferred Skills"):
                tags = " ".join([f'<span class="tag">{s}</span>' for s in jd_kp.get("preferred_skills", [])])
                st.markdown(tags or "_None found_", unsafe_allow_html=True)

            with st.expander("Key Responsibilities"):
                for r in jd_kp.get("key_responsibilities", []):
                    st.markdown(f"• {r}")

            with st.expander("Experience & Education"):
                st.markdown(f"**Experience:** {jd_kp.get('experience_required', 'N/A')}")
                st.markdown(f"**Education:** {jd_kp.get('education', 'N/A')}")
                soft = " ".join([f'<span class="tag">{s}</span>' for s in jd_kp.get("soft_skills", [])])
                if soft:
                    st.markdown(f"**Soft Skills:** {soft}", unsafe_allow_html=True)

        # ATS Analysis
        with r2:
            st.markdown("###  ATS Analysis")

            with st.expander("What's working", expanded=True):
                for p in ats.get("good_points", []):
                    st.markdown(f"✅ {p}")

            with st.expander("Issues found"):
                for issue in ats.get("issues", []):
                    st.markdown(f"❌ {issue}")

            with st.expander("Suggestions to improve"):
                for s in ats.get("suggestions", []):
                    st.markdown(f"💡 {s}")

        # Relevance
        with r3:
            st.markdown("### 📊 Relevance Breakdown")

            verdict = rel.get("overall_verdict", "")
            if verdict:
                st.info(verdict)

            with st.expander("Matched skills", expanded=True):
                tags = " ".join([f'<span class="tag">{s}</span>' for s in rel.get("matched_skills", [])])
                st.markdown(tags or "_No matches found_", unsafe_allow_html=True)

            with st.expander("Missing skills"):
                tags = " ".join([f'<span class="tag tag-missing">{s}</span>' for s in rel.get("missing_skills", [])])
                st.markdown(tags or "_None missing_", unsafe_allow_html=True)

            with st.expander("Your strengths"):
                for s in rel.get("strengths", []):
                    st.markdown(f"⭐ {s}")

            with st.expander("Gaps to address"):
                for g in rel.get("gaps", []):
                    st.markdown(f"⚠️ {g}")
