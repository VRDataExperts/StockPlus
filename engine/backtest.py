"""
Backtest the momentum strategy on free historical data (yfinance).
No broker or API key needed — runs entirely offline on daily bars.

Usage:
    python engine/backtest.py                # default ticker AAPL, 5y
    python engine/backtest.py SHOP.TO 3y
    python engine/backtest.py MSFT 10y
"""
from __future__ import annotations
import sys
import numpy as np
import pandas as pd
import yfinance as yf

from strategies import momentum

TRADING_DAYS = 252


def load_prices(ticker: str, period: str) -> pd.DataFrame:
    raw = yf.download(ticker, period=period, auto_adjust=True, progress=False)
    if raw.empty:
        raise SystemExit(f"No data for {ticker}. Check the symbol (Canadian = .TO).")
    # Flatten possible MultiIndex columns and normalise to lowercase 'close'.
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    df = raw.rename(columns=str.lower)[["close"]].dropna()
    return df


def run(ticker: str, period: str) -> None:
    df = load_prices(ticker, period)

    # Target position per bar; trade executes on the NEXT bar (no look-ahead).
    pos = momentum.target_position(df).shift(1).fillna(0.0)

    daily_ret = df["close"].pct_change().fillna(0.0)
    strat_ret = daily_ret * pos
    bh_curve = (1 + daily_ret).cumprod()
    strat_curve = (1 + strat_ret).cumprod()

    # Metrics
    def cagr(curve):
        years = len(curve) / TRADING_DAYS
        return curve.iloc[-1] ** (1 / years) - 1 if years > 0 else 0.0

    def max_dd(curve):
        return (curve / curve.cummax() - 1).min()

    def sharpe(ret):
        sd = ret.std()
        return (ret.mean() / sd * np.sqrt(TRADING_DAYS)) if sd > 0 else 0.0

    trades = int((pos.diff().abs() > 0).sum())

    print(f"\n=== Momentum backtest: {ticker}  ({period}, {len(df)} daily bars) ===")
    print(f"Params: SMA {momentum.FAST}/{momentum.SLOW}, RSI<{momentum.RSI_OVERBOUGHT}\n")
    print(f"{'Metric':22}{'Strategy':>14}{'Buy & Hold':>14}")
    print(f"{'Total return':22}{strat_curve.iloc[-1]-1:>13.1%}{bh_curve.iloc[-1]-1:>14.1%}")
    print(f"{'CAGR':22}{cagr(strat_curve):>13.1%}{cagr(bh_curve):>14.1%}")
    print(f"{'Max drawdown':22}{max_dd(strat_curve):>13.1%}{max_dd(bh_curve):>14.1%}")
    print(f"{'Sharpe (daily)':22}{sharpe(strat_ret):>14.2f}{sharpe(daily_ret):>14.2f}")
    print(f"{'Round-trip trades':22}{trades:>14}")
    print(f"{'Time in market':22}{pos.mean():>13.1%}")
    print("\nNote: backtests overstate live results (no fees/slippage/latency).")
    print("This is for ranking ideas, not a promise of returns.\n")


if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    period = sys.argv[2] if len(sys.argv) > 2 else "5y"
    run(ticker, period)
