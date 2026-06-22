"""
Volatile / lower-priced short-term "movers" screener.

Higher risk than the main screener. For each name it runs trend + mean-reversion
rules tuned to three horizons (day = fast, week = medium, month = slow), and
scores a 0-100 CONFIDENCE from trend alignment, momentum, volume surge, RSI and
news sentiment. Writes long signals to Supabase `movers`.

NOTE: uses daily bars (free). "day" = very short swing, not tick-level day trading.

    python engine/movers.py            # scan + enrich + write
    python engine/movers.py --dry      # print only
"""
from __future__ import annotations
import sys
import datetime as dt
from collections import defaultdict

import numpy as np
import config
import data_sources
from strategies import breakout, mean_reversion
from strategies._util import rsi as rsi_fn


def _mom_pos(df, fast, slow):
    """Horizon-tunable momentum: long when fast SMA > slow SMA."""
    c = df["close"]
    return (c.rolling(fast).mean() > c.rolling(slow).mean()).astype(float).fillna(0.0)

# Lower-priced / higher-volatility names (US + a few Canadian). Edit freely.
UNIVERSE = [
    "PLTR", "SOFI", "F", "BAC", "INTC", "NIO", "LCID", "PLUG", "RIOT", "MARA",
    "SNAP", "RBLX", "DKNG", "AFRM", "COIN", "HOOD", "CHPT", "UPST", "CCL", "AAL",
    "T", "PFE", "NU",
    "HUT.TO", "BITF.TO", "BTE.TO", "ATH.TO",
]

# horizon -> per-strategy lookback params
HORIZONS = {
    "day":   {"mom": (3, 8),  "brk": (5, 3),   "mr": 5},
    "week":  {"mom": (5, 15), "brk": (10, 5),  "mr": 9},
    "month": {"mom": (20, 50),"brk": (20, 10), "mr": 14},
}
FRESH_DAYS = 3


def _ind(df):
    close = df["close"]
    s20 = close.rolling(20).mean().iloc[-1]
    s50 = close.rolling(50).mean().iloc[-1]
    r = rsi_fn(close, 14).iloc[-1]
    mom = float(close.iloc[-1] / close.iloc[-21] - 1) if len(close) > 21 else 0.0
    vol = float(close.pct_change().std() * np.sqrt(252)) if len(close) > 30 else 0.0
    volr = 1.0
    if "volume" in df and len(df) > 60:
        v = df["volume"]
        volr = float(v.iloc[-5:].mean() / (v.iloc[-60:].mean() or 1))
    return {
        "price": float(close.iloc[-1]),
        "s20": None if s20 != s20 else float(s20),
        "s50": None if s50 != s50 else float(s50),
        "rsi": None if r != r else float(r),
        "mom": mom, "vol": vol, "volr": volr,
    }


def confidence(ind, fresh, sent):
    c = 50.0
    p, s20, s50 = ind["price"], ind["s20"], ind["s50"]
    if s20 and s50:
        if p > s20 and s20 > s50: c += 15
        elif p > s20: c += 7
        elif p < s20 and s20 < s50: c -= 15
    c += max(-15, min(15, ind["mom"] * 50))
    c += 10 if ind["volr"] > 1.5 else 5 if ind["volr"] > 1.2 else 0
    if ind["rsi"] is not None: c += 5 if ind["rsi"] < 70 else -5
    if sent is not None: c += round(sent * 10)
    if fresh: c += 5
    return int(max(0, min(100, c)))


def scan():
    today = dt.date.today().isoformat()
    rows = []
    for ticker in UNIVERSE:
        df = data_sources.get_prices(ticker, period="1y")
        if df is None or len(df) < 60:
            print(f"  skip {ticker}")
            continue
        ind = _ind(df)
        for hz, p in HORIZONS.items():
            strats = {
                "momentum": _mom_pos(df, p["mom"][0], p["mom"][1]),
                "breakout": breakout.target_position(df, p["brk"][0], p["brk"][1]),
                "mean_reversion": mean_reversion.target_position(df, p["mr"]),
            }
            for sname, pos in strats.items():
                if pos.iloc[-1] != 1.0:
                    continue
                fresh = bool((pos.iloc[-(FRESH_DAYS + 1):].diff() > 0).any())
                rows.append({
                    "as_of": today, "ticker": ticker, "horizon": hz, "strategy": sname,
                    "signal": "buy" if fresh else "hold-long",
                    "volatility": round(ind["vol"] * 100, 1), "momentum": round(ind["mom"], 4),
                    "last_price": round(ind["price"], 2), "fresh": fresh,
                    "_ind": ind, "_conf0": confidence(ind, fresh, None),
                })
    return rows


def main(dry):
    rows = scan()
    rows.sort(key=lambda r: r["_conf0"], reverse=True)
    print(f"\nFound {len(rows)} volatile long signals. Top 12 by confidence:")
    for r in rows[:12]:
        print(f"  {r['ticker']:8} {r['horizon']:5} {r['strategy']:14} {r['signal']:9} "
              f"conf={r['_conf0']:>3} vol={r['volatility']}% mom={r['momentum']:+.1%} ${r['last_price']}")
    if dry:
        print("\nDry run - nothing written.")
        return
    config.require("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY")
    import db
    client = db.get_client()
    news = (client.table("news_items").select("tickers,sentiment")
            .order("published_at", desc=True).limit(600).execute().data or [])
    sent = defaultdict(list)
    for n in news:
        if n.get("sentiment") is None: continue
        for t in (n.get("tickers") or []): sent[t].append(n["sentiment"])
    out = []
    for r in rows:
        s = sent.get(r["ticker"]); savg = round(sum(s) / len(s), 3) if s else None
        r["sentiment"] = savg
        r["confidence"] = confidence(r.pop("_ind"), r["fresh"], savg)
        r.pop("_conf0", None)
        out.append(r)
    client.table("movers").delete().neq("id", 0).execute()
    if out:
        client.table("movers").insert(out).execute()
    print(f"\nWrote {len(out)} movers to Supabase.")


if __name__ == "__main__":
    main(dry="--dry" in sys.argv)
