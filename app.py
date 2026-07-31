"""
app.py - AI Resume Shortlisting & Skill Analysis Platform
-----------------------------------------------------------------
Frontend only. All analysis logic comes from the existing,
unmodified backend modules: extractor.py, skills.py, matcher.py,
gap_analyzer.py, questions.py.
"""

import re
import json
import time
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from extractor import extract_text
from skills import extract_skills
from matcher import calculate_hybrid_score, format_match_report
from gap_analyzer import analyze_skill_gap, format_gap_report
from questions import generate_interview_questions, format_questions_report

# ===================================================================
# PAGE CONFIG
# ===================================================================
st.set_page_config(
    page_title="AI Resume Shortlisting Platform",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ===================================================================
# CUSTOM DARK THEME CSS
# ===================================================================
def inject_custom_css():
    st.markdown("""
        <style>
        .stApp { background-color: #0e1117; }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(6px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .fade-in { animation: fadeIn 0.4s ease-in-out; }

        .hero-title {
            font-size: 2.5rem;
            font-weight: 700;
            text-align: center;
            background: linear-gradient(90deg, #6366f1, #22d3ee);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.2rem;
        }
        .hero-subtitle {
            font-size: 1.05rem;
            color: #9ca3af;
            text-align: center;
            margin-bottom: 2rem;
        }

        /* ---- Main workflow card ---- */
        .workflow-card {
            background: linear-gradient(150deg, #161b22, #1a2030);
            border: 1px solid #262d3a;
            border-radius: 18px;
            padding: 2rem 2.2rem;
            margin-bottom: 1.8rem;
            box-shadow: 0 8px 30px rgba(0,0,0,0.35);
        }
        .workflow-heading {
            font-size: 1.3rem;
            font-weight: 700;
            color: #e5e7eb;
            margin-bottom: 0.2rem;
        }
        .workflow-subheading {
            color: #9ca3af;
            font-size: 0.92rem;
            margin-bottom: 1.4rem;
        }

        .upload-slot {
            background-color: #0e1117;
            border: 1.5px dashed #374151;
            border-radius: 14px;
            padding: 1rem 1.2rem 0.4rem 1.2rem;
            transition: border-color 0.2s ease, transform 0.15s ease;
            margin-bottom: 0.6rem;
        }
        .upload-slot:hover { border-color: #6366f1; transform: translateY(-2px); }
        .upload-slot-title {
            font-weight: 600;
            font-size: 1rem;
            color: #e5e7eb;
            margin-bottom: 0.1rem;
        }
        .upload-slot-caption {
            color: #6b7280;
            font-size: 0.8rem;
            margin-bottom: 0.6rem;
        }
        .upload-status-ok {
            color: #22c55e;
            font-size: 0.85rem;
            font-weight: 600;
        }
        .upload-status-pending {
            color: #6b7280;
            font-size: 0.85rem;
        }

        div[data-testid="stFileUploaderDropzone"] {
            background-color: #0b0e14;
            border-radius: 10px;
        }

        div.stButton > button[kind="primary"] {
            border-radius: 10px;
            font-weight: 700;
            font-size: 1.05rem;
            padding: 0.6rem 0;
            background: linear-gradient(90deg, #6366f1, #22d3ee);
            border: none;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }
        div.stButton > button[kind="primary"]:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 6px 18px rgba(99,102,241,0.4);
        }

        .badge {
            display: inline-block;
            padding: 0.3rem 0.8rem;
            margin: 0.2rem;
            border-radius: 999px;
            font-size: 0.85rem;
            font-weight: 500;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
            cursor: default;
        }
        .badge:hover { transform: translateY(-2px); box-shadow: 0 4px 10px rgba(0,0,0,0.35); }
        .badge-match { background-color: rgba(34,197,94,0.15); color: #22c55e; border: 1px solid #22c55e; }
        .badge-missing { background-color: rgba(239,68,68,0.15); color: #ef4444; border: 1px solid #ef4444; }
        .badge-extra { background-color: rgba(99,102,241,0.15); color: #818cf8; border: 1px solid #818cf8; }

        .roadmap-card {
            background-color: #161b22;
            border-radius: 10px;
            padding: 1rem 1.2rem;
            margin-bottom: 0.8rem;
            border: 1px solid #262d3a;
            border-left: 4px solid #6366f1;
            transition: transform 0.15s ease;
        }
        .roadmap-card:hover { transform: translateX(3px); }
        .roadmap-priority-high { border-left-color: #ef4444; }
        .roadmap-priority-med { border-left-color: #f59e0b; }
        .roadmap-priority-low { border-left-color: #22c55e; }

        .pill {
            display: inline-block;
            font-size: 0.72rem;
            padding: 0.15rem 0.55rem;
            border-radius: 6px;
            margin-right: 0.4rem;
            font-weight: 600;
        }
        .pill-diff-easy { background: rgba(34,197,94,0.15); color: #22c55e; }
        .pill-diff-medium { background: rgba(245,158,11,0.15); color: #f59e0b; }
        .pill-diff-hard { background: rgba(239,68,68,0.15); color: #ef4444; }
        .pill-priority-high { background: rgba(239,68,68,0.15); color: #ef4444; }
        .pill-priority-med { background: rgba(245,158,11,0.15); color: #f59e0b; }
        .pill-priority-low { background: rgba(34,197,94,0.15); color: #22c55e; }

        .readiness-strong { color: #22c55e; font-weight: 700; }
        .readiness-good { color: #3b82f6; font-weight: 700; }
        .readiness-moderate { color: #f59e0b; font-weight: 700; }
        .readiness-needs { color: #ef4444; font-weight: 700; }

        .candidate-card {
            background-color: #161b22;
            border-radius: 12px;
            padding: 1.2rem 1.4rem;
            margin-bottom: 1rem;
            border: 1px solid #262d3a;
        }
        .candidate-field { color: #d1d5db; margin: 0.15rem 0; font-size: 0.95rem; }
        .candidate-field b { color: #9ca3af; }

        .exec-summary-card {
            background: linear-gradient(145deg, #161b22, #1c2230);
            border-radius: 12px;
            padding: 1.4rem;
            border: 1px solid #262d3a;
        }

        .diff-tag {
            font-size: 0.75rem;
            padding: 0.15rem 0.5rem;
            border-radius: 6px;
            margin-left: 0.5rem;
        }
        .diff-beginner { background-color: rgba(34,197,94,0.15); color: #22c55e; }
        .diff-intermediate { background-color: rgba(245,158,11,0.15); color: #f59e0b; }
        .diff-advanced { background-color: rgba(239,68,68,0.15); color: #ef4444; }
        </style>
    """, unsafe_allow_html=True)


READINESS_CSS_CLASS = {
    "Strong Fit": "readiness-strong",
    "Good Fit": "readiness-good",
    "Moderate Fit": "readiness-moderate",
    "Needs Improvement": "readiness-needs",
}

CATEGORY_LEARNING_META = {
    "Programming Languages": ("Easy", "pill-diff-easy", "1-2 weeks"),
    "Web Development": ("Medium", "pill-diff-medium", "2-3 weeks"),
    "Databases": ("Medium", "pill-diff-medium", "1-2 weeks"),
    "Cloud & DevOps": ("Hard", "pill-diff-hard", "3-4 weeks"),
    "AI/ML": ("Hard", "pill-diff-hard", "4-6 weeks"),
    "Data Science": ("Medium", "pill-diff-medium", "2-4 weeks"),
    "Mobile Development": ("Medium", "pill-diff-medium", "2-3 weeks"),
    "Version Control & Tools": ("Easy", "pill-diff-easy", "3-5 days"),
    "Operating Systems": ("Easy", "pill-diff-easy", "1 week"),
    "Computer Science Fundamentals": ("Medium", "pill-diff-medium", "2-4 weeks"),
}

DIFF_CSS = {"Beginner": "diff-beginner", "Intermediate": "diff-intermediate", "Advanced": "diff-advanced"}
DIFF_ICON = {"Beginner": "🟢", "Intermediate": "🟡", "Advanced": "🔴"}


# ===================================================================
# CANDIDATE INFO EXTRACTION (UI-layer only, doesn't touch backend)
# ===================================================================
def extract_candidate_info(text: str) -> dict:
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    phone_match = re.search(r'(\+?\d[\d\-\s\(\)]{8,}\d)', text)
    github_match = re.search(r'(github\.com/[A-Za-z0-9_\-]+)', text, re.IGNORECASE)
    linkedin_match = re.search(r'(linkedin\.com/in/[A-Za-z0-9_\-]+)', text, re.IGNORECASE)
    portfolio_match = re.search(
        r'((https?://)?[A-Za-z0-9\-]+\.(dev|me|io|com)/[A-Za-z0-9_\-/]*)', text, re.IGNORECASE
    )
    location_match = re.search(
        r'\b([A-Z][a-zA-Z]+,\s?[A-Z][a-zA-Z]+)\b', text
    )

    name = "Not Available"
    for line in text.strip().splitlines()[:5]:
        clean_line = line.strip()
        if not clean_line or "@" in clean_line or any(ch.isdigit() for ch in clean_line):
            continue
        words = clean_line.split()
        if 1 <= len(words) <= 4 and clean_line.replace(" ", "").isalpha():
            name = clean_line.title()
            break

    return {
        "name": name,
        "email": email_match.group(0) if email_match else "Not Available",
        "phone": phone_match.group(0).strip() if phone_match else "Not Available",
        "github": github_match.group(0) if github_match else "Not Available",
        "linkedin": linkedin_match.group(0) if linkedin_match else "Not Available",
        "portfolio": portfolio_match.group(0) if portfolio_match else "Not Available",
        "location": location_match.group(0) if location_match else "Not Available",
    }


def looks_like_wrong_upload(text: str, expected: str) -> str | None:
    lowered = text.lower()
    jd_markers = ["responsibilities", "we are looking for", "requirements:", "years of experience required",
                  "apply now", "job description", "about the role"]
    resume_markers = ["education", "projects", "work experience", "objective", "career summary", "certifications"]

    jd_score = sum(1 for m in jd_markers if m in lowered)
    resume_score = sum(1 for m in resume_markers if m in lowered)

    if expected == "resume" and jd_score >= 2 and resume_score == 0:
        return "This looks like it might be a Job Description, not a resume. Please double-check your upload."
    if expected == "jd" and resume_score >= 2 and jd_score == 0:
        return "This looks like it might be a resume, not a Job Description. Please double-check your upload."
    return None


# ===================================================================
# CHART BUILDERS
# ===================================================================
def build_donut_chart(matched: int, missing: int, additional: int):
    fig = px.pie(
        values=[matched, missing, additional],
        names=["Matching", "Missing", "Additional"],
        hole=0.55,
        color=["Matching", "Missing", "Additional"],
        color_discrete_map={"Matching": "#22c55e", "Missing": "#ef4444", "Additional": "#818cf8"},
    )
    fig.update_traces(hovertemplate="%{label}: %{value} skills (%{percent})<extra></extra>")
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e5e7eb",
        showlegend=True,
        margin=dict(t=20, b=20, l=20, r=20),
        height=320,
    )
    return fig


def build_gauge_chart(score: float):
    if score < 40:
        color = "#ef4444"
    elif score < 60:
        color = "#f97316"
    elif score < 75:
        color = "#eab308"
    elif score < 90:
        color = "#84cc16"
    else:
        color = "#22c55e"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"suffix": "%", "font": {"color": "#e5e7eb"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#e5e7eb"},
            "bar": {"color": color},
            "bgcolor": "#161b22",
            "steps": [
                {"range": [0, 39], "color": "rgba(239,68,68,0.15)"},
                {"range": [39, 59], "color": "rgba(249,115,22,0.15)"},
                {"range": [59, 74], "color": "rgba(234,179,8,0.15)"},
                {"range": [74, 89], "color": "rgba(132,204,22,0.15)"},
                {"range": [89, 100], "color": "rgba(34,197,94,0.15)"},
            ],
        },
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#e5e7eb",
        margin=dict(t=30, b=10, l=30, r=30),
        height=280,
    )
    return fig


def build_category_bar_chart(categorized_matching: dict, categorized_missing: dict):
    categories = sorted(set(list(categorized_matching.keys()) + list(categorized_missing.keys())))
    if not categories:
        categories = ["No Data"]
    matched_counts = [len(categorized_matching.get(c, [])) for c in categories] if categories != ["No Data"] else [0]
    missing_counts = [len(categorized_missing.get(c, [])) for c in categories] if categories != ["No Data"] else [0]

    fig = go.Figure()
    fig.add_trace(go.Bar(y=categories, x=matched_counts, name="Matched", orientation="h",
                          marker_color="#22c55e", hovertemplate="%{y}: %{x} matched<extra></extra>"))
    fig.add_trace(go.Bar(y=categories, x=missing_counts, name="Missing", orientation="h",
                          marker_color="#ef4444", hovertemplate="%{y}: %{x} missing<extra></extra>"))
    fig.update_layout(
        barmode="stack",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e5e7eb",
        margin=dict(t=20, b=20, l=20, r=20),
        height=max(280, 40 * len(categories)),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig


def build_radar_chart(resume_text: str, jd_text: str):
    resume_cats = extract_skills(resume_text)["categorized"]
    jd_cats = extract_skills(jd_text)["categorized"]

    categories = sorted(set(list(resume_cats.keys()) + list(jd_cats.keys())))
    if not categories:
        categories = ["No Skills Detected"]
        resume_vals = [0]
        jd_vals = [0]
    else:
        resume_vals = [len(resume_cats.get(c, [])) for c in categories]
        jd_vals = [len(jd_cats.get(c, [])) for c in categories]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=resume_vals, theta=categories, fill='toself',
                                   name='Resume', line_color="#22d3ee"))
    fig.add_trace(go.Scatterpolar(r=jd_vals, theta=categories, fill='toself',
                                   name='Job Description', line_color="#818cf8"))
    fig.update_layout(
        polar=dict(
            bgcolor="#161b22",
            radialaxis=dict(visible=True, color="#9ca3af"),
            angularaxis=dict(color="#e5e7eb"),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#e5e7eb",
        showlegend=True,
        margin=dict(t=30, b=20, l=40, r=40),
        height=400,
    )
    return fig


# ===================================================================
# RENDER HELPERS
# ===================================================================
def render_badges(skills: list, css_class: str, categorized: dict = None):
    if not skills:
        st.caption("None")
        return
    skill_to_category = {}
    if categorized:
        for cat, sk_list in categorized.items():
            for s in sk_list:
                skill_to_category[s] = cat
    html = "".join(
        f'<span class="badge {css_class}" title="{skill_to_category.get(s, "")}">{s}</span>'
        for s in skills
    )
    st.markdown(html, unsafe_allow_html=True)


def render_roadmap_cards(recommendations: list):
    if not recommendations:
        st.info("No additional skills recommended — candidate covers all required areas.")
        return
    priority_labels = ["High", "High", "Medium", "Medium", "Low"]
    priority_css = ["pill-priority-high", "pill-priority-high", "pill-priority-med",
                     "pill-priority-med", "pill-priority-low"]
    border_css = ["roadmap-priority-high", "roadmap-priority-high", "roadmap-priority-med",
                  "roadmap-priority-med", "roadmap-priority-low"]

    for i, rec in enumerate(recommendations):
        idx = min(i, len(priority_labels) - 1)
        difficulty, diff_css, est_time = CATEGORY_LEARNING_META.get(
            rec["category"], ("Medium", "pill-diff-medium", "2-3 weeks")
        )
        st.markdown(f"""
            <div class="roadmap-card fade-in {border_css[idx]}">
                <b>{i + 1}. {rec['skill']}</b>
                <span class="pill {diff_css}">Difficulty: {difficulty}</span>
                <span class="pill {priority_css[idx]}">Priority: {priority_labels[idx]}</span><br>
                <span style="color:#9ca3af; font-size:0.85rem;">
                    Category: {rec['category']} &nbsp;|&nbsp; Est. Learning Time: {est_time}
                </span><br>
                <span style="color:#6b7280; font-size:0.82rem;">
                    Why it matters: Required by the job description but not detected in this candidate's resume.
                </span>
            </div>
        """, unsafe_allow_html=True)


def assign_difficulty(index: int, is_missing: bool) -> str:
    if is_missing:
        levels = ["Beginner", "Beginner", "Intermediate"]
    else:
        levels = ["Intermediate", "Advanced", "Intermediate", "Advanced"]
    return levels[index % len(levels)]


def render_interview_section(question_set: dict):
    all_skills = [e["skill"] for e in question_set["technical_questions"] + question_set["gap_probe_questions"]]

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        difficulty_filter = st.selectbox(
            "Filter by difficulty", ["All", "Beginner", "Intermediate", "Advanced"], key="diff_filter"
        )
    with col_f2:
        skill_filter = st.selectbox("Filter by skill", ["All"] + sorted(set(all_skills)), key="skill_filter")

    regenerate = st.button("🔄 Generate New Questions")
    if regenerate:
        st.session_state["question_regen_key"] = st.session_state.get("question_regen_key", 0) + 1
        st.rerun()

    def matches_filters(skill, difficulty):
        if difficulty_filter != "All" and difficulty != difficulty_filter:
            return False
        if skill_filter != "All" and skill != skill_filter:
            return False
        return True

    all_questions_for_download = []

    with st.expander("🧪 Technical Verification Questions", expanded=True):
        any_shown = False
        for i, entry in enumerate(question_set["technical_questions"]):
            diff = assign_difficulty(i, is_missing=False)
            if not matches_filters(entry["skill"], diff):
                continue
            any_shown = True
            diff_css = DIFF_CSS[diff]
            diff_icon = DIFF_ICON[diff]
            st.markdown(
                f"**{entry['skill']}** <span class='diff-tag {diff_css}'>{diff_icon} {diff}</span>",
                unsafe_allow_html=True,
            )
            for q in entry["questions"]:
                st.code(q, language=None)
                all_questions_for_download.append(f"[Technical - {entry['skill']} - {diff}] {q}")
        if not any_shown:
            st.caption("No questions match the current filters.")

    with st.expander("🧩 Skill Gap Probe Questions"):
        any_shown = False
        for i, entry in enumerate(question_set["gap_probe_questions"]):
            diff = assign_difficulty(i, is_missing=True)
            if not matches_filters(entry["skill"], diff):
                continue
            any_shown = True
            diff_css = DIFF_CSS[diff]
            diff_icon = DIFF_ICON[diff]
            st.markdown(
                f"**{entry['skill']}** <span class='diff-tag {diff_css}'>{diff_icon} {diff}</span>",
                unsafe_allow_html=True,
            )
            for q in entry["questions"]:
                st.code(q, language=None)
                all_questions_for_download.append(f"[Gap Probe - {entry['skill']} - {diff}] {q}")
        if not any_shown:
            st.caption("No questions match the current filters.")

    if all_questions_for_download:
        st.download_button(
            "⬇️ Download Filtered Questions (TXT)",
            data="\n".join(all_questions_for_download),
            file_name="interview_questions.txt",
            mime="text/plain",
        )


def render_executive_summary(candidate_info, match_result, gap_result):
    score = match_result["hybrid_score_percentage"]
    if score >= 80:
        recommendation, rec_color = "Strongly Recommend", "#22c55e"
    elif score >= 60:
        recommendation, rec_color = "Recommend after Technical Interview", "#3b82f6"
    else:
        recommendation, rec_color = "Needs Upskilling", "#ef4444"

    strengths = gap_result["matching_skills"][:5] or ["None detected"]
    weaknesses = gap_result["missing_skills"][:5] or ["None — full coverage"]

    st.markdown(f"""
        <div class="exec-summary-card fade-in">
            <h4>📋 Candidate Summary — {candidate_info['name']}</h4>
            <p style="font-size:1.1rem;">Overall Match: <b style="color:{rec_color};">{score}%</b></p>
            <p><b>Strengths:</b> {', '.join(strengths)}</p>
            <p><b>Areas to Improve:</b> {', '.join(weaknesses)}</p>
            <p><b>Hiring Recommendation:</b>
                <span style="color:{rec_color}; font-weight:700;">{recommendation}</span>
            </p>
        </div>
    """, unsafe_allow_html=True)


def generate_txt_report(candidate_info, match_result, gap_result, question_set) -> str:
    lines = [
        "=" * 60,
        "AI RESUME SHORTLISTING - CANDIDATE REPORT",
        "=" * 60,
        f"Name     : {candidate_info['name']}",
        f"Email    : {candidate_info['email']}",
        f"Phone    : {candidate_info['phone']}",
        f"GitHub   : {candidate_info['github']}",
        f"LinkedIn : {candidate_info['linkedin']}",
        f"Portfolio: {candidate_info['portfolio']}",
        f"Location : {candidate_info['location']}",
        "",
        format_match_report(match_result),
        "",
        format_gap_report(gap_result),
        "",
        format_questions_report(question_set),
    ]
    return "\n".join(lines)


def generate_json_report(candidate_info, match_result, gap_result, question_set) -> str:
    payload = {
        "candidate": candidate_info,
        "match_result": match_result,
        "gap_analysis": gap_result,
        "interview_questions": question_set,
        "generated_at": datetime.now().isoformat(),
    }
    return json.dumps(payload, indent=2, default=str)


def safe_extract(file):
    try:
        text = extract_text(file)
        if not text or not text.strip():
            return None, "No readable text could be extracted from this file. It may be empty, scanned, or corrupted."
        return text, None
    except Exception as e:
        return None, f"Failed to process file: {e}"


# ===================================================================
# CACHED ANALYSIS
# ===================================================================
@st.cache_data(show_spinner=False)
def cached_full_analysis(resume_text: str, jd_text: str, tfidf_weight: float, skill_weight: float):
    match_result = calculate_hybrid_score(
        resume_text, jd_text, tfidf_weight=tfidf_weight, skill_weight=skill_weight
    )
    gap_result = analyze_skill_gap(resume_text, jd_text)
    question_set = generate_interview_questions(
        gap_result["matching_skills"], gap_result["missing_skills"]
    )
    return match_result, gap_result, question_set


# ===================================================================
# SESSION STATE
# ===================================================================
if "analysis_history" not in st.session_state:
    st.session_state.analysis_history = []

# ===================================================================
# UI START
# ===================================================================
inject_custom_css()

st.markdown('<div class="hero-title fade-in">🎯 AI Resume Shortlisting & Skill Analysis Platform</div>',
            unsafe_allow_html=True)
st.markdown(
    '<div class="hero-subtitle fade-in">Upload any resume and any job description to instantly evaluate '
    'candidate suitability, detect skill gaps, and generate interview questions.</div>',
    unsafe_allow_html=True,
)

# -------------------------------------------------------------
# SIDEBAR - Advanced options only
# -------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Advanced Settings")

    with st.expander("🎛️ Fine-tune Scoring Weights", expanded=False):
        st.caption("These are also editable in the main panel — changes here sync automatically.")

    with st.expander("🧹 Session", expanded=False):
        reset_clicked = st.button("♻️ Reset Everything", use_container_width=True)
        if st.button("🗑️ Clear Cache", use_container_width=True):
            st.cache_data.clear()
            st.success("Cache cleared.")

if reset_clicked:
    st.session_state.analysis_history = []
    st.cache_data.clear()
    st.rerun()

# ===================================================================
# MAIN CENTER WORKFLOW CARD (replaces sidebar-driven upload)
# ===================================================================
st.markdown('<div class="workflow-card fade-in">', unsafe_allow_html=True)
st.markdown('<div class="workflow-heading">🚀 Start a New Analysis</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="workflow-subheading">Upload a resume and job description to get an instant '
    'AI-powered suitability report.</div>',
    unsafe_allow_html=True,
)

batch_mode = st.toggle("📦 Batch mode — analyze multiple resumes against one job description")

up_col1, up_col2 = st.columns(2)

with up_col1:
    st.markdown('<div class="upload-slot">', unsafe_allow_html=True)
    st.markdown('<div class="upload-slot-title">📄 Job Description</div>', unsafe_allow_html=True)
    st.markdown('<div class="upload-slot-caption">PDF, DOCX, or TXT — drag & drop or browse</div>',
                unsafe_allow_html=True)
    jd_file = st.file_uploader("Job Description", type=["pdf", "docx", "txt"],
                                key="jd_upload", label_visibility="collapsed")
    if jd_file:
        st.markdown(f'<div class="upload-status-ok">✅ {jd_file.name} ready</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="upload-status-pending">Waiting for upload...</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with up_col2:
    st.markdown('<div class="upload-slot">', unsafe_allow_html=True)
    if batch_mode:
        st.markdown('<div class="upload-slot-title">👥 Resumes (multiple)</div>', unsafe_allow_html=True)
        st.markdown('<div class="upload-slot-caption">PDF, DOCX, or TXT — drag & drop or browse</div>',
                    unsafe_allow_html=True)
        resume_files = st.file_uploader("Resumes", type=["pdf", "docx", "txt"],
                                         accept_multiple_files=True, key="resume_upload_multi",
                                         label_visibility="collapsed")
        if resume_files:
            st.markdown(f'<div class="upload-status-ok">✅ {len(resume_files)} resume(s) ready</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown('<div class="upload-status-pending">Waiting for upload(s)...</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="upload-slot-title">👤 Resume</div>', unsafe_allow_html=True)
        st.markdown('<div class="upload-slot-caption">PDF, DOCX, or TXT — drag & drop or browse</div>',
                    unsafe_allow_html=True)
        single_file = st.file_uploader("Resume", type=["pdf", "docx", "txt"],
                                        key="resume_upload_single", label_visibility="collapsed")
        resume_files = [single_file] if single_file else []
        if single_file:
            st.markdown(f'<div class="upload-status-ok">✅ {single_file.name} ready</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="upload-status-pending">Waiting for upload...</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with st.expander("🎛️ Scoring Weights", expanded=False):
    tfidf_weight = st.slider("Text Similarity Weight", 0.0, 1.0, 0.5, 0.05)
    skill_weight = round(1.0 - tfidf_weight, 2)
    st.caption(f"Skill Match Weight: {skill_weight}")

files_ready = bool(jd_file) and bool(resume_files) and all(resume_files)

analyze_clicked = st.button(
    "🔍 Analyze Now" if files_ready else "🔍 Upload both files to continue",
    type="primary",
    use_container_width=True,
    disabled=not files_ready,
)

st.markdown('</div>', unsafe_allow_html=True)  # close workflow-card

# ===================================================================
# ANALYSIS
# ===================================================================
if analyze_clicked:
    progress_bar = st.progress(0, text="Starting analysis...")
    steps = [
        "Uploading files...",
        "Extracting Resume(s)...",
        "Extracting Job Description...",
        "Finding Skills...",
        "Computing TF-IDF Similarity...",
        "Analyzing Skill Gap...",
        "Generating Interview Questions...",
        "Preparing Dashboard...",
    ]
    for i, step in enumerate(steps):
        progress_bar.progress((i + 1) / len(steps), text=step)
        time.sleep(0.12)
    progress_bar.progress(1.0, text="Done.")
    time.sleep(0.2)
    progress_bar.empty()

    jd_text, jd_error = safe_extract(jd_file)
    if jd_error:
        st.error(f"Job description error: {jd_error}")
        st.stop()

    jd_mismatch_warning = looks_like_wrong_upload(jd_text, expected="jd")
    if jd_mismatch_warning:
        st.warning(f"⚠️ {jd_mismatch_warning}")

    # ---------------- BATCH MODE ----------------
    if batch_mode:
        results = []
        for f in resume_files:
            resume_text, err = safe_extract(f)
            if err:
                st.warning(f"Skipped **{f.name}**: {err}")
                continue

            mismatch = looks_like_wrong_upload(resume_text, expected="resume")
            if mismatch:
                st.warning(f"⚠️ **{f.name}**: {mismatch}")

            try:
                match_result, gap_result, _ = cached_full_analysis(resume_text, jd_text, tfidf_weight, skill_weight)
                info = extract_candidate_info(resume_text)
                score = match_result["hybrid_score_percentage"]
                recommendation = (
                    "Strongly Recommend" if score >= 80
                    else "Recommend after Interview" if score >= 60
                    else "Needs Upskilling"
                )
                row = {
                    "Candidate": info["name"] if info["name"] != "Not Available" else f.name,
                    "File": f.name,
                    "Overall Match (%)": score,
                    "Skill Match (%)": match_result["skill_match_percentage"],
                    "TF-IDF (%)": match_result["tfidf_similarity_percentage"],
                    "Readiness": gap_result["readiness_level"],
                    "Recommendation": recommendation,
                    "Email": info["email"],
                }
                results.append(row)
                st.session_state.analysis_history.append({**row, "Timestamp": datetime.now().strftime("%H:%M:%S")})
            except Exception as e:
                st.warning(f"Could not analyze **{f.name}**: {e}")

        if not results:
            st.error("No resumes could be analyzed successfully.")
            st.stop()

        st.success(f"Analyzed {len(results)} candidate(s)!")
        df = pd.DataFrame(results).sort_values("Overall Match (%)", ascending=False).reset_index(drop=True)
        df.insert(0, "Rank", range(1, len(df) + 1))

        st.subheader("🏆 Candidate Leaderboard")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            search_term = st.text_input("🔎 Search by candidate name")
        with col_s2:
            readiness_options = ["All"] + sorted(df["Readiness"].unique().tolist())
            readiness_filter = st.selectbox("Filter by Readiness", readiness_options)

        display_df = df.copy()
        if search_term:
            display_df = display_df[display_df["Candidate"].str.contains(search_term, case=False, na=False)]
        if readiness_filter != "All":
            display_df = display_df[display_df["Readiness"] == readiness_filter]

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Export Leaderboard as CSV", data=csv_bytes,
                            file_name="candidate_leaderboard.csv", mime="text/csv")

    # ---------------- SINGLE MODE ----------------
    else:
        resume_text, err = safe_extract(resume_files[0])
        if err:
            st.error(f"Resume error: {err}")
            st.stop()

        resume_mismatch = looks_like_wrong_upload(resume_text, expected="resume")
        if resume_mismatch:
            st.warning(f"⚠️ {resume_mismatch}")

        try:
            match_result, gap_result, question_set = cached_full_analysis(
                resume_text, jd_text, tfidf_weight, skill_weight
            )
        except Exception as e:
            st.error(f"Analysis failed: {e}")
            st.stop()

        candidate_info = extract_candidate_info(resume_text)
        readiness = gap_result["readiness_level"]

        st.session_state.analysis_history.append({
            "Candidate": candidate_info["name"],
            "File": resume_files[0].name,
            "Overall Match (%)": match_result["hybrid_score_percentage"],
            "Skill Match (%)": match_result["skill_match_percentage"],
            "TF-IDF (%)": match_result["tfidf_similarity_percentage"],
            "Readiness": readiness,
            "Timestamp": datetime.now().strftime("%H:%M:%S"),
        })

        st.success("Analysis complete!")

        st.markdown(f"""
            <div class="candidate-card fade-in">
                <h4>👤 {candidate_info['name']}</h4>
                <div class="candidate-field">📧 <b>Email:</b> {candidate_info['email']}</div>
                <div class="candidate-field">📞 <b>Phone:</b> {candidate_info['phone']}</div>
                <div class="candidate-field">📍 <b>Location:</b> {candidate_info['location']}</div>
                <div class="candidate-field">💻 <b>GitHub:</b> {candidate_info['github']}</div>
                <div class="candidate-field">🔗 <b>LinkedIn:</b> {candidate_info['linkedin']}</div>
                <div class="candidate-field">🌐 <b>Portfolio:</b> {candidate_info['portfolio']}</div>
            </div>
        """, unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Overall Match", f"{match_result['hybrid_score_percentage']}%")
        c2.metric("Skill Match", f"{match_result['skill_match_percentage']}%")
        c3.metric("Text Similarity", f"{match_result['tfidf_similarity_percentage']}%")
        readiness_css = READINESS_CSS_CLASS.get(readiness, "")
        c4.markdown(f"**Readiness**<br><span class='{readiness_css}'>{readiness}</span>",
                    unsafe_allow_html=True)
        st.caption(gap_result["readiness_description"])

        st.markdown("---")
        render_executive_summary(candidate_info, match_result, gap_result)
        st.markdown("---")

        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.subheader("Score Overview")
            st.plotly_chart(build_gauge_chart(match_result["hybrid_score_percentage"]), use_container_width=True)
        with chart_col2:
            st.subheader("Skill Breakdown")
            st.plotly_chart(
                build_donut_chart(gap_result["matched_count"], gap_result["missing_count"],
                                   len(gap_result["additional_skills"])),
                use_container_width=True,
            )

        chart_col3, chart_col4 = st.columns(2)
        with chart_col3:
            st.subheader("Skills by Category")
            st.plotly_chart(
                build_category_bar_chart(gap_result["categorized_matching_skills"],
                                          gap_result["categorized_missing_skills"]),
                use_container_width=True,
            )
        with chart_col4:
            st.subheader("Resume vs JD Coverage")
            st.plotly_chart(build_radar_chart(resume_text, jd_text), use_container_width=True)

        st.markdown("---")
        st.subheader("🏷️ Skills")
        col_left, col_mid, col_right = st.columns(3)
        with col_left:
            st.markdown("**✅ Matching**")
            render_badges(gap_result["matching_skills"], "badge-match", gap_result["categorized_matching_skills"])
        with col_mid:
            st.markdown("**❌ Missing**")
            render_badges(gap_result["missing_skills"], "badge-missing", gap_result["categorized_missing_skills"])
        with col_right:
            st.markdown("**➕ Additional**")
            render_badges(gap_result["additional_skills"], "badge-extra")

        st.markdown("---")
        st.subheader("🎯 Priority Learning Roadmap")
        render_roadmap_cards(gap_result["priority_recommendations"])

        st.markdown("---")
        st.subheader("❓ Suggested Interview Questions")
        render_interview_section(question_set)

        st.markdown("---")
        st.subheader("⬇️ Download Full Report")
        report_txt = generate_txt_report(candidate_info, match_result, gap_result, question_set)
        report_json = generate_json_report(candidate_info, match_result, gap_result, question_set)

        dl_col1, dl_col2 = st.columns(2)
        with dl_col1:
            st.download_button(
                "📄 Download TXT Report", data=report_txt,
                file_name=f"{candidate_info['name'].replace(' ', '_')}_report.txt",
                mime="text/plain", use_container_width=True,
            )
        with dl_col2:
            st.download_button(
                "🗂️ Download JSON Report", data=report_json,
                file_name=f"{candidate_info['name'].replace(' ', '_')}_report.json",
                mime="application/json", use_container_width=True,
            )

# ===================================================================
# SESSION HISTORY
# ===================================================================
if st.session_state.analysis_history:
    st.markdown("---")
    with st.expander(f"🕘 Session History ({len(st.session_state.analysis_history)} analyses)"):
        hist_df = pd.DataFrame(st.session_state.analysis_history)
        st.dataframe(hist_df, use_container_width=True, hide_index=True)
        hist_csv = hist_df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Export Session History as CSV", data=hist_csv,
                            file_name="session_history.csv", mime="text/csv")