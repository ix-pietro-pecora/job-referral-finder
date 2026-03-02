import os
import streamlit as st
from dotenv import load_dotenv

from discovery.resolver import resolve
from scrapers import greenhouse, lever
from claude_client.ranker import filter_and_rank, score_with_resume
from utils.resume_parser import extract_text

load_dotenv()

st.set_page_config(page_title="Job Referral Finder", page_icon="🔍", layout="wide")

st.title("🔍 Job Referral Finder")
st.caption("Find open roles at companies where you have connections — so you can ask for a referral.")

# ── Inputs ────────────────────────────────────────────────────────────────────

col1, col2 = st.columns(2)

with col1:
    target_role = st.text_input(
        "What role are you targeting?",
        placeholder="e.g. Product Manager, Software Engineer, Designer",
    )

with col2:
    companies_input = st.text_input(
        "Which companies do you want to check?",
        placeholder="e.g. Stripe, Airbnb, Notion, Vercel",
    )

resume_file = st.file_uploader(
    "Upload your resume (optional — enables personalized match scores)",
    type=["pdf"],
)

search = st.button("Find Roles", type="primary", disabled=not (target_role and companies_input))

# ── Search ────────────────────────────────────────────────────────────────────

if search:
    company_names = [c.strip() for c in companies_input.split(",") if c.strip()]
    resume_text = ""

    if resume_file:
        resume_text = extract_text(resume_file.read())

    all_jobs = []
    unresolved = []

    progress = st.progress(0, text="Looking up job boards...")

    for i, company in enumerate(company_names):
        progress.progress((i) / len(company_names), text=f"Checking {company}...")
        info = resolve(company)

        if info is None:
            unresolved.append(company)
            continue

        if info["ats"] == "greenhouse":
            jobs = greenhouse.fetch_jobs(info["slug"])
        elif info["ats"] == "lever":
            jobs = lever.fetch_jobs(info["slug"])
        else:
            jobs = []

        for job in jobs:
            job["company"] = company

        all_jobs.extend(jobs)

    progress.progress(1.0, text="Asking Claude to filter matches...")

    matched = filter_and_rank(all_jobs, target_role)

    if resume_text and matched:
        matched = score_with_resume(matched, resume_text)

    progress.empty()

    # ── Results ───────────────────────────────────────────────────────────────

    if unresolved:
        st.warning(
            f"Couldn't find job boards for: **{', '.join(unresolved)}**. "
            "Try checking their careers page manually or add them to `known_companies.json`."
        )

    if not matched:
        st.info("No matching roles found. Try broadening your role description or adding more companies.")
    else:
        st.success(f"Found **{len(matched)} matching role{'s' if len(matched) != 1 else ''}** across {len(company_names) - len(unresolved)} companies.")

        for job in matched:
            with st.expander(f"**{job['company'].title()}** — {job['title']}  |  {job.get('location', 'Location N/A')}"):
                if resume_text and "match_score" in job:
                    score = job["match_score"]
                    color = "green" if score >= 70 else "orange" if score >= 40 else "red"
                    st.markdown(f"**Resume match: :{color}[{score}/100]** — {job.get('score_reason', '')}")

                    if job.get("talking_points"):
                        st.markdown("**Highlight in your referral ask:**")
                        for point in job["talking_points"]:
                            st.markdown(f"- {point}")

                elif job.get("match_note"):
                    st.markdown(f"_{job['match_note']}_")

                st.markdown(f"[View job posting →]({job['url']})")
