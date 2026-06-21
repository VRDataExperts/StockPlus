"""
Finnhub -> Supabase news ingestion.

Pulls general market news + company news for your watchlist and stores them
in the `news_items` table (deduplicated). Free Finnhub tier is enough for this.

Run:
    python engine/news_ingest.py
"""
from __future__ import annotations
import datetime as dt
import sys
import requests

import config
import db

BASE = "https://finnhub.io/api/v1"

# Edit this watchlist freely (US + Canadian tickers). For Canadian names on
# Finnhub use the .TO suffix, e.g. "SHOP.TO", "RY.TO".
WATCHLIST = ["AAPL", "MSFT", "NVDA", "SPY", "SHOP.TO", "RY.TO"]


def _get(path: str, params: dict) -> list | dict:
    params = {**params, "token": config.FINNHUB_API_KEY}
    r = requests.get(f"{BASE}{path}", params=params, timeout=20)
    if r.status_code != 200:
        # 403 = symbol not allowed on the free tier (e.g. Canadian .TO names);
        # 429 = rate limited. Skip gracefully instead of crashing the run.
        sym = params.get("symbol", "")
        print(f"  Finnhub {r.status_code} for {path} {sym} — skipping.")
        return []
    return r.json()


def fetch_general() -> list[dict]:
    data = _get("/news", {"category": "general"})
    return [_norm("finnhub", a, tickers=None) for a in (data or [])]


def fetch_company(ticker: str) -> list[dict]:
    today = dt.date.today()
    frm = (today - dt.timedelta(days=3)).isoformat()
    data = _get("/company-news", {"symbol": ticker, "from": frm, "to": today.isoformat()})
    return [_norm("finnhub", a, tickers=[ticker]) for a in (data or [])]


def _norm(provider: str, a: dict, tickers: list[str] | None) -> dict:
    published = a.get("datetime")
    published_at = (
        dt.datetime.fromtimestamp(published, dt.timezone.utc).isoformat()
        if published else None
    )
    return {
        "provider": provider,
        "headline": (a.get("headline") or "").strip()[:1000],
        "url": a.get("url"),
        "tickers": tickers,
        "sentiment": None,  # free tier has no sentiment; we can add later
        "published_at": published_at,
        "external_id": str(a.get("id") or a.get("url")),
    }


def main() -> None:
    config.require("FINNHUB_API_KEY", "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY")
    client = db.get_client()

    rows: list[dict] = []
    print("Fetching general market news...")
    rows += fetch_general()
    for t in WATCHLIST:
        print(f"Fetching company news for {t}...")
        rows += fetch_company(t)

    # drop rows with no usable id/headline
    rows = [r for r in rows if r["headline"] and r["external_id"]]
    inserted = db.insert_news(client, rows)
    db.log(client, "news_ingest", "fetch", {"fetched": len(rows), "inserted": inserted})
    print(f"\nDone. {len(rows)} fetched, {inserted} new rows written to news_items.")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        print(e)
        sys.exit(1)
