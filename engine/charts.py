"""
Per-ticker chart data: price + SMA20/50 + Bollinger bands + buy/sell markers
for every strategy. Written to Supabase so the Charts page can render it.

Usage:
    python engine/charts.py            # build + write
    python engine/charts.py --dry      # build one ticker, print summary
"""
from __future__ import annotations
import sys
import pandas as pd

import config
import data_sources
from strategies import REGISTRY

TAIL = 250  # ~1 trading year of daily points


def _r(x):
    return None if x is None or pd.isna(x) else round(float(x), 2)


def build(ticker: str):
    df = data_sources.get_prices(ticker, period="1y")
    if df is None or len(df) < 60:
        return None
    close = df["close"]
    sma20 = close.rolling(20).mean()
    sma50 = close.rolling(50).mean()
    std = close.rolling(20).std()
    bb_up, bb_lo = sma20 + 2 * std, sma20 - 2 * std
    tail = df.index[-TAIL:]

    points = [{
        "t": str(t.date()), "close": _r(close[t]), "sma20": _r(sma20[t]),
        "sma50": _r(sma50[t]), "bb_up": _r(bb_up[t]), "bb_lo": _r(bb_lo[t]),
    } for t in tail]

    markers = []
    tailset = set(tail)
    for sname, fn in REGISTRY.items():
        chg = fn(df).reindex(df.index).fillna(0).diff()
        for t in df.index[chg != 0]:
            if t in tailset:
                markers.append({
                    "t": str(t.date()),
                    "side": "buy" if chg.loc[t] > 0 else "sell",
                    "strategy": sname, "price": _r(close[t]),
                })
    return {"ticker": ticker, "points": points, "markers": markers}


def main(dry: bool):
    from screen import UNIVERSE
    if dry:
        c = build("AAPL")
        print(f"AAPL: {len(c['points'])} points, {len(c['markers'])} markers (sample)")
        print("\nDry run - nothing written.")
        return
    config.require("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY")
    import db
    client = db.get_client()
    n = 0
    for t in UNIVERSE:
        c = build(t)
        if not c:
            print(f"  skip {t}")
            continue
        client.table("chart_data").upsert(c, on_conflict="ticker").execute()
        n += 1
        print(f"  {t:8} {len(c['points'])} pts, {len(c['markers'])} markers")
    print(f"\nWrote chart data for {n} tickers to Supabase.")


if __name__ == "__main__":
    main(dry="--dry" in sys.argv)
