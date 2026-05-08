import streamlit as st
import ollama
import requests
from PyPDF2 import PdfReader
from ddgs import DDGS

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Resume Feedback System", page_icon="🤖", layout="wide")

# --- 2. API KEYS ---
# Replace with your actual SerpApi key
from dotenv import load_dotenv
load_dotenv()
SERPAPI_KEY = "your_actual_key"
# --- 3. CUSTOM STYLING ---
st.markdown("""
    <style>
    .stFileUploader { width: 60%; margin: 0 auto; }
    .stTextInput, .stTextArea { width: 60%; margin: 0 auto; }
    .stSuccess, .stError, .stInfo { width: 60%; margin: 0 auto; padding: 10px; }
    .stChatMessage { width: 80%; margin: 0 auto; }
    h1 { text-align: center; }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 Resume Feedback System")

# --- 4. INITIALIZE SESSION STATE ---
if "step" not in st.session_state:
    st.session_state.step = "get_major"

if "major" not in st.session_state:
    st.session_state.major = ""

if "job_desc" not in st.session_state:
    st.session_state.job_desc = ""

if "resume_text" not in st.session_state:
    st.session_state.resume_text = None

if "audit_report" not in st.session_state:
    st.session_state.audit_report = ""

if "messages" not in st.session_state:
    st.session_state.messages = []


# --- 5. AGENTIC HELPER FUNCTIONS ---

def serpapi_search(query):
    params = {
        "engine": "google",
        "q": query,
        "api_key": SERPAPI_KEY,
        "num": 5
    }

    try:
        response = requests.get(
            "https://serpapi.com/search.json",
            params=params
        )

        data = response.json()

        results = data.get("organic_results", [])

        return [
            {
                "title": r.get('title'),
                "link": r.get('link'),
                "snippet": r.get('snippet')
            }
            for r in results
        ]

    except Exception:
        return []


def get_learning_path(audit_text):

    with st.status("🚀 Curating your learning path...", expanded=True) as status:

        status.write("🧠 Identifying key technical skill gaps...")

        extract_resp = ollama.chat(
            model='llama3.2',
            messages=[
                {
                    'role': 'system',
                    'content': 'Identify exactly 2 technical skills missing. Reply with comma-separated values ONLY.'
                },
                {
                    'role': 'user',
                    'content': audit_text
                }
            ]
        )

        skills = extract_resp['message']['content'].split(',')

        recommendations = "### 📚 Recommended Projects & Certifications\n"

        for skill in skills:

            skill = skill.strip()

            status.write(f"🔍 Searching Google for: **{skill}**")

            cert_results = serpapi_search(
                f"best professional {skill} certification 2026"
            )

            proj_results = serpapi_search(
                f"beginner {skill} open source projects github"
            )

            recommendations += f"\n#### 🎯 {skill}\n"
            recommendations += "**Top Certifications:**\n"

            for r in cert_results:
                recommendations += f"* [{r['title']}]({r['link']}) - {r['snippet'][:150]}...\n"

            recommendations += "**Suggested Projects:**\n"

            for r in proj_results:
                recommendations += f"* [{r['title']}]({r['link']}) - {r['snippet'][:150]}...\n"

        status.update(
            label="Learning Path Generated!",
            state="complete"
        )

        return recommendations


def generate_cover_letter():

    with st.status("📝 Scraping 2026 templates & drafting letter...") as status:

        with DDGS() as ddgs:
            templates = "\n".join(
                [
                    r['body']
                    for r in ddgs.text(
                        "2026 general professional cover letter templates",
                        max_results=2
                    )
                ]
            )

        prompt = f"""
        Draft a high-impact cover letter.

        MAJOR:
        {st.session_state.major}

        JOB DESCRIPTION:
        {st.session_state.job_desc}

        RESUME CONTEXT:
        {st.session_state.resume_text[:2000]}

        STYLE TEMPLATES:
        {templates}

        TASK:
        Write a 3-paragraph professional letter.
        """

        response = ollama.chat(
            model='llama3.2',
            messages=[{'role': 'user', 'content': prompt}]
        )

        return response['message']['content']


def find_top_jobs():

    with st.status("🔍 Finding jobs based on your resume...", expanded=True) as status:
        prompt = f"""
                Analyze this resume carefully.

                TASK:
                Identify:

                1. 5 DIVERSE job roles this candidate qualifies for
                2. 8 technical skills

                IMPORTANT:
                - Roles must be different from each other
                - Include internships, entry-level, hardware, software,
                  research, systems, CAD, embedded, simulation,
                  controls, and engineering-related roles when relevant
                - Avoid repeating similar titles

                FORMAT EXACTLY:

                ROLES: role1, role2, role3, role4, role5
                SKILLS: skill1, skill2, skill3, skill4,
                        skill5, skill6, skill7, skill8

                Resume:
                {st.session_state.resume_text[:3000]}
                """

        resp = ollama.chat(
            model="llama3.2",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        text = resp["message"]["content"]

        roles = []
        skills = []

        for line in text.split("\n"):

            if line.startswith("ROLES:"):
                roles = [
                    r.strip()
                    for r in line.replace("ROLES:", "").split(",")
                    if r.strip()
                ]

            if line.startswith("SKILLS:"):
                skills = [
                    s.strip()
                    for s in line.replace("SKILLS:", "").split(",")
                    if s.strip()
                ]

            # ---------------------------------------------------
            # FALLBACK ROLES
            # ---------------------------------------------------

        if not roles:
            roles = [
                "Electrical Engineer",
                "Embedded Systems Engineer",
                "Hardware Engineer",
                "Controls Engineer",
                "CAD Engineer"
            ]

        status.write(f"🎯 Roles Found: {roles}")
        status.write(f"🛠 Skills Found: {skills}")

        # ---------------------------------------------------
        # STEP 2 → Build diverse queries
        # ---------------------------------------------------

        query_templates = [
            "{} internship",
            "{} intern",
            "{} entry level",
            "junior {}",
            "{} new grad",
            "{} co-op"
        ]

        queries = []

        for role in roles:

            for template in query_templates:
                queries.append(
                    template.format(role)
                )

        # Add skill-based searches
        for skill in skills[:4]:
            queries.extend([
                f"{skill} internship",
                f"{skill} engineer",
            ])

        # Remove duplicates
        queries = list(set(queries))

        status.write(f"🔎 Total Queries: {len(queries)}")

        # ---------------------------------------------------
        # STEP 3 → Search ALL queries
        # ---------------------------------------------------

        all_jobs = []

        for query in queries:

            status.write(f"🔍 Searching: {query}")

            try:

                response = requests.get(
                    "https://serpapi.com/search.json",
                    params={
                        "engine": "google_jobs",
                        "q": query,
                        "hl": "en",
                        "location": "United States",
                        "api_key": SERPAPI_KEY
                    }
                )

                data = response.json()

                jobs = data.get("jobs_results", [])

                if jobs:

                    for job in jobs:
                        job["search_query"] = query

                    all_jobs.extend(jobs)

            except Exception as e:

                status.write(f"❌ Error searching {query}")

        # ---------------------------------------------------
        # STEP 4 → Fallback if nothing found
        # ---------------------------------------------------

        if not all_jobs:

            fallback_queries = [
                "embedded systems internship",
                "hardware engineering internship",
                "electronics engineering intern",
                "controls engineering internship",
                "firmware engineering intern",
                "CAD engineering internship"
            ]

            for query in fallback_queries:

                try:

                    response = requests.get(
                        "https://serpapi.com/search.json",
                        params={
                            "engine": "google_jobs",
                            "q": query,
                            "hl": "en",
                            "location": "United States",
                            "api_key": SERPAPI_KEY
                        }
                    )

                    jobs = response.json().get("jobs_results", [])

                    if jobs:

                        for job in jobs:
                            job["search_query"] = query

                        all_jobs.extend(jobs)

                except:
                    pass

        if not all_jobs:
            return "❌ No job listings found."

        # ---------------------------------------------------
        # STEP 5 → Remove duplicates intelligently
        # ---------------------------------------------------

        unique_jobs = []

        seen = set()

        for job in all_jobs:

            title = job.get("title", "").strip().lower()

            company = job.get(
                "company_name",
                ""
            ).strip().lower()

            # Simplified title
            short_title = " ".join(title.split()[:3])

            key = (short_title, company)

            if key not in seen:
                seen.add(key)

                unique_jobs.append(job)

        # ---------------------------------------------------
        # STEP 6 → Diversify results
        # ---------------------------------------------------

        diversified_jobs = []

        used_categories = set()

        for job in unique_jobs:

            title = job.get("title", "").lower()

            category = title.split()[0]

            if category not in used_categories:
                used_categories.add(category)

                diversified_jobs.append(job)

        # If not enough diversified jobs,
        # add remaining jobs

        if len(diversified_jobs) < 10:

            for job in unique_jobs:

                if job not in diversified_jobs:
                    diversified_jobs.append(job)

                if len(diversified_jobs) >= 15:
                    break

        # ---------------------------------------------------
        # STEP 7 → Format Output
        # ---------------------------------------------------

        output = "## 🎯 Top Job Listings\n"

        for idx, job in enumerate(diversified_jobs[:15], start=1):

            title = job.get("title", "No title")

            company = job.get(
                "company_name",
                "Unknown company"
            )

            location = job.get(
                "location",
                "Unknown location"
            )

            via_query = job.get(
                "search_query",
                "Unknown"
            )

            # ---------------------------------------------------
            # APPLY LINK LOGIC
            # ---------------------------------------------------

            apply_link = None

            related_links = job.get(
                "related_links",
                []
            )

            if related_links and isinstance(related_links, list):
                first_link = related_links[0]

                apply_link = first_link.get("link")

            if not apply_link:
                apply_link = job.get("share_link")

            if not apply_link:
                search_query = f"{title} {company} jobs"

                apply_link = (
                        "https://www.google.com/search?q="
                        + search_query.replace(" ", "+")
                )

            output += f"""
        ### {idx}. {title}

        🏢 **Company:** {company}  
        📍 **Location:** {location}  
        🔎 **Matched Via:** {via_query}

        🔗 [Apply Here]({apply_link})

        ---
        """

        status.update(
            label="✅ Diverse Jobs Found",
            state="complete"
        )

        return output


def identify_and_validate(resume_text, user_major):

    with st.status("Agentic Analysis in progress...", expanded=True) as status:

        status.write("🔬 Analyzing document DNA...")

        analysis_prompt = f"""
        Identify document type.
        Start with 'TYPE: [Type]'.

        TEXT:
        {resume_text[:3000]}
        """

        class_resp = ollama.chat(
            model='llama3.2',
            messages=[
                {
                    'role': 'user',
                    'content': analysis_prompt
                }
            ]
        )

        if "TYPE: RESUME" not in class_resp['message']['content'].upper():
            return False, class_resp['message']['content']

        status.write(f"🌐 Scraping {user_major} standards...")

        with DDGS() as ddgs:

            search_context = "\n".join(
                [
                    r['body']
                    for r in ddgs.text(
                        f"required resume skills for {user_major} 2026",
                        max_results=2
                    )
                ]
            )

        status.write("⚖️ Validating content...")

        val_prompt = f"""
        Major:
        {user_major}

        Standards:
        {search_context}

        Resume:
        {resume_text[:2500]}

        Reply [PASS] or [FAIL] with reasons.
        """

        check_resp = ollama.chat(
            model='llama3.2',
            messages=[
                {
                    'role': 'user',
                    'content': val_prompt
                }
            ]
        )

        return (
            True,
            check_resp['message']['content']
        ) if "[PASS]" in check_resp['message']['content'] else (
            False,
            check_resp['message']['content']
        )


# --- 6. LOGIC FLOW ---

if st.session_state.step == "get_major":

    with st.chat_message("assistant"):
        st.markdown(
            "Hello! I'm your AI Resume Agent. "
            "First, **what is your major?**"
        )

    major_input = st.text_input(
        "Enter major:",
        key="maj_input"
    )

    if st.button("Submit Major", type="primary"):

        if major_input:

            st.session_state.major = major_input
            st.session_state.step = "upload_resume"

            st.rerun()

elif st.session_state.step == "upload_resume":

    with st.chat_message("assistant"):
        st.markdown(
            f"**{st.session_state.major}** detected. "
            f"Please upload your resume (PDF)."
        )

    uploaded_file = st.file_uploader(
        "Upload PDF",
        type="pdf",
        label_visibility="collapsed"
    )

    if uploaded_file:

        reader = PdfReader(uploaded_file)

        text = "".join(
            [
                page.extract_text()
                for page in reader.pages
            ]
        )

        is_valid, feedback = identify_and_validate(
            text,
            st.session_state.major
        )

        if is_valid is True:

            st.session_state.resume_text = text
            st.session_state.step = "get_job_desc"

            st.rerun()

        else:
            st.error(f"Validation Failed: {feedback}")

elif st.session_state.step == "get_job_desc":

    with st.chat_message("assistant"):
        st.markdown(
            "Resume verified! Now, paste the **Job Description**."
        )

    job_input = st.text_area(
        "Paste JD here:",
        height=200,
        key="jd_input"
    )

    if st.button("Submit Job Description", type="primary"):

        if job_input.strip():

            st.session_state.job_desc = job_input
            st.session_state.step = "confirm_analyze"

            st.rerun()

        else:
            st.warning("Please provide a job description.")

elif st.session_state.step == "confirm_analyze":

    with st.chat_message("assistant"):
        st.markdown(
            "Job description received! "
            "Do you want your resume analyzed? "
            "If so, please type **resume analyze** below."
        )

    confirm_input = st.text_input(
        "Type here:",
        key="confirm_trigger"
    )

    if st.button("Analyze", type="primary"):

        if confirm_input.lower().strip() == "resume analyze":

            with st.status("🕵️ Auditing Fit...") as status:

                audit_prompt = f"""
                Analyze:
                - Strengths
                - Weaknesses
                - Missing Keywords
                - Summary

                RESUME:
                {st.session_state.resume_text}

                JD:
                {st.session_state.job_desc}
                """

                audit_resp = ollama.chat(
                    model='llama3.2',
                    messages=[
                        {
                            'role': 'user',
                            'content': audit_prompt
                        }
                    ]
                )

                st.session_state.audit_report = audit_resp['message']['content']

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": f"### 📊 Audit Report\n\n{st.session_state.audit_report}"
                    }
                )

                st.session_state.step = "ask_recommendations"

            st.rerun()

        else:
            st.error(
                "Please type 'resume analyze' exactly to proceed."
            )

elif st.session_state.step == "ask_recommendations":

    with st.chat_message("assistant"):

        st.markdown(st.session_state.audit_report)

        st.markdown("---")

        st.markdown(
            "Would you like me to find "
            "**specific projects and certifications** "
            "using SerpApi?"
        )

    col1, col2 = st.columns([1, 4])

    with col1:

        if st.button(
            "Yes, help me!",
            type="primary",
            key="yes_recs"
        ):

            recs = get_learning_path(
                st.session_state.audit_report
            )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": recs
                }
            )

            st.session_state.step = "ask_cover_letter"

            st.rerun()

    with col2:

        if st.button(
            "No, skip recommendations",
            key="no_recs"
        ):

            st.session_state.step = "ask_cover_letter"

            st.rerun()

elif st.session_state.step == "ask_cover_letter":

    for m in st.session_state.messages:
        st.chat_message(m["role"]).markdown(m["content"])

    if st.button("Yes Cover Letter"):

        cl = generate_cover_letter()

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": cl
            }
        )

        st.session_state.step = "ask_job_search"

        st.rerun()

    if st.button("No Cover Letter"):

        st.session_state.step = "ask_job_search"

        st.rerun()

elif st.session_state.step == "ask_job_search":

    for m in st.session_state.messages:
        st.chat_message(m["role"]).markdown(m["content"])

    if st.button("Yes Show Jobs"):

        st.session_state.step = "job_search"

        st.rerun()

    if st.button("No Finish"):

        st.session_state.step = "end_chat"

        st.rerun()

elif st.session_state.step == "job_search":

    for m in st.session_state.messages:
        st.chat_message(m["role"]).markdown(m["content"])

    st.chat_message("assistant").markdown("Finding jobs...")

    jobs = find_top_jobs()

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": jobs
        }
    )

    st.session_state.step = "show_jobs"

    st.rerun()

elif st.session_state.step == "show_jobs":

    for m in st.session_state.messages:
        st.chat_message(m["role"]).markdown(m["content"])

    if st.button("Finish"):

        st.session_state.step = "end_chat"

        st.rerun()

elif st.session_state.step == "end_chat":

    for m in st.session_state.messages:
        st.chat_message(m["role"]).markdown(m["content"])

    st.success("Session Complete ✅")

    if st.button("Restart"):

        st.session_state.clear()

        st.rerun()

elif st.session_state.step == "chat_mode":

    for msg in st.session_state.messages:

        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask about specific skills..."):

        st.session_state.messages.append(
            {
                "role": "user",
                "content": prompt
            }
        )

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):

            placeholder = st.empty()

            full_res = ""

            chat_context = [
                {
                    'role': 'system',
                    'content': (
                        f'Recruiter. '
                        f'Major: {st.session_state.major}. '
                        f'JD: {st.session_state.job_desc}'
                    )
                }
            ] + st.session_state.messages

            response = ollama.chat(
                model='llama3.2',
                messages=chat_context,
                stream=True
            )

            for chunk in response:

                full_res += chunk['message']['content']

                placeholder.markdown(full_res + "▌")

            placeholder.markdown(full_res)

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": full_res
                }
            )

with st.sidebar:

    if st.button("Restart Session"):

        st.session_state.clear()

        st.rerun()