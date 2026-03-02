import requests


def fetch_jobs(slug: str) -> list[dict]:
    """
    Fetch all jobs from a company's Greenhouse board.
    Returns a list of dicts with: title, location, url, description.
    """
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
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
            "location": job.get("location", {}).get("name", ""),
            "url": job.get("absolute_url", ""),
            "description": _strip_html(job.get("content", "")),
        })
    return jobs


def _strip_html(html: str) -> str:
    """Remove HTML tags for cleaner text passed to Claude."""
    import re
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()
