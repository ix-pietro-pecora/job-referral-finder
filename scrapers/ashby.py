import requests
import re


def fetch_jobs(slug: str) -> list[dict]:
    """
    Fetch all jobs from a company's Ashby board.
    Returns a list of dicts with: title, location, url, description.
    """
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
    except (requests.RequestException, ValueError):
        return []

    jobs = []
    for job in data.get("jobs", []):
        jobs.append({
            "title": job.get("title", ""),
            "location": job.get("location", ""),
            "url": job.get("jobUrl", ""),
            "description": _strip_html(job.get("descriptionHtml", "") or job.get("descriptionPlain", "")),
        })
    return jobs


def _strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()
