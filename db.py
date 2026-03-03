from __future__ import annotations
import os
from supabase import create_client, Client


def _client() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set.")
    return create_client(url, key)


def add_subscription(email: str, companies: list, target_role: str, background: str = "") -> dict:
    """Add or update a subscription. Upserts on email."""
    result = (
        _client()
        .table("subscriptions")
        .upsert(
            {"email": email, "companies": companies, "target_role": target_role, "background": background, "active": True},
            on_conflict="email",
        )
        .execute()
    )
    return result.data[0] if result.data else {}


def get_all_subscriptions() -> list:
    """Return all active subscriptions."""
    result = (
        _client()
        .table("subscriptions")
        .select("*")
        .eq("active", True)
        .execute()
    )
    return result.data


def unsubscribe(email: str) -> None:
    """Soft-delete a subscription by email."""
    _client().table("subscriptions").update({"active": False}).eq("email", email).execute()


def get_sent_urls(email: str) -> set[str]:
    """Return all job URLs already sent to this email."""
    result = (
        _client()
        .table("sent_jobs")
        .select("job_url")
        .eq("email", email)
        .execute()
    )
    return {row["job_url"] for row in result.data}


def mark_jobs_sent(email: str, job_urls: list[str]) -> None:
    """Record that these job URLs were sent to this email."""
    if not job_urls:
        return
    rows = [{"email": email, "job_url": url} for url in job_urls]
    _client().table("sent_jobs").upsert(rows, on_conflict="email,job_url").execute()
