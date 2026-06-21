"""
Daily opportunity screener.

Scans a universe of US + Canadian tickers, runs every strategy, and records
which ones are currently LONG -- flagging fresh buy signals (entries in the
last few days) -- then writes a ranked list to Supabase for the dashboard.

Usage:
    python engine/screen.py            # scan + write to Supabase
    python engine/screen.py --dry      # print only, no DB write
"""
from __future__ import annotations
import sys
import datetime as dt

import config
import data_sources
from strategies import REGISTRY

# Starter universe (expand freely). Canadian names use .TO
UNIVERSE = [
    # US large caps + ETFs
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "JPM", "V", "MA",
    "UNH", "JNJ", "XOM", "CVX", "WMT", "PG", "HD", "KO", "PEP", "DIS",
    "NFLX", "AMD", "INTC", "BA", "CAT", "SPY", "QQQ",
    # Canada (TSX)
    "RY.TO", "TD.TO", "BNS.TO", "BMO.TO", "ENB.TO", "CNQ.TO", "SU.TO", "TRP.TO",
    "CP.TO", "CNR.TO", "BCE.TO", "MFC.TO", "SHOP.TO", "XIU.TO",
]

FRESH_DAYS = 5     # a "buy" = entered long within this many bars
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
                continue  # only surface things currently long
            recent = pos.iloc[-(FRESH_DAYS + 1):]
            fresh = bool((recent.diff() > 0).any())
            rows.append({
                "as_of": today, "ticker": ticker, "strategy": sname,
                "signal": "buy" if fresh else "hold-long",
                "last_price": last_price, "score": round(score, 4), "fresh": fresh,
            })
    rows.sort(key=lambda r: r["score"], reverse=True)
    return rows


def main(dry):
    rows = scan()
    print(f"\nFound {len(rows)} long signals "
          f"({sum(r['fresh'] for r in rows)} fresh buys). Top 10 by 20-day momentum:")
    for r in rows[:10]:
        print(f"  {r['ticker']:8} {r['strategy']:14} {r['signal']:9} "
              f"score={r['score']:+.1%}  ${r['last_price']}")
    if dry:
        print("\nDry run - nothing written.")
        return
    config.require("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY")
    import db
    client = db.get_client()
    client.table("opportunities").delete().neq("id", 0).execute()  # clear prior run
    if rows:
        client.table("opportunities").insert(rows).execute()
    print(f"\nWrote {len(rows)} opportunities to Supabase. Open the dashboard.")


if __name__ == "__main__":
    main(dry="--dry" in sys.argv)
