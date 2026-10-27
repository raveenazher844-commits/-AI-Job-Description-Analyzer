
import json
import streamlit as st
from main import analyze_job

st.set_page_config(
    page_title="AI Job Description Analyzer",
    page_icon="💼",
    layout="wide",
)

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #10172a, #202449);
    color: #ffffff;
}
h1, h2, h3, p, label {
    color: #ffffff !important;
}
.hero {
    padding: 24px;
    border-radius: 18px;
    background: linear-gradient(120deg, #5145cd, #a13ec8);
    margin-bottom: 24px;
}
.panel {
    padding: 18px;
    border: 1px solid #50557c;
    border-radius: 14px;
    background: rgba(255,255,255,0.06);
    margin-bottom: 14px;
}
.tag {
    display: inline-block;
    background: #343b70;
    color: white;
    padding: 7px 12px;
    border-radius: 18px;
    margin: 4px;
    font-size: 14px;
}
.stButton > button {
    background: #7956e8;
    color: white;
    border-radius: 10px;
    border: none;
    min-height: 45px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <h1>💼 AI Job Description Analyzer</h1>
    <p>Powered by LangGraph and Groq AI</p>
    <p>Extract job details, classify roles, analyze skills,
    and generate a structured hiring report.</p>
</div>
""", unsafe_allow_html=True)

st.subheader("📝 Enter Job Description")

description = st.text_area(
    "Paste the complete job description below:",
    height=230,
    placeholder=(
        "Example: We are hiring a Python Developer with "
        "2 years of experience in Python, FastAPI, SQL..."
    ),
)

if st.button("🚀 Analyze Job Description", use_container_width=True):
    if not description.strip():
        st.error("Please enter a job description first.")
    elif len(description.strip()) < 30:
        st.warning("Please enter a more detailed job description.")
    else:
        try:
            with st.spinner(
                "AI is extracting information and analyzing skills..."
            ):
                report = analyze_job(description)

            st.session_state["job_report"] = report
            st.success("Job analysis completed successfully!")

        except Exception as exc:
            st.error(
                "Analysis failed. Check your Groq API key, internet "
                "connection, model availability, and terminal error."
            )
            with st.expander("Technical error details"):
                st.code(str(exc))

if "job_report" in st.session_state:
    report = st.session_state["job_report"]

    st.divider()
    st.header("📊 Structured Hiring Report")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 🎯 Job Title")
        st.write(report.get("job_title", "Not specified"))

    with col2:
        st.markdown("#### 🏢 Company")
        st.write(report.get("company_name", "Not specified"))

    with col3:
        st.markdown("#### 📂 Category")
        st.write(report.get("job_category", "Not specified"))

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("📌 Job Details")

    st.write(
        "**Experience:**",
        report.get("required_experience", "Not specified"),
    )
    st.write(
        "**Employment Type:**",
        report.get("employment_type", "Not specified"),
    )
    st.write(
        "**Work Mode:**",
        report.get("work_mode", "Not specified"),
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.subheader("🛠️ Technical Skills")
    technical = report.get("technical_skills", [])
    if technical:
        st.markdown(
            "".join(
                f'<span class="tag">{str(skill).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")}</span>'
                for skill in technical
            ),
            unsafe_allow_html=True,
        )
    else:
        st.info("No technical skills were identified.")

    st.subheader("🤝 Soft Skills")
    soft = report.get("soft_skills", [])
    if soft:
        st.markdown(
            "".join(
                f'<span class="tag">{str(skill).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")}</span>'
                for skill in soft
            ),
            unsafe_allow_html=True,
        )
    else:
        st.info("No soft skills were identified.")

    st.subheader("⭐ Top 3 Most Important Skills")
    top_skills = report.get("top_3_skills", [])
    if top_skills:
        for number, skill in enumerate(top_skills[:3], start=1):
            st.write(f"**{number}.** {skill}")
    else:
        st.info("No priority skills were identified.")

    st.divider()
    st.subheader("📥 Export Report")

    json_data = json.dumps(report, indent=4, ensure_ascii=False)

    st.download_button(
        label="⬇️ Download Hiring Report (JSON)",
        data=json_data,
        file_name="hiring_report.json",
        mime="application/json",
        use_container_width=True,
    )

    with st.expander("View Complete JSON"):
        st.json(report)

st.divider()
st.caption("AI Job Description Analyzer | Built with Python, Streamlit, Groq and LangGraph")
