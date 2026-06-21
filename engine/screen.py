"""
Daily opportunity screener.

Scans a universe of US + Canadian tickers, runs every strategy, finds what's
currently LONG (flagging fresh buys), then ENRICHES each with the company's
strength score (fundamentals) and recent news sentiment, and writes a ranked
list to Supabase for the dashboard.

Usage:
    python engine/screen.py            # scan + enrich + write
    python engine/screen.py --dry      # print only (no DB, no enrichment)
"""
from __future__ import annotations
import sys
import datetime as dt
from collections import defaultdict

import config
import data_sources
from strategies import REGISTRY

UNIVERSE = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "JPM", "V", "MA",
    "UNH", "JNJ", "XOM", "CVX", "WMT", "PG", "HD", "KO", "PEP", "DIS",
    "NFLX", "AMD", "INTC", "BA", "CAT", "SPY", "QQQ",
    "RY.TO", "TD.TO", "BNS.TO", "BMO.TO", "ENB.TO", "CNQ.TO", "SU.TO", "TRP.TO",
    "CP.TO", "CNR.TO", "BCE.TO", "MFC.TO", "SHOP.TO", "XIU.TO",
]
FRESH_DAYS = 5
LOOKBACK = "1y"


def scan():
    rows = []
    today = dt.date.today().isoformat()
    for ticker in UNIVERSE:
        df = data_sources.get_prices(ticker, period=LOOKBACK)
        if df is None or len(df) < 60:
            print(f"  skip {ticker} (insufficient data)")
            continue
        close = df["close"]
        score = float(close.iloc[-1] / close.iloc[-21] - 1) if len(close) > 21 else 0.0
        last_price = round(float(close.iloc[-1]), 2)
        for sname, fn in REGISTRY.items():
            pos = fn(df)
            if pos.iloc[-1] != 1.0:
                continue
            fresh = bool((pos.iloc[-(FRESH_DAYS + 1):].diff() > 0).any())
            rows.append({
                "as_of": today, "ticker": ticker, "strategy": sname,
                "signal": "buy" if fresh else "hold-long",
                "last_price": last_price, "score": round(score, 4), "fresh": fresh,
            })
    rows.sort(key=lambda r: r["score"], reverse=True)
    return rows


def enrich(client, rows):
    fund = {r["ticker"]: r.get("strength_score")
            for r in (client.table("fundamentals").select("ticker,strength_score").execute().data or [])}
    news = (client.table("news_items").select("tickers,sentiment")
            .order("published_at", desc=True).limit(600).execute().data or [])
    sent = defaultdict(list)
    for n in news:
        if n.get("sentiment") is None:
            continue
        for t in (n.get("tickers") or []):
            sent[t].append(n["sentiment"])
    for r in rows:
        r["strength_score"] = fund.get(r["ticker"])
        vals = sent.get(r["ticker"])
        r["sentiment"] = round(sum(vals) / len(vals), 3) if vals else None
    return rows


def main(dry):
    rows = scan()
    print(f"\nFound {len(rows)} long signals ({sum(r['fresh'] for r in rows)} fresh buys). Top 10:")
    for r in rows[:10]:
        print(f"  {r['ticker']:8} {r['strategy']:14} {r['signal']:9} mom={r['score']:+.1%}  ${r['last_price']}")
    if dry:
        print("\nDry run - nothing written.")
        return
    config.require("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY")
    import db
    client = db.get_client()
    rows = enrich(client, rows)
    client.table("opportunities").delete().neq("id", 0).execute()
    if rows:
        client.table("opportunities").insert(rows).execute()
    print(f"\nWrote {len(rows)} opportunities (with strength + sentiment) to Supabase.")


if __name__ == "__main__":
    main(dry="--dry" in sys.argv)
