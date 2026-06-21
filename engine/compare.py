"""
Run every strategy across a basket of tickers and several time windows
(including the 2022 bear market), then write the results + equity curves
to Supabase so the dashboard can chart them.

Usage:
    python engine/compare.py            # full run, writes to Supabase
    python engine/compare.py --dry      # print only, no DB write
"""
from __future__ import annotations
import sys
import pandas as pd
import yfinance as yf

import config
from strategies import REGISTRY
import metrics

# US + Canadian mix. Canadian tickers use the .TO suffix.
BASKET = ["AAPL", "MSFT", "NVDA", "SPY", "SHOP.TO", "RY.TO", "TD.TO", "XIU.TO"]

# Each window: label -> kwargs passed to yf.download
WINDOWS = {
    "5Y": {"period": "5y"},
    "2022 bear": {"start": "2022-01-01", "end": "2022-12-31"},
    "2020-now": {"start": "2020-01-01"},
}


def load_prices(ticker: str, dl_kwargs: dict) -> pd.DataFrame | None:
    raw = yf.download(ticker, auto_adjust=True, progress=False, **dl_kwargs)
    if raw is None or raw.empty:
        return None
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    return raw.rename(columns=str.lower)[["close"]].dropna()


def main(dry: bool) -> None:
    client = None
    if not dry:
        config.require("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY")
        import db
        client = db.get_client()

    rows_written = 0
    for ticker in BASKET:
        for wlabel, dl_kwargs in WINDOWS.items():
            df = load_prices(ticker, dl_kwargs)
            if df is None or len(df) < 60:
                print(f"  skip {ticker} [{wlabel}] (insufficient data)")
                continue
            for sname, fn in REGISTRY.items():
                m, sc, bc = metrics.evaluate(df["close"], fn(df))
                print(f"{ticker:8} {wlabel:10} {sname:14} "
                      f"ret={m['total_return']:+.1%}  bh={m['bh_total_return']:+.1%}  "
                      f"dd={m['max_drawdown']:.1%}  sharpe={m['sharpe']:.2f}")
                if dry:
                    continue
                rec = {"strategy": sname, "ticker": ticker, "period_label": wlabel, **m}
                res = client.table("backtests").insert(rec).execute()
                bid = res.data[0]["id"]
                client.table("backtest_curves").insert(
                    {"backtest_id": bid, "points": metrics.downsample_curves(sc, bc)}
                ).execute()
                rows_written += 1

    if dry:
        print("\nDry run — nothing written.")
    else:
        print(f"\nWrote {rows_written} backtests to Supabase. Open the dashboard to view.")


if __name__ == "__main__":
    main(dry="--dry" in sys.argv)
