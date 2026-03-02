import requests


def fetch_jobs(slug: str) -> list[dict]:
    """
    Fetch all jobs from a company's Lever board.
    Returns a list of dicts with: title, location, url, description.
    """
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
    except (requests.RequestException, ValueError):
        return []

    jobs = []
    for job in data:
        categories = job.get("categories", {})
        description_parts = [
            job.get("descriptionPlain", ""),
            job.get("additionalPlain", ""),
        ]
        jobs.append({
            "title": job.get("text", ""),
            "location": categories.get("location", ""),
            "url": job.get("hostedUrl", ""),
            "description": " ".join(p for p in description_parts if p),
        })
    return jobs
