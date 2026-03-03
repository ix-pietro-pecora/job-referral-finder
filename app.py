import os
import resend
import streamlit as st
from dotenv import load_dotenv
from db import add_subscription, unsubscribe
from discovery.resolver import resolve

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")
FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")
APP_URL = "https://friend-job-referral-finder.streamlit.app"

st.set_page_config(page_title="Job Referral Finder", page_icon="🔍")

# Handle unsubscribe via query param
params = st.query_params
if "unsubscribe" in params:
    email = params["unsubscribe"]
    try:
        unsubscribe(email)
        st.success(f"You've been unsubscribed. You won't receive any more emails at {email}.")
    except Exception as e:
        st.error(f"Something went wrong: {e}")
    st.stop()


def send_confirmation_email(email: str, target_role: str, supported: list, unsupported: list) -> None:
    supported_rows = "".join(
        f"<li style='margin:4px 0'>✓ {c}</li>" for c in supported
    )
    unsupported_rows = "".join(
        f"<li style='margin:4px 0; color:#9CA3AF'>✗ {c} — unsupported job board</li>" for c in unsupported
    )
    unsupported_section = f"""
        <p style='margin-top:16px;margin-bottom:4px;font-weight:600;color:#DC2626'>
            Companies we couldn't find ({len(unsupported)}):
        </p>
        <ul style='margin:0;padding-left:20px'>{unsupported_rows}</ul>
        <p style='color:#9CA3AF;font-size:12px;margin-top:8px'>
            These companies may use Workday or a custom job board we don't support yet.
        </p>
    """ if unsupported else ""

    html = f"""
    <div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px">
        <h2 style="margin-bottom:4px">You're subscribed to Job Referral Finder</h2>
        <p style="color:#6B7280;margin-top:0">
            We'll email you daily when new <strong>{target_role}</strong> roles open up at your watched companies.
        </p>
        <p style='margin-bottom:4px;font-weight:600'>
            Companies we're monitoring ({len(supported)}):
        </p>
        <ul style='margin:0;padding-left:20px'>{supported_rows}</ul>
        {unsupported_section}
        <hr style="border:none;border-top:1px solid #E5E7EB;margin:24px 0">
        <p style="color:#9CA3AF;font-size:12px">
            Job Referral Finder · <a href="{APP_URL}?unsubscribe={email}" style="color:#9CA3AF">Unsubscribe</a>
        </p>
    </div>
    """
    try:
        resend.Emails.send({
            "from": FROM_EMAIL,
            "to": email,
            "subject": f"You're subscribed — here's what we're monitoring",
            "html": html,
        })
    except Exception:
        pass  # Don't block signup if confirmation email fails


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

    background = st.text_input(
        "Your background (optional but recommended)",
        placeholder="e.g. B2B SaaS PM, 5 years total experience, 2 years in PM — no director or principal roles",
        help="Helps us filter out roles you're over or under-qualified for.",
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
            add_subscription(email, companies, target_role, background)
            st.success(
                f"You're subscribed! We'll email **{email}** daily with "
                f"**{target_role}** roles."
            )

            # Resolve each company and show coverage
            with st.spinner("Checking which companies we can monitor..."):
                supported = []
                unsupported = []
                for company in companies:
                    if resolve(company):
                        supported.append(company)
                    else:
                        unsupported.append(company)

            if supported:
                st.markdown("**Monitoring these companies:**")
                for c in supported:
                    st.markdown(f"✓ &nbsp; {c}")

            if unsupported:
                st.markdown("**Couldn't find a job board for:**")
                for c in unsupported:
                    st.markdown(f"✗ &nbsp; {c}")
                st.warning(
                    "These companies may use Workday or a custom job board we don't support yet. "
                    "You won't receive alerts for them."
                )

            send_confirmation_email(email, target_role, supported, unsupported)

        except Exception as e:
            st.error(f"Something went wrong: {e}")

st.divider()
st.caption("Built with Claude AI")
