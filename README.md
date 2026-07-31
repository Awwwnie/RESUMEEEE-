# RESUMEEEE-

# AI Resume Shortlisting & Skill Analysis Platform

An AI-powered platform that evaluates candidate resumes against job descriptions, providing suitability scores, detecting skill gaps, and generating interview questions. Built as a proof-of-concept for integration into a university placement portal.

---

## ✨ Features

- Resume & Job Description Parsing (PDF, DOCX, TXT)
- Technical Skill Extraction using a categorized skills taxonomy
- Hybrid Suitability Scoring (TF-IDF + Skill Match)
- Configurable scoring weights
- Skill Gap Analysis
- Personalized Learning Roadmap
- AI-generated Interview Questions
- Batch Resume Analysis
- Interactive Dashboard with charts and analytics
- Export reports in TXT, JSON, and CSV formats

---

## 🛠 Tech Stack

### Backend
- Python
- scikit-learn
- Regex-based Skill Extraction

### Frontend
- Streamlit
- Plotly

### File Parsing
- pypdf
- python-docx

---

## 📁 Project Structure

```text
RESUMEEEE-/
├── app.py
├── extractor.py
├── matcher.py
├── skills.py
├── gap_analyzer.py
├── questions.py
├── data/
│   └── skills_db.json
├── sample_data/
├── tests/
├── requirements.txt
└── README.md
```

---

## 🚀 Running Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## 🧪 Running Tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```

---

## 🎯 Future Roadmap

- PDF report generation
- Resume improvement suggestions
- Learning resource recommendations
- Recruiter dashboard
- University placement portal integration
- FastAPI/Django backend
- Authentication and user accounts

---

## 👩‍💻 Author

**Aditi Tripathy**

B.Tech Computer Science (AI & ML)  
Sri Sri University
