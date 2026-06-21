"""
Backtest a strategy on daily bars (data via the universal adapter).

Usage:
    python engine/backtest.py                # default AAPL, 5y, momentum
    python engine/backtest.py SHOP.TO 3y
    python engine/backtest.py MSFT 10y breakout
"""
from __future__ import annotations
import sys

import data_sources
import metrics
from strategies import REGISTRY


def load_prices(ticker, period):
    df = data_sources.get_prices(ticker, period=period)
    if df is None or df.empty:
        raise SystemExit(f"No data for {ticker}. Check the symbol (Canadian = .TO).")
    return df[["close"]].dropna()


def run(ticker, period, strategy):
    fn = REGISTRY.get(strategy)
    if fn is None:
        raise SystemExit(f"Unknown strategy '{strategy}'. Options: {', '.join(REGISTRY)}")
    df = load_prices(ticker, period)
    m, _, _ = metrics.evaluate(df["close"], fn(df))
    print(f"\n=== {strategy} backtest: {ticker} ({period}, {len(df)} daily bars) ===\n")
    print(f"{'Metric':22}{'Strategy':>14}{'Buy & Hold':>14}")
    print(f"{'Total return':22}{m['total_return']:>13.1%}{m['bh_total_return']:>14.1%}")
    print(f"{'Max drawdown':22}{m['max_drawdown']:>13.1%}{m['bh_max_drawdown']:>14.1%}")
    print(f"{'Sharpe (daily)':22}{m['sharpe']:>14.2f}{m['bh_sharpe']:>14.2f}")
    print(f"{'Round-trip trades':22}{m['trades']:>14}")
    print(f"{'Time in market':22}{m['time_in_market']:>13.1%}")
    print("\nNote: backtests overstate live results (no fees/slippage/latency).\n")


if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    period = sys.argv[2] if len(sys.argv) > 2 else "5y"
    strategy = sys.argv[3] if len(sys.argv) > 3 else "momentum"
    run(ticker, period, strategy)
