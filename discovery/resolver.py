from __future__ import annotations
import json
import re
import requests
from pathlib import Path

KNOWN_COMPANIES_PATH = Path(__file__).parent / "known_companies.json"

with open(KNOWN_COMPANIES_PATH) as f:
    KNOWN_COMPANIES = json.load(f)


def _normalize(name: str) -> str:
    """Lowercase, strip punctuation and spaces."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _probe_greenhouse(slug: str) -> bool:
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
    try:
        r = requests.get(url, timeout=5)
        return r.status_code == 200
    except requests.RequestException:
        return False


def _probe_lever(slug: str) -> bool:
    url = f"https://api.lever.co/v0/postings/{slug}"
    try:
        r = requests.get(url, timeout=5)
        return r.status_code == 200
    except requests.RequestException:
        return False


def resolve(company_name: str) -> dict | None:
    """
    Given a company name, return its ATS info.
    Returns: {"ats": "greenhouse"|"lever", "slug": str} or None if unresolvable.
    """
    slug = _normalize(company_name)

    # Tier 1: known lookup
    if slug in KNOWN_COMPANIES:
        return KNOWN_COMPANIES[slug]

    # Tier 2: API probe
    if _probe_greenhouse(slug):
        return {"ats": "greenhouse", "slug": slug}
    if _probe_lever(slug):
        return {"ats": "lever", "slug": slug}

    return None
