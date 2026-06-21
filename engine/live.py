"""
Near-real-time quote feed for the live price strip.

Base prices come from a single batched yfinance call (reliable, ~15-min delayed).
If Alpaca keys are set, US prices are overlaid with Alpaca's real-time IEX feed.
Writes to Supabase live_quotes. Run frequently via cron during market hours.

    python engine/live.py            # fetch + write
    python engine/live.py --dry      # print only
"""
from __future__ import annotations
import sys

import config

# Focused live watchlist (keep small so it can run every couple of minutes).
LIVE_WATCH = ["AAPL", "MSFT", "NVDA", "SPY", "SHOP.TO", "RY.TO", "TD.TO", "XIU.TO"]


def fetch_live(tickers):
    import yfinance as yf
    out = {}
    data = yf.download(tickers, period="5d", auto_adjust=True, progress=False, group_by="ticker")
    for t in tickers:
        try:
            df = data[t] if len(tickers) > 1 else data
            closes = df["Close"].dropna()
            price, prev = float(closes.iloc[-1]), float(closes.iloc[-2])
            out[t] = {"ticker": t, "price": round(price, 2), "prev_close": round(prev, 2),
                      "change_pct": round((price / prev - 1) * 100, 2)}
        except Exception:
            pass

    # overlay real-time US prices from Alpaca, if configured
    us = [t for t in tickers if not t.upper().endswith((".TO", ".V")) and t in out]
    if us and config.ALPACA_API_KEY and config.ALPACA_API_SECRET:
        try:
            from alpaca.data.historical import StockHistoricalDataClient
            from alpaca.data.requests import StockSnapshotRequest
            from alpaca.data.enums import DataFeed
            client = StockHistoricalDataClient(config.ALPACA_API_KEY, config.ALPACA_API_SECRET)
            snaps = client.get_stock_snapshot(StockSnapshotRequest(symbol_or_symbols=us, feed=DataFeed.IEX))
            for t, s in snaps.items():
                rt = getattr(getattr(s, "latest_trade", None), "price", None)
                if rt:
                    prev = out[t]["prev_close"]
                    out[t]["price"] = round(float(rt), 2)
                    out[t]["change_pct"] = round((float(rt) / prev - 1) * 100, 2)
        except Exception as ex:
            print(f"  Alpaca real-time overlay skipped: {ex}")
    return list(out.values())


def main(dry):
    rows = fetch_live(LIVE_WATCH)
    for r in rows:
        print(f"  {r['ticker']:8} ${r['price']:<10} {r['change_pct']:+.2f}%")
    if dry:
        print("\nDry run - nothing written.")
        return
    config.require("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY")
    import db
    client = db.get_client()
    if rows:
        client.table("live_quotes").upsert(rows, on_conflict="ticker").execute()
    print(f"\nWrote {len(rows)} live quotes to Supabase.")


if __name__ == "__main__":
    main(dry="--dry" in sys.argv)
