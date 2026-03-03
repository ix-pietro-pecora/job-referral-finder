"""
Nightly job scraper — run by GitHub Actions cron.
Fetches jobs for every active subscription and sends a digest email via Resend.
"""
from __future__ import annotations
import os
import resend
from dotenv import load_dotenv

from db import get_all_subscriptions, get_sent_urls, mark_jobs_sent
from discovery.resolver import resolve
from scrapers import greenhouse, lever, ashby
from claude_client.ranker import filter_and_rank

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")
FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")


def scrape_companies(companies: list, target_role: str) -> tuple[list, list]:
    """Return (matched_jobs, unresolved_companies)."""
    all_jobs = []
    unresolved = []

    for company in companies:
        info = resolve(company)
        if info is None:
            unresolved.append(company)
            continue

        if info["ats"] == "greenhouse":
            jobs = greenhouse.fetch_jobs(info["slug"])
        elif info["ats"] == "lever":
            jobs = lever.fetch_jobs(info["slug"])
        elif info["ats"] == "ashby":
            jobs = ashby.fetch_jobs(info["slug"])
        else:
            jobs = []

        for job in jobs:
            job["company"] = company
        all_jobs.extend(jobs)

    matched = filter_and_rank(all_jobs, target_role)
    return matched, unresolved


APP_URL = "https://friend-job-referral-finder.streamlit.app"


def build_email_html(target_role: str, jobs: list, unresolved: list, email: str = "") -> str:
    rows = ""
    for job in jobs:
        note = f"<br><span style='color:#6B7280;font-size:13px'>{job['match_note']}</span>" if job.get("match_note") else ""
        location = f" · {job['location']}" if job.get("location") else ""
        rows += f"""
        <div style="margin-bottom:20px;padding:14px 16px;border-left:3px solid #4F46E5;background:#F9FAFB;border-radius:4px">
          <div style="font-weight:600">{job['company'].title()} — {job['title']}</div>
          <div style="color:#6B7280;font-size:13px;margin:2px 0">{location}</div>
          {note}
          <a href="{job['url']}" style="display:inline-block;margin-top:8px;color:#4F46E5;font-size:13px">View job →</a>
        </div>
        """

    unresolved_note = ""
    if unresolved:
        unresolved_note = f"""
        <p style="color:#9CA3AF;font-size:12px;margin-top:24px">
          Couldn't find job boards for: {', '.join(unresolved)}.<br>
          These may use an unsupported ATS — check their careers page manually.
        </p>
        """

    return f"""
    <div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px">
      <h2 style="margin-bottom:4px">Your daily {target_role} matches</h2>
      <p style="color:#6B7280;margin-top:0">Found <strong>{len(jobs)} role{'s' if len(jobs) != 1 else ''}</strong> at your watched companies today.</p>
      {rows}
      {unresolved_note}
      <hr style="border:none;border-top:1px solid #E5E7EB;margin:24px 0">
      <p style="color:#9CA3AF;font-size:12px">Job Referral Finder · <a href="{APP_URL}?unsubscribe={email}" style="color:#9CA3AF">Unsubscribe</a></p>
    </div>
    """


def process_subscription(sub: dict) -> None:
    email = sub["email"]
    companies = sub["companies"]
    target_role = sub["target_role"]

    print(f"  Processing {email} — {target_role} at {companies}")

    matched, unresolved = scrape_companies(companies, target_role)

    already_sent = get_sent_urls(email)
    new_jobs = [j for j in matched if j["url"] not in already_sent]

    if not new_jobs:
        print(f"  No new matches for {email} — skipping email.")
        return

    html = build_email_html(target_role, new_jobs, unresolved, email)

    resend.Emails.send({
        "from": FROM_EMAIL,
        "to": email,
        "subject": f"{len(new_jobs)} new {target_role} role{'s' if len(new_jobs) != 1 else ''} at your watched companies",
        "html": html,
    })

    mark_jobs_sent(email, [j["url"] for j in new_jobs])
    print(f"  ✓ Sent {len(new_jobs)} new matches to {email}")


def main() -> None:
    subs = get_all_subscriptions()
    print(f"Running nightly job scraper — {len(subs)} active subscription(s)")

    for sub in subs:
        try:
            process_subscription(sub)
        except Exception as e:
            print(f"  ✗ Error for {sub.get('email')}: {e}")

    print("Done.")


if __name__ == "__main__":
    main()
