import re
import requests


def fetch_jobs(slug: str, base_url: str = "", board_name: str = "") -> list[dict]:
    """
    Fetch jobs from a company's Workday career site.
    Requires the full base_url (e.g. 'https://netflix.wd1.myworkdayjobs.com')
    and board_name (e.g. 'Netflix').
    Returns a list of dicts with: title, location, url, description.
    """
    if not base_url or not board_name:
        return []

    api_url = f"{base_url}/wday/cxs/{slug}/{board_name}/jobs"
    PAGE_SIZE = 20
    MAX_PAGES = 5
    all_postings = []

    for page in range(MAX_PAGES):
        try:
            r = requests.post(
                api_url,
                json={"limit": PAGE_SIZE, "offset": page * PAGE_SIZE, "appliedFacets": {}},
                headers={"Content-Type": "application/json"},
                timeout=15,
            )
            r.raise_for_status()
            data = r.json()
        except (requests.RequestException, ValueError):
            break

        postings = data.get("jobPostings", [])
        all_postings.extend(postings)
        if len(postings) < PAGE_SIZE:
            break

    jobs = []
    for posting in all_postings:
        title = posting.get("title", "")
        location = posting.get("locationsText", "")
        path = posting.get("externalPath", "")
        job_url = f"{base_url}/{board_name}{path}" if path else ""

        bullet_fields = posting.get("bulletFields", [])
        description = " | ".join(bullet_fields) if bullet_fields else ""

        jobs.append({
            "title": title,
            "location": location,
            "url": job_url,
            "description": description,
            "_path": path,
        })
    return jobs


def fetch_description(base_url: str, slug: str, board_name: str, path: str) -> str:
    """Fetch full description for a single posting. Called on-demand."""
    return _fetch_description(base_url, slug, board_name, path)


def _fetch_description(base_url: str, slug: str, board_name: str, path: str) -> str:
    if not path:
        return ""
    url = f"{base_url}/wday/cxs/{slug}/{board_name}{path}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
    except (requests.RequestException, ValueError):
        return ""

    info = data.get("jobPostingInfo", {})
    desc = info.get("jobDescription", "")
    return _strip_html(desc) if desc else ""


def _strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()
