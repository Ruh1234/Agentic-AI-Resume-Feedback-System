# 🤖 Agentic Resume Feedback System

This is an AI-powered resume intelligence system that analyzes resumes, identifies skill gaps, and helps users improve their career readiness using LLMs and web scraping.

---

## 🚀 Key Features

### 📄 Resume Intelligence
- Parses uploaded PDF resumes
- Validates resume structure using LLM + web standards
- Identifies strengths, weaknesses, and missing keywords

### 🎯 Job Role Intelligence (NEW)
- Automatically extracts potential job roles from your resume
- Uses AI to infer suitable career paths without requiring manual input
- Finds **real job and internship listings** based on your resume content
- Prioritizes roles from platforms like:
  - LinkedIn Jobs
  - Indeed
  - Greenhouse
  - Lever

### 🔍 Smart Job Search Engine
- Scrapes live job postings using SerpApi + Google Jobs API
- Returns **actual apply links (not blog posts or generic search pages)**
- Filters listings based on extracted job roles

### 📚 Learning Path Generator
- Detects missing technical skills
- Recommends:
  - Open-source projects
  - Certifications
  - Skill-building resources

### 📝 Cover Letter Generator
- Generates ATS-optimized cover letters
- Uses real 2026 cover letter structures from web scraping
- Tailors content to both resume and job description

---

## 🧠 AI Capabilities
- LLM-based resume understanding (Ollama / Llama3.2)
- Job role inference without user input
- Context-aware career recommendations

---

## 🛠 Tech Stack
- Python
- Streamlit
- Ollama (LLM)
- SerpApi
- DuckDuckGo Search
- PyPDF2

---

## ▶️ How to Run

```bash
pip install -r requirements.txt
streamlit run FinalProject.py