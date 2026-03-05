from __future__ import annotations
import json
import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
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


def _probe_ashby(slug: str) -> bool:
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
    try:
        r = requests.get(url, timeout=5)
        return r.status_code == 200
    except requests.RequestException:
        return False


def _probe_gem(slug: str) -> bool:
    url = f"https://api.gem.com/job_board/v0/{slug}/job_posts/"
    try:
        r = requests.get(url, timeout=5)
        return r.status_code == 200
    except requests.RequestException:
        return False


def _probe_workable(slug: str) -> bool:
    url = f"https://apply.workable.com/api/v3/accounts/{slug}/jobs"
    try:
        r = requests.post(url, json={}, headers={"Content-Type": "application/json"}, timeout=5)
        return r.status_code == 200 and r.json().get("total", 0) > 0
    except (requests.RequestException, ValueError):
        return False


def _probe_smartrecruiters(slug: str) -> bool:
    url = f"https://api.smartrecruiters.com/v1/companies/{slug}/postings"
    try:
        r = requests.get(url, params={"limit": 1}, timeout=5)
        return r.status_code == 200
    except requests.RequestException:
        return False


WORKDAY_INSTANCES = range(1, 16)
WORKDAY_BOARD_TEMPLATES = [
    "{slug}",
    "{Slug}",
    "Careers",
    "External",
    "External_Career_Site",
    "{Slug}_Careers",
    "{slug}_careers",
    "en",
]


def _probe_workday(slug: str) -> dict | None:
    """Brute-force Workday tenant + board name in parallel. Returns config dict or None."""
    capitalized = slug.capitalize()
    boards = [
        t.format(slug=slug, Slug=capitalized) for t in WORKDAY_BOARD_TEMPLATES
    ]

    def _try(wd, board):
        url = f"https://{slug}.wd{wd}.myworkdayjobs.com/wday/cxs/{slug}/{board}/jobs"
        try:
            r = requests.post(
                url,
                json={"limit": 1, "offset": 0, "appliedFacets": {}},
                headers={"Content-Type": "application/json"},
                timeout=3,
            )
            if r.status_code == 200 and r.json().get("total", 0) > 0:
                return {
                    "ats": "workday",
                    "slug": slug,
                    "base_url": f"https://{slug}.wd{wd}.myworkdayjobs.com",
                    "board_name": board,
                }
        except (requests.RequestException, ValueError):
            pass
        return None

    combos = [(wd, board) for wd in WORKDAY_INSTANCES for board in boards]
    with ThreadPoolExecutor(max_workers=15) as pool:
        futures = {pool.submit(_try, wd, board): (wd, board) for wd, board in combos}
        for f in as_completed(futures):
            result = f.result()
            if result:
                pool.shutdown(wait=False, cancel_futures=True)
                return result
    return None


def resolve(company_name: str) -> dict | None:
    """
    Given a company name, return its ATS info.
    Returns: {"ats": "greenhouse"|"lever"|"ashby", "slug": str} or None if unresolvable.
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
    if _probe_ashby(slug):
        return {"ats": "ashby", "slug": slug}
    if _probe_gem(slug):
        return {"ats": "gem", "slug": slug}
    if _probe_workable(slug):
        return {"ats": "workable", "slug": slug}
    if _probe_smartrecruiters(slug):
        return {"ats": "smartrecruiters", "slug": slug}

    workday_result = _probe_workday(slug)
    if workday_result:
        return workday_result

    return None
