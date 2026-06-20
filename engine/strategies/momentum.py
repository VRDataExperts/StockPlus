"""
Momentum strategy: moving-average crossover with an RSI filter.

Rules (long-only, the simplest sound starting point):
  - GO LONG when fast SMA crosses ABOVE slow SMA and RSI < overbought.
  - GO FLAT (sell) when fast SMA crosses BELOW slow SMA.

The same indicator logic feeds both the backtest and (later) live trading,
so what you validate is exactly what you run.
"""
from __future__ import annotations
import pandas as pd

# Default parameters — tune these later via the `strategies` table.
FAST = 20
SLOW = 50
RSI_PERIOD = 14
RSI_OVERBOUGHT = 75


def add_indicators(df: pd.DataFrame, fast=FAST, slow=SLOW, rsi_period=RSI_PERIOD) -> pd.DataFrame:
    df = df.copy()
    df["sma_fast"] = df["close"].rolling(fast).mean()
    df["sma_slow"] = df["close"].rolling(slow).mean()

    delta = df["close"].diff()
    gain = delta.clip(lower=0).rolling(rsi_period).mean()
    loss = (-delta.clip(upper=0)).rolling(rsi_period).mean()
    rs = gain / loss.replace(0, pd.NA)
    df["rsi"] = 100 - (100 / (1 + rs))
    return df


def target_position(df: pd.DataFrame, rsi_overbought=RSI_OVERBOUGHT) -> pd.Series:
    """1.0 = fully long, 0.0 = flat. One value per bar."""
    df = add_indicators(df)
    long_ok = (df["sma_fast"] > df["sma_slow"]) & (df["rsi"] < rsi_overbought)
    return long_ok.astype(float).fillna(0.0)


def latest_signal(df: pd.DataFrame) -> str | None:
    """For live use: returns 'buy', 'sell', or None based on the last bar's edge."""
    pos = target_position(df)
    if len(pos) < 2:
        return None
    prev, now = pos.iloc[-2], pos.iloc[-1]
    if prev == 0.0 and now == 1.0:
        return "buy"
    if prev == 1.0 and now == 0.0:
        return "sell"
    return None
