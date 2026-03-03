import os
import streamlit as st
from dotenv import load_dotenv
from db import add_subscription

load_dotenv()

st.set_page_config(page_title="Job Referral Finder", page_icon="🔍")

st.title("🔍 Job Referral Finder")
st.caption(
    "Get a daily email with open roles at companies where you have connections — "
    "so you can ask for a referral at the right time."
)

st.divider()

with st.form("subscribe_form"):
    email = st.text_input("Your email address")

    target_role = st.text_input(
        "What role are you looking for?",
        placeholder="e.g. Product Manager, Software Engineer, Designer",
    )

    companies_raw = st.text_area(
        "Companies to watch",
        placeholder="Stripe\nAirbnb\nNotion\nVercel",
        help="One company per line, or comma-separated.",
        height=140,
    )

    submitted = st.form_submit_button("Subscribe — send me daily job alerts →", type="primary")

if submitted:
    companies = [
        c.strip()
        for c in companies_raw.replace(",", "\n").splitlines()
        if c.strip()
    ]

    if not email or not target_role or not companies:
        st.error("Please fill in all three fields before subscribing.")
    elif "@" not in email:
        st.error("Please enter a valid email address.")
    else:
        try:
            add_subscription(email, companies, target_role)
            st.success(
                f"You're subscribed! We'll email **{email}** daily with "
                f"**{target_role}** roles at: {', '.join(companies)}."
            )
            st.info("It can take up to 24 hours for your first email — we run the job search every night.")
        except Exception as e:
            st.error(f"Something went wrong: {e}")

st.divider()
st.caption("Built with Claude AI · [Unsubscribe](mailto:unsubscribe@yourdomain.com)")
