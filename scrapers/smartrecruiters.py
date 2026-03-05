import re
import requests


def fetch_jobs(slug: str) -> list[dict]:
    """
    Fetch all jobs from a company's SmartRecruiters board.
    Returns a list of dicts with: title, location, url, description.
    """
    listing_url = f"https://api.smartrecruiters.com/v1/companies/{slug}/postings"
    try:
        r = requests.get(listing_url, params={"limit": 100}, timeout=10)
        r.raise_for_status()
        data = r.json()
    except (requests.RequestException, ValueError):
        return []

    jobs = []
    for posting in data.get("content", []):
        uuid = posting.get("uuid", "")
        title = posting.get("name", "")
        loc = posting.get("location", {})
        location = loc.get("fullLocation", "") or loc.get("city", "")

        dept = posting.get("department", {}).get("label", "")
        exp = posting.get("experienceLevel", {}).get("label", "")
        description = " | ".join(filter(None, [dept, exp]))

        jobs.append({
            "title": title,
            "location": location,
            "url": f"https://jobs.smartrecruiters.com/{slug}/{posting.get('id', '')}",
            "description": description,
            "_uuid": uuid,
        })
    return jobs


def fetch_description(slug: str, uuid: str) -> str:
    """Fetch full description for a single posting. Called on-demand."""
    return _fetch_description(slug, uuid)


def _fetch_description(slug: str, uuid: str) -> str:
    if not uuid:
        return ""
    url = f"https://api.smartrecruiters.com/v1/companies/{slug}/postings/{uuid}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
    except (requests.RequestException, ValueError):
        return ""

    sections = data.get("jobAd", {}).get("sections", {})
    parts = []
    for key in ("jobDescription", "qualifications", "additionalInformation"):
        text = sections.get(key, {}).get("text", "")
        if text:
            parts.append(_strip_html(text))
    return " ".join(parts)


def _strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()
