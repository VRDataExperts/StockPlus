"""
Finnhub -> Supabase news ingestion, with a simple sentiment score.

Pulls general market news + company news for the watchlist, scores each headline
-1..+1 with a small keyword lexicon, and stores them (deduplicated).

Run:
    python engine/news_ingest.py
"""
from __future__ import annotations
import datetime as dt
import re
import sys
import requests

import config

BASE = "https://finnhub.io/api/v1"
WATCHLIST = ["AAPL", "MSFT", "NVDA", "SPY", "AMZN", "GOOGL", "META", "TSLA", "JPM"]

POS = {"beat", "beats", "surge", "surges", "soar", "rally", "record", "growth", "upgrade",
       "strong", "gain", "gains", "jump", "jumps", "profit", "wins", "boost", "raises",
       "outperform", "bullish", "tops", "rises", "expand", "approve", "approved"}
NEG = {"miss", "misses", "plunge", "plunges", "drop", "drops", "fall", "falls", "cut",
       "cuts", "downgrade", "weak", "loss", "losses", "lawsuit", "probe", "decline",
       "slump", "warns", "warning", "bearish", "slashes", "fraud", "recall", "sinks"}


def score_sentiment(text: str) -> float:
    words = re.findall(r"[a-z]+", (text or "").lower())
    p = sum(w in POS for w in words)
    n = sum(w in NEG for w in words)
    return round((p - n) / (p + n), 3) if (p + n) else 0.0


def _get(path, params):
    params = {**params, "token": config.FINNHUB_API_KEY}
    r = requests.get(f"{BASE}{path}", params=params, timeout=20)
    if r.status_code != 200:
        print(f"  Finnhub {r.status_code} for {path} {params.get('symbol','')} - skipping.")
        return []
    return r.json()


def fetch_general():
    return [_norm(a, None) for a in (_get("/news", {"category": "general"}) or [])]


def fetch_company(ticker):
    today = dt.date.today()
    frm = (today - dt.timedelta(days=3)).isoformat()
    data = _get("/company-news", {"symbol": ticker, "from": frm, "to": today.isoformat()})
    return [_norm(a, [ticker]) for a in (data or [])]


def _norm(a, tickers):
    ts = a.get("datetime")
    published_at = dt.datetime.fromtimestamp(ts, dt.timezone.utc).isoformat() if ts else None
    headline = (a.get("headline") or "").strip()[:1000]
    return {
        "provider": "finnhub",
        "headline": headline,
        "url": a.get("url"),
        "tickers": tickers,
        "sentiment": score_sentiment(headline),
        "published_at": published_at,
        "external_id": str(a.get("id") or a.get("url")),
    }


def main():
    config.require("FINNHUB_API_KEY", "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY")
    import db
    client = db.get_client()
    rows = fetch_general()
    for t in WATCHLIST:
        print(f"Fetching company news for {t}...")
        rows += fetch_company(t)
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
