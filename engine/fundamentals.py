"""
Company fundamentals + a 0-100 "strength" score, via yfinance.

Pulls quality metrics (margins, ROE, growth, debt, valuation) for the screener
universe and writes them to Supabase so signals can be filtered to strong firms.

Usage:
    python engine/fundamentals.py            # fetch + write to Supabase
    python engine/fundamentals.py --dry      # print only
"""
from __future__ import annotations
import sys

import config


def get_fundamentals(ticker: str) -> dict:
    import yfinance as yf
    info = {}
    try:
        info = yf.Ticker(ticker).info or {}
    except Exception as ex:
        print(f"  fundamentals fetch failed for {ticker}: {ex}")
    d = {
        "ticker": ticker,
        "name": info.get("shortName"),
        "sector": info.get("sector"),
        "market_cap": info.get("marketCap"),
        "pe": info.get("trailingPE"),
        "profit_margin": info.get("profitMargins"),
        "roe": info.get("returnOnEquity"),
        "revenue_growth": info.get("revenueGrowth"),
        "debt_to_equity": info.get("debtToEquity"),
        "gross_margin": info.get("grossMargins"),
    }
    d["strength_score"] = strength_score(d)
    return d


def strength_score(d: dict) -> int:
    """Crude 0-100 quality score from a few fundamentals. Heuristic, not gospel."""
    score = 50
    pm, roe, rg, de = d.get("profit_margin"), d.get("roe"), d.get("revenue_growth"), d.get("debt_to_equity")
    if pm is not None:
        score += 15 if pm > 0.15 else 5 if pm > 0.05 else -10 if pm < 0 else 0
    if roe is not None:
        score += 15 if roe > 0.15 else 5 if roe > 0.05 else -5
    if rg is not None:
        score += 15 if rg > 0.10 else 5 if rg > 0 else -10
    if de is not None:                      # yfinance reports debt/equity as a percent
        score += 10 if de < 50 else 0 if de < 100 else -10
    return max(0, min(100, score))


def main(dry: bool):
    from screen import UNIVERSE
    rows = []
    for t in UNIVERSE:
        d = get_fundamentals(t)
        rows.append(d)
        print(f"  {t:8} score={d['strength_score']:>3}  "
              f"margin={d['profit_margin']}  roe={d['roe']}  growth={d['revenue_growth']}")
    if dry:
        print("\nDry run - nothing written.")
        return
    config.require("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY")
    import db
    client = db.get_client()
    client.table("fundamentals").upsert(rows, on_conflict="ticker").execute()
    print(f"\nWrote {len(rows)} fundamentals rows to Supabase.")


if __name__ == "__main__":
    main(dry="--dry" in sys.argv)
