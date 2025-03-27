import streamlit as st
st.set_page_config(
    page_title="ResumeATS Pro",
    layout="wide",
    page_icon="📄",
    initial_sidebar_state="expanded"
)

# -------------------- #
#      CSS Styling      #
# -------------------- #
st.markdown("""
    <style>
    :root {
        --primary: #2563eb;
        --secondary: #1e40af;
        --background: #f8fafc;
        --text: #1e293b;
        --success: #16a34a;
        --error: #dc2626;
        --warning: #d97706;
    }

    html {
        font-family: 'Inter', sans-serif;
    }

    .main {
        background-color: var(--background);
    }
    
    /* Input Styling */
    .stTextInput input, .stTextArea textarea {
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
        transition: all 0.3s ease;
    }

    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1) !important;
    }

    /* Button Styling */
    .stButton>button {
        background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        color: white !important;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        border: none;
        transition: all 0.3s ease;
    }

    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    /* Card Styling */
    .custom-card {
        background: white;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #e2e8f0;
        margin-bottom: 24px;
    }

    /* Progress Bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, var(--primary) 0%, var(--secondary) 100%);
        border-radius: 4px;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        background: #f1f5f9 !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        transition: all 0.3s ease;
    }

    .stTabs [aria-selected="true"] {
        background: var(--primary) !important;
        color: white !important;
    }

    /* History Cards */
    .history-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #e2e8f0;
        transition: transform 0.2s ease;
    }

    .history-card:hover {
        transform: translateY(-2px);
    }

    /* Section Headers */
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: var(--primary);
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid var(--primary);
    }
    </style>
""", unsafe_allow_html=True)

# -------------------- #
#    Dependencies      #
# -------------------- #
import configparser
import os
from dotenv import load_dotenv
import google.generativeai as genai
from PyPDF2 import PdfReader
import re
from collections import Counter
import hashlib
import plotly.graph_objects as go
import numpy as np
from database import init_db, create_user, verify_user, get_data
import time
from datetime import datetime
import json

import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager  # ✅ Use ChromeDriverManager

# Initialize database
init_db()

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'pdf_text' not in st.session_state:
    st.session_state.pdf_text = None

# -------------------- #
#  Authentication UI   #
# -------------------- #
def show_auth_ui():
    with st.container():
        col1, col2 = st.columns([1, 1], gap="large")
        
        with col1:
            st.markdown("""
                <div style="text-align: center; margin-bottom: 40px;">
                    <h1 style="color: var(--primary); margin-bottom: 16px;">📄 ResumeATS Pro</h1>
                    <p style="color: var(--text); font-size: 1.1rem;">
                        AI-Powered Career Success Platform
                    </p>
                </div>
            """, unsafe_allow_html=True)

            tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])

            with tab1:
                with st.form("login_form"):
                    st.subheader("Welcome Back!")
                    login_email = st.text_input("Email Address", key="login_email")
                    login_password = st.text_input("Password", type="password", key="login_password")

                    if st.form_submit_button("Login →", use_container_width=True):
                        if verify_user(login_email, login_password):
                            st.session_state.authenticated = True
                            st.session_state.username = login_email
                            st.session_state.password = login_password
                            st.rerun()
                        else:
                            st.error("Invalid credentials")

            with tab2:
                with st.form("signup_form"):
                    st.subheader("Get Started")
                    new_email = st.text_input("Work Email", key="new_email")
                    new_username = st.text_input("Full Name", key="new_username")
                    new_password = st.text_input("Create Password", type="password", key="new_password")
                    confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")

                    if st.form_submit_button("Create Account →", use_container_width=True):
                        if new_password != confirm_password:
                            st.error("Passwords do not match")
                        elif len(new_password) < 8:
                            st.error("Password must be at least 8 characters")
                        else:
                            if create_user(new_username, new_password, new_email):
                                st.success("Account created! Please login")
                            else:
                                st.error("Email already exists")

        with col2:
            st.info("Extra content here.")
def get_driver():
    """ Initialize Selenium WebDriver in headless mode. """
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")  # ✅ Required for Streamlit Cloud
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        service = Service(ChromeDriverManager().install())  # ✅ Auto-install ChromeDriver
        driver = webdriver.Chrome(service=service, options=options)
        
        return driver
    except Exception as e:
        st.error(f"WebDriver Error: {e}")
        return None  # Prevent crashes if WebDriver fails


# -------------------- #
#   Main Application    #
# -------------------- #
if not st.session_state.authenticated:
    show_auth_ui()
else:
    # Sidebar Navigation
    with st.sidebar:
        st.markdown(f"""
            <div style="text-align: center; margin-bottom: 32px;">
                <h3 style="color: var(--primary); margin-bottom: 8px;">{st.session_state.username}</h3>
                <div style="font-size: 0.9rem; color: #64748b;">Professional Account</div>
            </div>
        """, unsafe_allow_html=True)
        
        feature = st.radio(
            "Navigation",
            ["📄 Resume Analysis", "🤖 Auto Apply", "📋 Application History"],
            index=0,
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.rerun()

    # Feature Handling
    if feature == "📄 Resume Analysis":
        st.markdown('<div class="section-header">AI Resume Analysis</div>', unsafe_allow_html=True)
        
        with st.container():
            col1, col2 = st.columns([1, 2], gap="large")
            
            with col1:
                with st.container():
                    st.markdown("### Upload Resume")
                    upload_file = st.file_uploader("", type=["pdf"], label_visibility="collapsed")
                    
                    st.markdown("### Job Description")
                    use_jd = st.checkbox("Enable job description analysis", value=True)
                    job_description = st.text_area(
                        "Paste job description here",
                        height=200,
                        disabled=not use_jd,
                        placeholder="Enter job description..."
                    )
                    
                    analysis_option = st.selectbox(
                        "Analysis Type",
                        ["🚀 Quick Scan", "🔍 Detailed Analysis", "🎯 ATS Optimization"],
                        index=0
                    )
                    
                    if st.button("Start Analysis", use_container_width=True):
                        if upload_file is not None:
                            try:
                                pdf_reader = PdfReader(upload_file)
                                st.session_state.pdf_text = "".join([page.extract_text() for page in pdf_reader.pages])
                                st.success("Resume processed successfully!")
                            except Exception as e:
                                st.error(f"Error processing PDF: {str(e)}")
                        else:
                            st.error("Please upload a resume to analyze")

            with col2:
                if 'pdf_text' in st.session_state and st.session_state.pdf_text:
                    # Load environment variables and configure API
                    load_dotenv()
                    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
                    model = genai.GenerativeModel("gemini-pro")

                    # Original scoring functions
                    def calculate_keyword_match(text, keywords):
                        text = text.lower()
                        found_keywords = sum(1 for keyword in keywords if keyword.lower() in text)
                        return (found_keywords / len(keywords)) * 100 if keywords else 0

                    def normalize_score(score):
                        return min(max(score, 0), 100)

                    class ATSScoreComponents:
                        def _init_(self):
                            self.format_score = 0
                            self.content_score = 0
                            self.keyword_score = 0
                            self.match_score = 0
                            self.total_score = 0

                    def calculate_base_ats_score(pdf_text, job_description=None):
                        score_components = ATSScoreComponents()
                        
                        # Original scoring logic
                        sections = ['experience', 'education', 'skills']
                        for section in sections:
                            if section in pdf_text.lower():
                                score_components.format_score += 10
                        
                        if len(re.findall(r'[^\x00-\x7F]', pdf_text)) == 0:
                            score_components.format_score += 5
                        if len(re.findall(r'[^\S\n]{2,}', pdf_text)) == 0:
                            score_components.format_score += 5

                        action_verbs = ['achieved', 'implemented', 'developed', 'managed', 'created', 'increased']
                        score_components.keyword_score = calculate_keyword_match(pdf_text, action_verbs)
                        score_components.content_score = score_components.keyword_score * 0.2

                        if job_description:
                            job_terms = set(re.findall(r'\b\w+\b', job_description.lower()))
                            resume_terms = set(re.findall(r'\b\w+\b', pdf_text.lower()))
                            score_components.match_score = len(job_terms.intersection(resume_terms)) / len(job_terms) * 30
                            score_components.content_score += score_components.match_score
                        else:
                            score_components.content_score += 30 if len(pdf_text.split()) > 200 else 15

                        score_components.total_score = normalize_score(score_components.format_score + score_components.content_score)
                        return score_components

                    # Generate analysis
                    prompt = f"""
                    Analyze this resume and provide detailed insights:
                    {st.session_state.pdf_text}
                    {f'Job Description: {job_description}' if use_jd else ''}
                    """
                    
                    try:
                        with st.spinner("Generating AI analysis..."):
                            response = model.generate_content(prompt)
                            score_components = calculate_base_ats_score(st.session_state.pdf_text, job_description if use_jd else None)
                            
                            with st.expander("View Full Analysis", expanded=True):
                                st.markdown(f"""
                                    <div class="custom-card">
                                        {response.text}
                                    </div>
                                """, unsafe_allow_html=True)
                            
                            # Original visualization logic
                            st.markdown("### ATS Compatibility Score")
                            st.progress(score_components.total_score/100)
                            st.caption(f"ATS Score: {score_components.total_score}/100")
                            
                            # Original radar chart
                            categories = list(['Resume Structure', 'Content Quality', 'Keyword Match'])
                            values = [
                                normalize_score(score_components.format_score * 2.5),
                                normalize_score(score_components.content_score * 1.67),
                                score_components.keyword_score
                            ]
                            
                            if use_jd:
                                categories.append('Job Description Match')
                                values.append(normalize_score(score_components.match_score * 3.33))
                            
                            fig = go.Figure()
                            fig.add_trace(go.Scatterpolar(
                                r=values,
                                theta=categories,
                                fill='toself',
                                name='Score Components'
                            ))
                            fig.update_layout(
                                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                                showlegend=False,
                                height=400
                            )
                            st.plotly_chart(fig, use_container_width=True)
                            
                    except Exception as e:
                        st.error(f"Analysis failed: {str(e)}")

    elif feature == "🤖 Auto Apply":
        st.markdown('<div class="section-header">Smart Job Applications</div>', unsafe_allow_html=True)
        
        # Original Auto Apply logic
        st.subheader("Automatically Apply to Jobs on Naukri.com")
        auto_apply_resume = st.file_uploader("Upload Resume for Auto Apply", type=["pdf"], key="auto_apply_resume")
        
        if auto_apply_resume:
            def read_pdf(uploaded_file):
                if uploaded_file is not None:
                    pdf_reader = PdfReader(uploaded_file)
                    return "".join([page.extract_text() for page in pdf_reader.pages])
                raise FileNotFoundError("No file uploaded")
            st.session_state.pdf_text = read_pdf(auto_apply_resume)
            
        if 'pdf_text' not in st.session_state or not st.session_state.pdf_text:
            st.error("Please upload a resume first")
            st.stop()

        with st.form("auto_apply_form"):
            cols = st.columns(3)
            with cols[0]:
                st.markdown("*Job Preferences*")
                job_type = st.selectbox("Job Type", ["job", "internship"], index=0)
                designation_input = st.text_input("Designation (comma separated)")
                location_input = st.text_input("Location (comma separated)")
                
            with cols[1]:
                st.markdown("*Requirements*")
                yoe = st.number_input("Years of Experience", min_value=0, step=1)
                salary = st.number_input("Expected Salary", min_value=0)
                max_pages = st.number_input("Max Pages to Search", min_value=1, step=1)
                
            with cols[2]:
                st.markdown("*Optimization*")
                max_applications = st.number_input("Max Applications per Day", min_value=1, step=1)
                min_match_score = st.number_input("Minimum Match Score", min_value=0.0, max_value=1.0, step=0.1, value=0.0)
                
            if st.form_submit_button("Start Auto Apply", use_container_width=True):
                designations = [d.strip() for d in designation_input.split(",") if d.strip()]
                locations = [l.strip() for l in location_input.split(",") if l.strip()]

                # Original Selenium automation logic
                def login_naukri(driver, wait, credentials):
                    driver.get('https://login.naukri.com/')
                    try:
                        wait.until(EC.presence_of_element_located((By.ID, 'usernameField'))).send_keys(credentials['email'])
                        wait.until(EC.presence_of_element_located((By.ID, 'passwordField'))).send_keys(credentials['password'])
                        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Login']"))).click()
                    except Exception as e:
                        st.error(f"Login failed: {str(e)}")

                def construct_url_for_combo(designation, location, job_type, page):
                    base_url = "https://www.naukri.com"
                    designation_slug = designation.lower().replace(' ', '-')
                    location_slug = location.lower().replace(' ', '-') if location else ""
                    
                    if job_type == "internship":
                        if location_slug:
                            url = f"{base_url}/{designation_slug}-internship-jobs-in-{location_slug}-{page}" if page > 1 else f"{base_url}/{designation_slug}-internship-jobs-in-{location_slug}"
                        else:
                            url = f"{base_url}/internship/{designation_slug}-internship-jobs-{page}" if page > 1 else f"{base_url}/{designation_slug}-internship-jobs"
                    else:
                        if location_slug:
                            url = f"{base_url}/{designation_slug}-jobs-in-{location_slug}-{page}" if page > 1 else f"{base_url}/{designation_slug}-jobs-in-{location_slug}"
                        else:
                            url = f"{base_url}/{designation_slug}-jobs-{page}" if page > 1 else f"{base_url}/{designation_slug}-jobs"
                    return url

                def construct_search_urls(designations, locations, job_type, max_pages):
                    urls = []
                    for designation in designations:
                        if locations:
                            for location in locations:
                                for page in range(1, max_pages + 1):
                                    url = construct_url_for_combo(designation, location, job_type, page)
                                    urls.append(url)
                        else:
                            for page in range(1, max_pages + 1):
                                url = construct_url_for_combo(designation, "", job_type, page)
                                urls.append(url)
                    return urls

                def scrape_job_links(driver, wait, designations, locations, job_type, max_pages):
                    job_links = []
                    urls = construct_search_urls(designations, locations, job_type, max_pages)
                    for url in urls:
                        driver.get(url)
                        try:
                            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "span[title='Close']"))).click()
                        except Exception:
                            pass
                        try:
                            jobs = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.title")))
                            for job in jobs:
                                job_url = job.get_attribute('href')
                                if job_url and job_url not in job_links:
                                    job_links.append(job_url)
                        except TimeoutException:
                            pass
                    return job_links

                def extract_job_skills(driver, wait):
                    info = {'skill': [], 'yoe': 0, 'salary': [], 'company_name': "Unknown", 'designation': "Unknown"}
                    try:
                        parent_div = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.styles_key-skill_GIPn")))
                        child_div = parent_div.find_element(By.XPATH, ".//div[not(@class)]")
                        skill_spans = child_div.find_elements(By.TAG_NAME, "span")
                        info['skill'] = [span.text.strip().lower() for span in skill_spans if span.text.strip()]
                    except Exception:
                        pass
                    # Original extraction logic continues...
                    return info

                def skills_match(job_skills, user_skills):
                    if not job_skills:
                        return 0
                    count = sum(1 for sk in job_skills if sk in user_skills)
                    return (count / len(job_skills)) * 100

                def apply_to_jobs(driver, wait, job_links, max_applications, yoe, salary, user_skills, min_match_score, expected_domain):
                    applied = 0
                    failed = []
                    for job_url in job_links:
                        if applied >= max_applications:
                            break
                        driver.get(job_url)
                        try:
                            driver.find_element(By.XPATH, "//div[contains(text(), 'Applied')]")
                            continue
                        except NoSuchElementException:
                            pass
                        job_text = extract_job_skills(driver, wait)
                        if yoe < job_text['yoe'] or salary > job_text['salary'][1]:
                            continue
                        match_percentage = skills_match(job_text['skill'], user_skills)
                        if match_percentage < min_match_score * 100:
                            continue
                        try:
                            apply_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Apply')]")))
                            apply_btn.click()
                            current_url = driver.current_url
                            if expected_domain not in current_url:
                                driver.back()
                                continue
                            try:
                                submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Submit')]")))
                                submit_btn.click()
                                applied += 1
                                data = {
                                    'CompanyName': job_text['company_name'],
                                    'Designation': job_text['designation'],
                                    'Status': 'Pending',
                                    'Time': time.time()
                                }
                                # Original data logging logic
                                try:
                                    with open("data.json", "r") as f:
                                        existing_data = json.load(f)
                                        existing_data.append(data)
                                    with open("data.json", "w") as f:
                                        json.dump(existing_data, f)
                                except:
                                    with open("data.json", "w") as f:
                                        json.dump([data], f)
                            except Exception:
                                pass
                        except Exception as e:
                            failed.append(job_url)
                    return applied, failed

                def extract_skills_from_resume():
                    prompt = "Extract technical skills from this resume:"
                    response = genai.GenerativeModel("gemini-pro").generate_content([st.session_state.pdf_text, prompt])
                    return [skill.lower() for skill in response.text.split(", ")]

                def main():
                    credentials = {'email': st.session_state.username, 'password': st.session_state.password}
                    user_skills = extract_skills_from_resume()
                    options = webdriver.EdgeOptions()
                    options.add_argument("--disable-blink-features=AutomationControlled")
                    service = Service(st.session_state.edgedriver_path)
                    driver = webdriver.Edge(service=service, options=options)
                    wait = WebDriverWait(driver, 20)
                    
                    try:
                        login_naukri(driver, wait, credentials)
                        job_links = scrape_job_links(driver, wait, designations, locations, job_type, max_pages)
                        if job_links:
                            applied_count, _ = apply_to_jobs(driver, wait, job_links, max_applications, yoe, salary, user_skills, min_match_score, "naukri.com")
                            st.success(f"Successfully applied to {applied_count} positions!")
                    finally:
                        driver.quit()

                main()

    elif feature == "📋 Application History":
        st.markdown('<div class="section-header">Application History</div>', unsafe_allow_html=True)
        
        try:
            with open("data.json", "r") as f:
                data = json.load(f)
                entries = data if isinstance(data, list) else [data]
                
                if not entries:
                    st.markdown("""
                        <div class="custom-card" style="text-align: center;">
                            <h3>No applications found</h3>
                            <p>Your application history will appear here</p>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    for entry in entries:
                        timestamp = entry.get('Time', time.time())
                        applied_time = datetime.fromtimestamp(timestamp).strftime('%b %d, %Y %I:%M %p')
                        status_color = "var(--success)" if entry.get('Status') == "Success" else "var(--error)"
                        
                        st.markdown(f"""
                            <div class="history-card">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                                    <h3 style="margin: 0; color: var(--primary);">{entry.get('CompanyName', 'Unknown Company')}</h3>
                                    <span style="font-size: 0.9rem; color: #64748b;">{applied_time}</span>
                                </div>
                                <div style="display: flex; gap: 24px; color: var(--text);">
                                    <div>
                                        <p style="margin: 0; font-size: 0.9rem;">Position</p>
                                        <p style="margin: 0; font-weight: 500;">{entry.get('Designation', 'N/A')}</p>
                                    </div>
                                    <div>
                                        <p style="margin: 0; font-size: 0.9rem;">Status</p>
                                        <p style="margin: 0; color: {status_color}; font-weight: 500;">{entry.get('Status', 'Pending')}</p>
                                    </div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                        
        except FileNotFoundError:
            st.warning("No application history found")
        except json.JSONDecodeError:
            st.error("Error reading application history")
