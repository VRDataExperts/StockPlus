"""
Thin Supabase helper. Uses the service-role key (server-side only).
"""
from typing import Any
from supabase import create_client, Client
import config


def get_client() -> Client:
    config.require("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY")
    return create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY)


def insert_news(client: Client, rows: list[dict[str, Any]]) -> int:
    """Upsert news rows; ignores duplicates on (provider, external_id)."""
    if not rows:
        return 0
    res = client.table("news_items").upsert(
        rows, on_conflict="provider,external_id", ignore_duplicates=True
    ).execute()
    return len(res.data or [])


def insert_signal(client: Client, row: dict[str, Any]) -> None:
    client.table("signals").insert(row).execute()


def log(client: Client, actor: str, action: str, detail: dict | None = None) -> None:
    client.table("audit_log").insert(
        {"actor": actor, "action": action, "detail": detail or {}}
    ).execute()
