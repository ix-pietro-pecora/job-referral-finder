import re
import requests


def fetch_jobs(slug: str) -> list[dict]:
    """
    Fetch all jobs from a company's Workable board.
    Returns a list of dicts with: title, location, url, description.
    """
    url = f"https://apply.workable.com/api/v3/accounts/{slug}/jobs"
    try:
        r = requests.post(url, json={}, headers={"Content-Type": "application/json"}, timeout=10)
        r.raise_for_status()
        data = r.json()
    except (requests.RequestException, ValueError):
        return []

    jobs = []
    for posting in data.get("results", []):
        title = posting.get("title", "")
        loc = posting.get("location", {})
        location_parts = filter(None, [loc.get("city"), loc.get("region"), loc.get("country")])
        location = ", ".join(location_parts) if loc else ""

        dept = posting.get("department", [])
        dept_str = ", ".join(dept) if isinstance(dept, list) else str(dept or "")
        workplace = posting.get("workplace", "") or ""
        description = " | ".join(filter(None, [dept_str, workplace]))

        shortcode = posting.get("shortcode", "")
        job_url = f"https://apply.workable.com/{slug}/j/{shortcode}/" if shortcode else ""

        jobs.append({
            "title": title,
            "location": location,
            "url": job_url,
            "description": description,
        })
    return jobs
