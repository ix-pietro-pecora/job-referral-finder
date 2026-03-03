import anthropic

client = anthropic.Anthropic()


def filter_and_rank(jobs: list[dict], target_role: str, background: str = "") -> list[dict]:
    """
    Use Claude to filter jobs relevant to target_role and return them ranked
    with a short match note. Returns a subset of the input jobs list.
    """
    if not jobs:
        return []

    # Pre-filter by title to reduce token usage before hitting Claude
    keywords = [w.lower() for w in target_role.split()]
    candidates = [
        j for j in jobs
        if any(kw in j["title"].lower() for kw in keywords)
    ] or jobs  # fall back to all jobs if pre-filter removes everything
    candidates = candidates[:50]  # cap to avoid truncated responses

    # Build a compact job list for the prompt
    job_lines = []
    for i, job in enumerate(candidates):
        desc_preview = job["description"][:300].replace("\n", " ")
        job_lines.append(
            f"[{i}] {job['title']} | {job['location']}\n{desc_preview}"
        )

    background_line = f"\nCandidate background: {background}" if background else ""

    prompt = f"""You are helping a job seeker find relevant roles.

Target role: "{target_role}"{background_line}

Below are job postings. Return ONLY the ones genuinely relevant to the target role.
If a candidate background is provided, filter out roles that are too senior, too junior, or clearly mismatched in seniority or experience level.
For each match, respond with a JSON array of objects with these fields:
- index: the [number] from the input
- match_note: one sentence on why this role fits (max 15 words)

Respond with only the JSON array, no other text.

Jobs:
{chr(10).join(job_lines)}"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    import json, re
    try:
        raw = message.content[0].text.strip()
        # Strip markdown code fences if present
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        matches = json.loads(raw)
    except (json.JSONDecodeError, IndexError):
        return []

    results = []
    for match in matches:
        idx = match.get("index")
        if idx is not None and 0 <= idx < len(candidates):
            job = candidates[idx].copy()
            job["match_note"] = match.get("match_note", "")
            results.append(job)

    return results


def score_with_resume(jobs: list[dict], resume_text: str) -> list[dict]:
    """
    Given a list of jobs and resume text, add a match_score (0-100)
    and talking_points to each job.
    """
    if not jobs or not resume_text:
        return jobs

    results = []
    for job in jobs:
        desc_preview = job["description"][:800].replace("\n", " ")
        prompt = f"""You are a career coach reviewing a resume against a job posting.

Job title: {job['title']}
Job description: {desc_preview}

Resume:
{resume_text[:2000]}

Respond with a JSON object with:
- score: integer 0-100 (how well the resume fits this role)
- reason: one sentence explaining the score (max 20 words)
- talking_points: list of 2-3 short strings the candidate should highlight in a referral ask

Respond with only the JSON object, no other text."""

        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )

        import json
        try:
            raw = message.content[0].text.strip()
            data = json.loads(raw)
            job = job.copy()
            job["match_score"] = data.get("score", 0)
            job["score_reason"] = data.get("reason", "")
            job["talking_points"] = data.get("talking_points", [])
        except (json.JSONDecodeError, IndexError):
            job = job.copy()
            job["match_score"] = 0
            job["score_reason"] = ""
            job["talking_points"] = []

        results.append(job)

    return sorted(results, key=lambda j: j["match_score"], reverse=True)
