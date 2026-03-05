import re
import requests


def fetch_jobs(slug: str) -> list[dict]:
    """
    Fetch all jobs from a company's Gem job board.
    Returns a list of dicts with: title, location, url, description.
    """
    url = f"https://api.gem.com/job_board/v0/{slug}/job_posts/"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
    except (requests.RequestException, ValueError):
        return []

    jobs = []
    for job in data:
        jobs.append({
            "title": job.get("title", ""),
            "location": job.get("location", {}).get("name", ""),
            "url": job.get("absolute_url", ""),
            "description": job.get("content_plain", "") or _strip_html(job.get("content", "")),
        })
    return jobs


def _strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()
